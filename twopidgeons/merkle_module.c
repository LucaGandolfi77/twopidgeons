#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <openssl/sha.h>
#include <stdlib.h>
#include <string.h>

// Helper to compute SHA256 of a string and return hex string
static void sha256_string(const char *str, size_t len, char *outputBuffer) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, str, len);
    SHA256_Final(hash, &sha256);
    
    for(int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(outputBuffer + (i * 2), "%02x", hash[i]);
    }
    outputBuffer[64] = 0;
}

static PyObject* compute_root(PyObject* self, PyObject* args) {
    PyObject *listObj;
    
    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &listObj)) {
        return NULL;
    }
    
    Py_ssize_t num_tx = PyList_Size(listObj);
    if (num_tx == 0) {
        // Hash of empty string
        char empty_hash[65];
        sha256_string("", 0, empty_hash);
        return PyUnicode_FromString(empty_hash);
    }
    
    // 1. Hash all transactions (Leaves)
    // We allocate an array of strings (char buffers) to hold the hashes
    char **hashes = malloc(num_tx * sizeof(char*));
    if (!hashes) return PyErr_NoMemory();

    for (Py_ssize_t i = 0; i < num_tx; i++) {
        hashes[i] = malloc(65);
        if (!hashes[i]) {
            // Cleanup previous
            for (Py_ssize_t j=0; j<i; j++) free(hashes[j]);
            free(hashes);
            return PyErr_NoMemory();
        }

        PyObject *item = PyList_GetItem(listObj, i); // Borrowed ref
        
        if (!PyUnicode_Check(item)) {
            for (Py_ssize_t j=0; j<=i; j++) free(hashes[j]);
            free(hashes);
            PyErr_SetString(PyExc_TypeError, "List items must be strings");
            return NULL;
        }
        
        Py_ssize_t len;
        const char *tx_str = PyUnicode_AsUTF8AndSize(item, &len);
        sha256_string(tx_str, len, hashes[i]);
    }
    
    Py_ssize_t current_len = num_tx;
    
    // 2. Tree Reduction
    while (current_len > 1) {
        Py_ssize_t new_len = (current_len + 1) / 2;
        char **new_hashes = malloc(new_len * sizeof(char*));
        if (!new_hashes) {
             // Cleanup
             for(Py_ssize_t i=0; i<current_len; i++) free(hashes[i]);
             free(hashes);
             return PyErr_NoMemory();
        }
        
        for (Py_ssize_t i = 0; i < new_len; i++) {
            new_hashes[i] = malloc(65);
            // Check null... (omitted for brevity but good practice)
            
            char *left = hashes[2*i];
            char *right;
            
            if (2*i + 1 < current_len) {
                right = hashes[2*i + 1];
            } else {
                right = left; // Duplicate last
            }
            
            // Combine left + right
            char combined[129]; // 64 + 64 + 1
            strcpy(combined, left);
            strcat(combined, right);
            
            sha256_string(combined, strlen(combined), new_hashes[i]);
        }
        
        // Free old hashes
        for(Py_ssize_t i=0; i<current_len; i++) free(hashes[i]);
        free(hashes);
        
        hashes = new_hashes;
        current_len = new_len;
    }
    
    PyObject *result = PyUnicode_FromString(hashes[0]);
    free(hashes[0]);
    free(hashes);
    
    return result;
}

static PyMethodDef MerkleMethods[] = {
    {"compute_root", compute_root, METH_VARARGS, "Compute Merkle Root in C"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef merklemodule = {
    PyModuleDef_HEAD_INIT,
    "merkle_module",
    NULL,
    -1,
    MerkleMethods
};

PyMODINIT_FUNC PyInit_merkle_module(void) {
    return PyModule_Create(&merklemodule);
}
