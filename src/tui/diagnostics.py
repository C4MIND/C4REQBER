from __future__ import annotations


"""
TUI: Diagnostics
Diagnostic wizard and related methods for C4TUI.
"""


from rich import box
from rich.panel import Panel
from rich.text import Text


def make_diagnostic_wizard(t, router, q1: str = '', q2: str = '', q3: str = '') -> Panel:
    """Render the 30-second diagnostic wizard panel."""
    _DIAG_Q1_MAP = {'1': 'Регулятивный', '2': 'Структурний', '3': 'Смисловий', '4': 'Реляціонний'}
    _DIAG_Q2_MAP = {'1': 'Градієнтний', '2': 'Дискретний', '3': 'Циклічний', '4': 'Каскадний'}
    _DIAG_Q3_MAP = {'1': 'Упругий', '2': 'Умовно-упругий', '3': 'Необоротний'}
    _DIAG_SITUATION_MAP = {'Регулятивний': 'overload', 'Структурний': 'rigidity', 'Смисловий': 'chaos', 'Реляціонний': 'isolation'}

    def _marker(selected: str, key: str, label: str) -> str:
        if selected == key:
            return f"[bold #4ECDC4]▶ [{key}] {label}[/]"
        return f"  [{key}] {label}"

    q1_text = (
        f"  [bold]1. ЩО трансформується?[/]\n"
        f"     {_marker(q1, '1', 'Стан')}\n"
        f"     {_marker(q1, '2', 'Структура')}\n"
        f"     {_marker(q1, '3', 'Смисл')}\n"
        f"     {_marker(q1, '4', 'Відношення')}"
    )

    q2_text = (
        f"  [bold]2. ЯК проходить зміна?[/]\n"
        f"     {_marker(q2, '1', 'Поступово')}\n"
        f"     {_marker(q2, '2', 'Стрибком')}\n"
        f"     {_marker(q2, '3', 'Циклічно')}\n"
        f"     {_marker(q2, '4', 'Каскадно')}"
    )

    q3_text = (
        f"  [bold]3. ОБРАТИМО чи зміна?[/]\n"
        f"     {_marker(q3, '1', 'Да')}\n"
        f"     {_marker(q3, '2', 'Умовно')}\n"
        f"     {_marker(q3, '3', 'Ні')}"
    )

    code = ''
    if q1 and q2 and q3:
        p1 = _DIAG_Q1_MAP.get(q1, 'Регулятивний')
        p2 = _DIAG_Q2_MAP.get(q2, 'Градієнтний')
        p3 = _DIAG_Q3_MAP.get(q3, 'Упругий')
        code = f"{p1}-{p2}-{p3}"

        situation = _DIAG_SITUATION_MAP.get(p1, 'chaos')
        gap_pct = 25 if p3 == 'Упругий' else (50 if p3 == 'Умовно-упругий' else 85)
        ops = router.route(situation, gap_pct)

        level = 'SIMPLE' if gap_pct < 30 else ('MEDIUM' if gap_pct <= 70 else 'COMPLEX')
        info = (
            f"\n\n  [bold #4ECDC4]Ваш код:[/] [{code}]\n"
            f"  [bold #4ECDC4]Рекомендовані оператори:[/] {' → '.join(ops)}\n"
            f"  [bold #4ECDC4]Рівень складності:[/] {level} (GAP < {'30' if gap_pct < 30 else '70' if gap_pct <= 70 else '100'}%)"
        )
    else:
        info = "\n\n  [dim]Виберіть відповіді на все 3 питання[/]"

    body = Text.from_markup(
        f"{q1_text}\n\n{q2_text}\n\n{q3_text}{info}"
    )

    return Panel(
        body,
        title="[bold]🧠 ДІАГНОСТЮКА ПРОБЛЕМА (30 секунд)[/]",
        border_style="bold #FFD93D",
        box=box.ROUNDED,
        padding=(1, 4),
    )


def run_diagnostic_wizard(keyboard_reader, make_diagnostic_wizard_fn, router) -> dict:
    """Interactive diagnostic wizard returning problem profile."""
    _DIAG_Q1_MAP = {'1': 'Регулятивний', '2': 'Структурний', '3': 'Смисловий', '4': 'Реляціонний'}
    _DIAG_Q2_MAP = {'1': 'Градієнтний', '2': 'Дискретний', '3': 'Циклічний', '4': 'Каскадний'}
    _DIAG_Q3_MAP = {'1': 'Упругий', '2': 'Умовно-упругий', '3': 'Необоротний'}
    _DIAG_SITUATION_MAP = {'Регулятивний': 'overload', 'Структурний': 'rigidity', 'Смисловий': 'chaos', 'Реляціонний': 'isolation'}

    selections: dict = {'q1': '1', 'q2': '1', 'q3': '1'}
    current_q = 'q1'

    with keyboard_reader as kr:
        while True:
            import sys
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            print(make_diagnostic_wizard_fn(selections['q1'], selections['q2'], selections['q3']))
            sys.stdout.flush()

            key = kr.read_key(timeout=0.3)

            if key is None:
                continue

            if key == ('esc',) or key == ('char', 'q') or key == ('char', 'Q'):
                return {}

            if key == ('char', '1'):
                selections[current_q] = '1'
                if current_q == 'q1':
                    current_q = 'q2'
                elif current_q == 'q2':
                    current_q = 'q3'
                else:
                    continue

            elif key == ('char', '2'):
                selections[current_q] = '2'
                if current_q == 'q1':
                    current_q = 'q2'
                elif current_q == 'q2':
                    current_q = 'q3'
                else:
                    continue

            elif key == ('char', '3'):
                selections[current_q] = '3'
                if current_q == 'q1':
                    current_q = 'q2'
                elif current_q == 'q2':
                    current_q = 'q3'
                else:
                    continue

            elif key == ('char', '4'):
                if current_q in ('q1', 'q2'):
                    selections[current_q] = '4'
                    if current_q == 'q1':
                        current_q = 'q2'
                    elif current_q == 'q2':
                        current_q = 'q3'
                else:
                    continue

            elif key == ('enter',):
                if selections['q1'] and selections['q2'] and selections['q3']:
                    break

    p1 = _DIAG_Q1_MAP.get(selections['q1'], 'Регулятивний')
    p2 = _DIAG_Q2_MAP.get(selections['q2'], 'Градієнтний')
    p3 = _DIAG_Q3_MAP.get(selections['q3'], 'Упругий')
    code = f"{p1}-{p2}-{p3}"

    situation = _DIAG_SITUATION_MAP.get(p1, 'chaos')
    gap_pct = 25 if p3 == 'Упругий' else (50 if p3 == 'Умовно-упругий' else 85)
    ops = router.route(situation, gap_pct)

    fp = router.fingerprint("diagnostic problem")
    fp.update({
        'code': code,
        'gap_pct': gap_pct,
        'operator_chain': ops,
    })
    return fp
