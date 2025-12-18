/*
 * Assembly implementation wrapped in C for compatibility with setuptools.
 * Uses GCC Inline Assembly (AT&T Syntax).
 */

int check_lowercase_5(const char* str) {
    int result = 1;
    
    /*
     * Logic:
     * Check if the first 5 bytes are between 'a' (97) and 'z' (122).
     * Optimization: (unsigned)(char - 97) <= 25
     */
    __asm__ volatile (
        // Check 1st char (offset 0)
        "movzbl 0(%1), %%eax\n\t"   // Load byte at str[0] into eax
        "subl $97, %%eax\n\t"       // Subtract 'a'
        "cmpl $25, %%eax\n\t"       // Compare with 25
        "ja 1f\n\t"                 // Jump to label 1 (fail) if above

        // Check 2nd char (offset 1)
        "movzbl 1(%1), %%eax\n\t"
        "subl $97, %%eax\n\t"
        "cmpl $25, %%eax\n\t"
        "ja 1f\n\t"

        // Check 3rd char (offset 2)
        "movzbl 2(%1), %%eax\n\t"
        "subl $97, %%eax\n\t"
        "cmpl $25, %%eax\n\t"
        "ja 1f\n\t"

        // Check 4th char (offset 3)
        "movzbl 3(%1), %%eax\n\t"
        "subl $97, %%eax\n\t"
        "cmpl $25, %%eax\n\t"
        "ja 1f\n\t"

        // Check 5th char (offset 4)
        "movzbl 4(%1), %%eax\n\t"
        "subl $97, %%eax\n\t"
        "cmpl $25, %%eax\n\t"
        "ja 1f\n\t"

        // Success path
        "movl $1, %0\n\t"           // Set result to 1
        "jmp 2f\n\t"                // Jump to end

        // Failure path
        "1:\n\t"
        "movl $0, %0\n\t"           // Set result to 0
        
        // End label
        "2:"
        : "=r" (result)             // Output operand
        : "r" (str)                 // Input operand
        : "eax", "cc"               // Clobbered registers
    );
    
    return result;
}
