#ifdef _WIN32

#include "windows_compat.h"
#include <stdlib.h>
#include <string.h>

// Windows implementation of regex functions
// This provides basic pattern matching for string validation

int regcomp(regex_t* preg, const char* pattern, int cflags) {
    if (!preg || !pattern) {
        return 1; // Error
    }

    // Store the pattern
    size_t pattern_len = strlen(pattern);
    preg->pattern = malloc(pattern_len + 1);
    if (!preg->pattern) {
        return 1; // Memory allocation error
    }

    strcpy(preg->pattern, pattern);
    preg->flags = cflags;
    preg->compiled = 1;

    return 0; // Success
}

int regexec(const regex_t* preg, const char* string, size_t nmatch, regmatch_t pmatch[], int eflags) {
    if (!preg || !preg->compiled || !preg->pattern || !string) {
        return 1; // Error
    }

    // Use simple pattern matching
    return simple_pattern_match(preg->pattern, string);
}

void regfree(regex_t* preg) {
    if (preg && preg->pattern) {
        free(preg->pattern);
        preg->pattern = NULL;
        preg->compiled = 0;
    }
}

#endif // _WIN32
