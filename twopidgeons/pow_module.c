#include <Python.h>
#include <openssl/sha.h>
#include <stdio.h>
#include <string.h>

static PyObject* find_proof(PyObject* self, PyObject* args) {
    const char* part1;
    const char* part2;
    int difficulty;
    long long nonce = 0;
    char buffer[8192]; 
    unsigned char hash[SHA256_DIGEST_LENGTH];
    char hex_hash[SHA256_DIGEST_LENGTH * 2 + 1];
    
    if (!PyArg_ParseTuple(args, "ssi", &part1, &part2, &difficulty)) {
        return NULL;
    }

    int len1 = strlen(part1);
    int len2 = strlen(part2);
    
    // Pre-copy part1 since it never changes
    memcpy(buffer, part1, len1);

    while (1) {
        // Append nonce
        int len_nonce = sprintf(buffer + len1, "%lld", nonce);
        
        // Append part2
        memcpy(buffer + len1 + len_nonce, part2, len2);
        
        int total_len = len1 + len_nonce + len2;
        
        // Compute SHA256
        SHA256((unsigned char*)buffer, total_len, hash);

        // Check difficulty (leading zeros)
        int valid = 1;
        for (int i = 0; i < difficulty; i++) {
            int byte_index = i / 2;
            int nibble_index = i % 2;
            unsigned char byte = hash[byte_index];
            unsigned char nibble = (nibble_index == 0) ? (byte >> 4) : (byte & 0x0F);
            
            if (nibble != 0) {
                valid = 0;
                break;
            }
        }

        if (valid) {
            // Convert to hex string
            for(int i = 0; i < SHA256_DIGEST_LENGTH; i++)
                sprintf(hex_hash + (i * 2), "%02x", hash[i]);
            
            return Py_BuildValue("Ls", nonce, hex_hash);
        }

        nonce++;
        // Avoid infinite loop in case of overflow (very unlikely)
        if (nonce < 0) break; 
        
        // Allow Python to interrupt (Ctrl+C) every 100k iterations
        if (nonce % 100000 == 0) {
            if (PyErr_CheckSignals() != 0) return NULL;
        }
    }

    Py_RETURN_NONE;
}

static PyMethodDef PowMethods[] = {
    {"find_proof", find_proof, METH_VARARGS, "Find PoW nonce efficiently in C"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef powmodule = {
    PyModuleDef_HEAD_INIT,
    "pow_module",
    NULL,
    -1,
    PowMethods
};

PyMODINIT_FUNC PyInit_pow_module(void) {
    return PyModule_Create(&powmodule);
}
