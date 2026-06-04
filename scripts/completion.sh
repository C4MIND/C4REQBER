#!/bin/bash
# C4REQBER shell completion for bash/zsh
# Install: source <(blast completion)

_c4reqber_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        opts="solve turbo flash turbofactory analyze auto serve agent packages integrations models config setup modes wasm-load wasm-list wasm-execute tui soul policy qa guardian social"
    elif [[ ${COMP_CWORD} -ge 2 ]]; then
        case "${prev}" in
            --scale) opts="mini standard mega giga" ;;
            --pipeline|--p) opts="solve turbo mixed" ;;
            --format|--f) opts="concise detailed bullet code auto" ;;
            --verify-backend) opts="hybrid z3 lean4 coq dafny agda hoare" ;;
            --mode) opts="autopilot interactive assisted" ;;
            *) opts="" ;;
        esac
    fi

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

complete -F _c4reqber_completion blast 2>/dev/null || true
echo "C4REQBER shell completion loaded. Type 'blast ' and press Tab."
