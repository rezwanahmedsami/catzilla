#include "router.h"
#include <stdlib.h>

// Stub router functions for DI testing
catzilla_route_node_t* catzilla_route_node_create(void) {
    return calloc(1, sizeof(catzilla_route_node_t));
}

void catzilla_route_node_destroy(catzilla_route_node_t* node) {
    if (node) free(node);
}
