#!/bin/bash
# Install formal verification backends for c4reqber
# macOS only — uses Homebrew

set -e

echo "=== Installing Formal Verification Backends ==="
echo ""

# Lean4 (via elan)
if ! command -v lean &> /dev/null; then
    echo "Installing Lean4 via elan..."
    curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
    source "$HOME/.elan/env"
else
    echo "✓ Lean4: $(lean --version | head -1)"
fi

# Coq / Rocq
if ! command -v coqc &> /dev/null; then
    echo "Installing Coq (Rocq) via brew..."
    brew install coq
else
    echo "✓ Coq: $(coqc --version | head -1)"
fi

# Dafny
if ! command -v dafny &> /dev/null; then
    echo "Installing Dafny via brew..."
    brew install dafny
else
    echo "✓ Dafny: $(dafny --version | head -1)"
fi

# Agda
if ! command -v agda &> /dev/null; then
    echo "Installing Agda via brew..."
    brew install agda
else
    echo "✓ Agda: $(agda --version | head -1)"
fi

# Z3 (for Hoare logic)
if ! python3 -c "import z3" 2>/dev/null; then
    echo "Installing Z3 Python bindings..."
    pip install z3-solver
else
    echo "✓ Z3 Python: already installed"
fi

echo ""
echo "=== All verifiers installed ==="
echo "Run tests: python3 -m pytest tests/verification/ -q"
