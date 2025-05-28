from decimal import ROUND_HALF_UP, Decimal, getcontext
from typing import List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aws_finops_dashboard.helpers import convert_currency, format_currency

# Set precision context for Decimal operations
getcontext().prec = 6

console = Console()


def create_trend_bars(monthly_costs: List[Tuple[str, float]], currency: str = "USD") -> None:
    """Create colorful trend bars using Rich's styling and precise Decimal math."""
    if not monthly_costs:
        return

    table = Table(box=None, padding=(1, 1), collapse_padding=True)

    table.add_column("Month", style="bright_magenta", width=10)
    table.add_column("Cost", style="bright_cyan", justify="right", width=15)
    table.add_column("", width=50)
    table.add_column("MoM Change", style="bright_yellow", width=12)

    # Convert costs to the target currency
    converted_costs = []
    for month, cost in monthly_costs:
        converted_cost = convert_currency(cost, "USD", currency)
        converted_costs.append((month, converted_cost))

    max_cost = max(cost for _, cost in converted_costs)
    if max_cost == 0:
        console.print("[yellow]All costs are $0.00 for this period[/]")
        return

    prev_cost = None

    for month, cost in converted_costs:
        cost_d = Decimal(str(cost))
        bar_length = int((cost / max_cost) * 40) if max_cost > 0 else 0
        bar = "█" * bar_length

        # Default values
        bar_color = "blue"
        change = ""

        if prev_cost is not None:
            prev_d = Decimal(str(prev_cost))

            if prev_d < Decimal("0.01"):
                if cost_d < Decimal("0.01"):
                    change = "[bright_yellow]0%[/]"
                    bar_color = "yellow"
                else:
                    change = "[bright_red]N/A[/]"
                    bar_color = "bright_red"
            else:
                change_pct = ((cost_d - prev_d) / prev_d * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

                if abs(change_pct) < Decimal("0.01"):
                    change = "[bright_yellow]0%[/]"
                    bar_color = "yellow"
                elif abs(change_pct) > Decimal("999"):
                    color = "bright_red" if change_pct > 0 else "bright_green"
                    change = f"[{color}]{'>+' if change_pct > 0 else '-'}999%[/]"
                    bar_color = color
                else:
                    color = "bright_red" if change_pct > 0 else "bright_green"
                    sign = "+" if change_pct > 0 else ""
                    change = f"[{color}]{sign}{change_pct}%[/]"
                    bar_color = color

        # Format the cost with appropriate currency symbol
        formatted_cost = format_currency(cost, currency)
        
        table.add_row(month, formatted_cost, f"[{bar_color}]{bar}[/]", change)
        prev_cost = cost

    console.print(
        Panel(
            table,
            title=f"[cyan]AWS Cost Trend Analysis ({currency})[/]",
            border_style="bright_blue",
            padding=(1, 1),
        )
    )
