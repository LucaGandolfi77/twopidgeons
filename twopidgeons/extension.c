#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>

/*
 * External Assembly function declaration.
 * Defined in validator.s
 */
extern int check_lowercase_5(const char* str);

/*
 * C implementation of is_valid_filename
 * Checks if the string is exactly 9 chars long:
 * - First 5 chars must be lowercase letters [a-z] (Checked via ASM)
 * - Last 4 chars must be ".2pg"
 */
static PyObject* is_valid_filename_c(PyObject* self, PyObject* args) {
    const char* filename;
    
    // Parse arguments: expect a string ("s")
    if (!PyArg_ParseTuple(args, "s", &filename)) {
        return NULL;
    }

    // 1. Length check: 5 chars + ".2pg" (4 chars) = 9 chars
    size_t len = strlen(filename);
    if (len != 9) {
        Py_RETURN_FALSE;
    }

    // 2. Check first 5 chars using optimized Assembly function
    if (check_lowercase_5(filename) == 0) {
        Py_RETURN_FALSE;
    }

    // 3. Check suffix ".2pg"
    // We compare starting from index 5
    if (strcmp(filename + 5, ".2pg") != 0) {
        Py_RETURN_FALSE;
    }

    Py_RETURN_TRUE;
}


// Method definition table
static PyMethodDef Methods[] = {
    {"is_valid_filename_c", is_valid_filename_c, METH_VARARGS, "Fast validation of filename format."},
    {NULL, NULL, 0, NULL}
};

// Module definition structure
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "twopidgeons_c",   // Module name
    "C extension for twopidgeons optimizations", // Module documentation
    -1,       // Size of per-interpreter state of the module, or -1 if the module keeps state in global variables.
    Methods
};

// Module initialization function
PyMODINIT_FUNC PyInit_twopidgeons_c(void) {
    return PyModule_Create(&module);
}
