# Hoare Logic Verification Directory

## Language

Hoare-logic specifications embedded in Python. These files encode preconditions, postconditions, and loop invariants as executable assertions or structured comments for external Hoare verifiers.

## Verification

Depending on the toolchain:

- **Runtime assertion checking:**
  ```bash
  python 0000-template.py
  ```

- **Static verification** (if a Hoare verifier is configured):
  Follow the tool-specific instructions for the chosen Hoare-logic framework.

## Naming Convention

```
NNNN-theorem-name.py
```

## Template Reference

See `0000-template.py` for the expected file structure.
