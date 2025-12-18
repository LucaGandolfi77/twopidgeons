from setuptools import setup, Extension

# Define the C extension with Assembly source (wrapped in C)
module_c = Extension(
    "twopidgeons.twopidgeons_c", 
    sources=[
        "twopidgeons/extension.c",
        "twopidgeons/validator.c"  # Now a .c file containing inline ASM
    ]
)

# Define the PoW optimization module
module_pow = Extension(
    "twopidgeons.pow_module",
    sources=["twopidgeons/pow_module.c"],
    libraries=["crypto"]
)

# Define the Merkle Tree optimization module
module_merkle = Extension(
    "twopidgeons.merkle_module",
    sources=["twopidgeons/merkle_module.c"],
    libraries=["crypto"]
)

setup(
    ext_modules=[module_c, module_pow, module_merkle]
)
