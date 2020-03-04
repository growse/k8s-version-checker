SRC_DIR := src/
SRC_FILES := $(wildcard $(SRC_DIR)/*.rs)

.PHONY: build
build: target/debug/k8s-version-checker

.PHONY: test
test:
	cargo test

.PHONY: clean
clean:
	rm -rf target

target/debug/k8s-version-checker: $(SRC_FILES)
	cargo build