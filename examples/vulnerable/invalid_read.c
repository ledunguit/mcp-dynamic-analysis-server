#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *buf = (char *)malloc(4);
    if (!buf) {
        return 1;
    }
    strcpy(buf, "abc");
    free(buf);
    // Use-after-free style invalid read
    printf("%c\n", buf[0]);
    return 0;
}
