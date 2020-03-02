PKGS := $(shell go list ./... | grep -v /vendor)

.PHONY: test
test:
	go test $(PKGS)

.PHONY: clean
clean:
	rm k8s-version-checker