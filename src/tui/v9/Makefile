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
