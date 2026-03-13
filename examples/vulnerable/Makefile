CC ?= cc
CFLAGS ?= -g -O0
BIN_DIR := bin

all: $(BIN_DIR)/invalid_read $(BIN_DIR)/leak

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/invalid_read: invalid_read.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

$(BIN_DIR)/leak: leak.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -rf $(BIN_DIR)
