#include <stdlib.h>

int main(void) {
    char *buf = (char *)malloc(64);
    if (!buf) {
        return 1;
    }
    // Intentionally leak memory
    return 0;
}
