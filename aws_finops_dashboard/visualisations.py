from typing import List, Tuple
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

console = Console()

def create_trend_bars(monthly_costs: List[Tuple[str, float]]) -> None:
    """Create colorful trend bars using Rich's styling."""
    if not monthly_costs:
        return
        
    table = Table(
        #show_header=False,
        box=None,
        padding=(1, 1),  # Increased vertical padding between rows
        collapse_padding=True
    )
    
    table.add_column("Month", style="bright_magenta", width=10)
    table.add_column("Cost", style="bright_cyan", justify="right", width=15)
    table.add_column("", width=50)
    table.add_column("MoM Change", style="bright_yellow", width=12)
    
    max_cost = max(cost for _, cost in monthly_costs)
    if max_cost == 0:
        console.print("[yellow]All costs are $0.00 for this period[/]")
        return
        
    prev_cost = None
    
    for month, cost in monthly_costs:
        bar_length = int((cost / max_cost) * 40) if max_cost > 0 else 0
        
        # Determine bar color based on change from previous month
        if prev_cost is not None:
            if prev_cost < 0.01:
                bar_color = "bright_red" if cost > 0.01 else "yellow"
            else:
                change_pct = ((cost - prev_cost) / prev_cost * 100)
                if abs(change_pct) < 0.01:
                    bar_color = "yellow"
                else:
                    bar_color = "bright_red" if change_pct > 0.01 else "bright_green"
        else:
            bar_color = "blue"
            
        # Add spaces between bar blocks for visual separation
        bar = ("█" * bar_length).rstrip()
        
        # Calculate and format change percentage with better handling
        if prev_cost is not None:
            if prev_cost < 0.01:
                if cost < 0.01:
                    change = "[bright_yellow]0%[/]"
                elif cost < 0.01:
                    change = "[bright_red]+<0.01%[/]"
                else:
                    change = "[bright_red]>+999%[/]"
            else:
                change_pct = ((cost - prev_cost) / prev_cost * 100)
                # Cap percentage changes at 999%
                if abs(change_pct) > 999:
                    change_color = "bright_red" if change_pct > 0 else "bright_green"
                    change = f"[{change_color}]{'>+' if change_pct > 0 else '-'}999%[/]"
                else:
                    change_color = "bright_red" if change_pct > 0 else "bright_green"
                    change = f"[{change_color}]{'+' if change_pct > 0 else ''}{change_pct:.1f}%[/]"
        else:
            change = ""
            
        table.add_row(
            month,
            f"${cost:,.2f}",
            f"[{bar_color}]{bar}[/]",
            change
        )
        prev_cost = cost
   
    console.print(Panel(
        table,
        title="[cyan]AWS Cost Trend Analysis[/]",
        border_style="bright_blue",
        padding=(1, 1)
    ))