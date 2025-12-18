from setuptools import setup, Extension

# Define the C extension with Assembly source (wrapped in C)
module = Extension(
    "twopidgeons.twopidgeons_c", 
    sources=[
        "twopidgeons/extension.c",
        "twopidgeons/validator.c"  # Now a .c file containing inline ASM
    ]
)

setup(
    ext_modules=[module]
)
