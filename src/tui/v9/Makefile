.PHONY: build test snapshot run clean tidy

build:
	go build -o bin/c4tui-v9 ./cmd/c4tui-v9

test:
	go test ./... -count=1

snapshot:
	go test ./tests/snapshots/ -count=1 -update

run: build
	./bin/c4tui-v9

tidy:
	go mod tidy

clean:
	rm -rf bin/

# Local release: build for current platform
release: clean
	mkdir -p bin
	go build -ldflags="-s -w" -o bin/c4tui-v9 ./cmd/c4tui-v9
	@echo "Built: bin/c4tui-v9 ($$(du -h bin/c4tui-v9 | awk '{print $$1}'))"

# Cross-compile (requires CGO=0 for full static)
release-all: clean
	mkdir -p bin
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/c4tui-v9-linux-amd64 ./cmd/c4tui-v9
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -o bin/c4tui-v9-darwin-arm64 ./cmd/c4tui-v9
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -ldflags="-s -w" -o bin/c4tui-v9-darwin-amd64 ./cmd/c4tui-v9
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o bin/c4tui-v9-windows-amd64.exe ./cmd/c4tui-v9
	@ls -la bin/

# Headless e2e probe
probe:
	go build -o bin/c4tui-v9-probe ./cmd/c4tui-v9-probe
	@echo "Probe: bin/c4tui-v9-probe (run with ./bin/c4tui-v9-probe <query>)"

probe-run: probe
	./bin/c4tui-v9-probe "$(QUERY)"

# TUI main
tui: build
	./bin/c4tui-v9
