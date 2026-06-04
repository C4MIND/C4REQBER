#!/usr/bin/env python3
"""
TURBO-CDI: Proto Code Generation Script
Generates Python (Pydantic + FastAPI) and TypeScript clients from proto files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROTO_DIR = Path("proto")
GEN_DIR = Path("generated")


def generate_python():
    """Generate Python Pydantic models from proto files."""
    print("🐍 Generating Python code...")
    
    proto_files = list(PROTO_DIR.rglob("*.proto"))
    if not proto_files:
        print("❌ No proto files found")
        return False
    
    # Create output directories
    python_out = GEN_DIR / "python"
    python_out.mkdir(parents=True, exist_ok=True)
    
    for proto_file in proto_files:
        # Use protoc with Python plugin
        cmd = [
            "python3", "-m", "grpc_tools.protoc",
            f"--proto_path={PROTO_DIR}",
            f"--python_out={python_out}",
            f"--pyi_out={python_out}",
            str(proto_file.relative_to(PROTO_DIR)),
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ {proto_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {proto_file.name}: {e.stderr}")
            return False
        except FileNotFoundError:
            print("  ⚠️  grpc_tools not installed. Install: pip install grpcio-tools")
            return False
    
    print(f"✅ Python code generated in {python_out}")
    return True


def generate_typescript():
    """Generate TypeScript clients from proto files."""
    print("📘 Generating TypeScript code...")
    
    ts_out = GEN_DIR / "typescript"
    ts_out.mkdir(parents=True, exist_ok=True)
    
    # Check for protoc-gen-ts
    try:
        subprocess.run(["which", "protoc-gen-ts"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("  ⚠️  protoc-gen-ts not found. Install: npm install -g ts-proto")
        return False
    
    proto_files = list(PROTO_DIR.rglob("*.proto"))
    for proto_file in proto_files:
        cmd = [
            "protoc",
            f"--proto_path={PROTO_DIR}",
            f"--ts_out={ts_out}",
            str(proto_file.relative_to(PROTO_DIR)),
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ {proto_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {proto_file.name}: {e.stderr}")
            return False
    
    print(f"✅ TypeScript code generated in {ts_out}")
    return True


def generate_openapi():
    """Generate OpenAPI spec from proto files."""
    print("📄 Generating OpenAPI spec...")
    
    openapi_out = GEN_DIR / "openapi"
    openapi_out.mkdir(parents=True, exist_ok=True)
    
    # Use protoc-gen-openapi
    try:
        subprocess.run(["which", "protoc-gen-openapi"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("  ⚠️  protoc-gen-openapi not found. Skipping OpenAPI generation.")
        return False
    
    proto_files = list(PROTO_DIR.rglob("*.proto"))
    for proto_file in proto_files:
        cmd = [
            "protoc",
            f"--proto_path={PROTO_DIR}",
            f"--openapi_out={openapi_out}",
            str(proto_file.relative_to(PROTO_DIR)),
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ {proto_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {proto_file.name}: {e.stderr}")
            return False
    
    print(f"✅ OpenAPI spec generated in {openapi_out}")
    return True


def main():
    """Main entry point."""
    print("═══════════════════════════════════════════════════════════")
    print("  TURBO-CDI Proto Code Generation")
    print("═══════════════════════════════════════════════════════════")
    print()
    
    if not PROTO_DIR.exists():
        print(f"❌ Proto directory not found: {PROTO_DIR}")
        sys.exit(1)
    
    results = []
    
    # Generate Python
    results.append(("Python", generate_python()))
    print()
    
    # Generate TypeScript
    results.append(("TypeScript", generate_typescript()))
    print()
    
    # Generate OpenAPI
    results.append(("OpenAPI", generate_openapi()))
    print()
    
    # Summary
    print("═══════════════════════════════════════════════════════════")
    print("  Summary")
    print("═══════════════════════════════════════════════════════════")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    all_success = all(r[1] for r in results)
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
