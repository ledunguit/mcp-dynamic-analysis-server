CC ?= cc
CFLAGS ?= -g -O0
CFLAGS_ASAN ?= -g -O0 -fsanitize=address -fno-omit-frame-pointer
BIN_DIR := bin

all: $(BIN_DIR)/invalid_read $(BIN_DIR)/leak
asan: $(BIN_DIR)/invalid_read_asan $(BIN_DIR)/leak_asan

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/invalid_read: invalid_read.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

$(BIN_DIR)/leak: leak.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

$(BIN_DIR)/invalid_read_asan: invalid_read.c | $(BIN_DIR)
	$(CC) $(CFLAGS_ASAN) -o $@ $<

$(BIN_DIR)/leak_asan: leak.c | $(BIN_DIR)
	$(CC) $(CFLAGS_ASAN) -o $@ $<

clean:
	rm -rf $(BIN_DIR)
