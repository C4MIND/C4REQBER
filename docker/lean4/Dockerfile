FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install elan (Lean package manager)
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
ENV PATH="/root/.elan/bin:${PATH}"

# Install latest Lean 4 stable
RUN elan toolchain install stable && elan default stable

# Pre-install mathlib4 cache tools
RUN elan run stable lake --help > /dev/null 2>&1 || true

WORKDIR /work

# Entrypoint: run lean on provided file
ENTRYPOINT ["lean"]
CMD ["--help"]
