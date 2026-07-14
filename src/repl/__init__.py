"""c4reqber REPL package."""
from repl.commands import C4REQBERCommands
from repl.core import C4REQBERShell, Style


__all__ = ["Style", "C4REQBERCommands", "C4REQBERShell", "main"]


def main() -> None:
    """Start interactive shell."""
    shell = C4REQBERCommands()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print(f"\n\n{Style.GREEN}Good luck with your research! ⚡{Style.RESET}\n")
