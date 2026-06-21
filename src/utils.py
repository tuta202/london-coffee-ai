from __future__ import annotations


def format_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
