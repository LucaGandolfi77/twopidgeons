#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>

// OpCodes
#define OP_HALT 0x00
#define OP_PUSH 0x01
#define OP_LOAD 0x02
#define OP_ADD  0x10
#define OP_SUB  0x11
#define OP_MUL  0x12
#define OP_DIV  0x13
#define OP_EQ   0x20
#define OP_GT   0x21
#define OP_LT   0x22
#define OP_AND  0x30
#define OP_OR   0x31
#define OP_NOT  0x32

#define STACK_SIZE 256

static PyObject* execute(PyObject* self, PyObject* args) {
    Py_buffer bytecode_buf;
    PyObject *values_list;

    if (!PyArg_ParseTuple(args, "y*O!", &bytecode_buf, &PyList_Type, &values_list)) {
        return NULL;
    }

    unsigned char *code = (unsigned char *)bytecode_buf.buf;
    Py_ssize_t code_len = bytecode_buf.len;
    Py_ssize_t pc = 0;

    double stack[STACK_SIZE];
    int sp = -1; // Stack pointer

    // Helper macros
    #define PUSH(v) stack[++sp] = (v)
    #define POP() stack[sp--]
    #define PEEK() stack[sp]

    while (pc < code_len) {
        unsigned char op = code[pc++];

        switch (op) {
            case OP_HALT:
                goto end;
            case OP_PUSH: {
                if (pc + sizeof(double) > code_len) { PyErr_SetString(PyExc_RuntimeError, "Truncated bytecode"); goto error; }
                double val = *(double*)(code + pc);
                pc += sizeof(double);
                if (sp >= STACK_SIZE - 1) { PyErr_SetString(PyExc_RuntimeError, "Stack overflow"); goto error; }
                PUSH(val);
                break;
            }
            case OP_LOAD: {
                if (pc + 1 > code_len) { PyErr_SetString(PyExc_RuntimeError, "Truncated bytecode"); goto error; }
                unsigned char idx = code[pc++];
                if (idx >= PyList_Size(values_list)) { PyErr_SetString(PyExc_RuntimeError, "Var index out of bounds"); goto error; }
                PyObject *item = PyList_GetItem(values_list, idx);
                double val = PyFloat_AsDouble(item);
                if (val == -1.0 && PyErr_Occurred()) goto error;
                if (sp >= STACK_SIZE - 1) { PyErr_SetString(PyExc_RuntimeError, "Stack overflow"); goto error; }
                PUSH(val);
                break;
            }
            case OP_ADD: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a + b); break;
            }
            case OP_SUB: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a - b); break;
            }
            case OP_MUL: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a * b); break;
            }
            case OP_DIV: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP();
                if (b == 0) { PyErr_SetString(PyExc_ZeroDivisionError, "Division by zero"); goto error; }
                PUSH(a / b); break;
            }
            case OP_EQ: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a == b ? 1.0 : 0.0); break;
            }
            case OP_GT: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a > b ? 1.0 : 0.0); break;
            }
            case OP_LT: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH(a < b ? 1.0 : 0.0); break;
            }
            case OP_AND: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH((a != 0 && b != 0) ? 1.0 : 0.0); break;
            }
            case OP_OR: {
                if (sp < 1) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double b = POP(); double a = POP(); PUSH((a != 0 || b != 0) ? 1.0 : 0.0); break;
            }
            case OP_NOT: {
                if (sp < 0) { PyErr_SetString(PyExc_RuntimeError, "Stack underflow"); goto error; }
                double a = POP(); PUSH(a == 0 ? 1.0 : 0.0); break;
            }
            default:
                PyErr_SetString(PyExc_RuntimeError, "Unknown opcode");
                goto error;
        }
    }

end:
    PyBuffer_Release(&bytecode_buf);
    if (sp == -1) {
        // Empty stack, return False
        Py_RETURN_FALSE;
    }
    // Return top of stack as bool
    if (stack[sp] != 0.0) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }

error:
    PyBuffer_Release(&bytecode_buf);
    return NULL;
}

static PyMethodDef VMMethods[] = {
    {"execute", execute, METH_VARARGS, "Execute bytecode"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef vmmodule = {
    PyModuleDef_HEAD_INIT,
    "vm_module",
    NULL,
    -1,
    VMMethods
};

PyMODINIT_FUNC PyInit_vm_module(void) {
    return PyModule_Create(&vmmodule);
}
