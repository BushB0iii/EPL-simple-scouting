"""
UI Components Layer - Reusable Flet UI components
No business logic, only presentation and event callbacks
"""
import flet as ft
from typing import Callable, Optional, List, Dict, Any


# Color constants from spec
COLORS = {
    'background': '#1A1A1A',
    'surface': '#2D2D2D',
    'primary': '#FFD700',
    'secondary': '#4A4A4A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'success': '#4CAF50',
    'error': '#F44336',
    'warning': '#FF9800'
}


def create_bento_card(
    title: str,
    subtitle: str,
    icon: str,
    on_click: Callable,
    stats_label: str = "",
    stats_value: str = ""
) -> ft.Container:
    """Create a bento grid card for home view"""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(name=icon, size=40, color=COLORS['primary']),
                ft.Column([
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=COLORS['text_primary']),
                    ft.Text(subtitle, size=12, color=COLORS['text_secondary']),
                ], spacing=2, expand=True)
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(height=10),
            ft.Divider(color=COLORS['secondary'], height=1),
            ft.Container(height=10),
            ft.Row([
                ft.Text(stats_label, size=11, color=COLORS['text_secondary']),
                ft.Text(stats_value, size=14, weight=ft.FontWeight.BOLD, color=COLORS['primary']),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=5),
        bgcolor=COLORS['surface'],
        border_radius=12,
        padding=20,
        on_click=on_click,
        ink=True,
        expand=True
    )


def create_player_row(
    player_id: str,
    name: str,
    position: str,
    club_name: str,
    market_value: int,
    age: int,
    on_click: Callable
) -> ft.DataRow:
    """Create a row for player table"""
    value_str = format_market_value(market_value)
    
    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(name, color=COLORS['text_primary'])),
            ft.DataCell(ft.Text(position, color=COLORS['text_secondary'])),
            ft.DataCell(ft.Text(club_name, color=COLORS['text_secondary'])),
            ft.DataCell(ft.Text(value_str, color=COLORS['primary'])),
            ft.DataCell(ft.Text(str(age), color=COLORS['text_secondary'])),
        ],
        on_select_changed=lambda e: on_click(player_id)
    )


def format_market_value(value: int) -> str:
    """Format market value in millions"""
    if value >= 1000000:
        return f"€{value / 1000000:.1f}M"
    elif value >= 1000:
        return f"€{value / 1000:.0f}K"
    else:
        return f"€{value}"


def create_scouting_slider(
    label: str,
    min_val: float = 50,
    max_val: float = 95,
    value: float = 75,
    on_change: Optional[Callable] = None
) -> ft.Column:
    """Create a slider for scouting view"""
    return ft.Column([
        ft.Row([
            ft.Text(label, size=14, color=COLORS['text_primary']),
            ft.Text(f"{int(value)}%", size=12, color=COLORS['primary'], width=50, text_align=ft.TextAlign.RIGHT)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Slider(
            min=min_val,
            max=max_val,
            divisions=int(max_val - min_val),
            value=value,
            active_color=COLORS['primary'],
            inactive_color=COLORS['secondary'],
            on_change=on_change
        ),
        ft.Row([
            ft.Text("Good", size=10, color=COLORS['text_secondary']),
            ft.Text("Elite", size=10, color=COLORS['text_secondary'])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ], spacing=5)


def create_star_rating(rating: int, on_click: Callable) -> ft.Row:
    """Create clickable star rating component"""
    stars = []
    for i in range(1, 6):
        is_filled = i <= rating
        stars.append(
            ft.IconButton(
                icon=ft.icons.STAR if is_filled else ft.icons.STAR_BORDER,
                icon_color=COLORS['primary'] if is_filled else COLORS['secondary'],
                icon_size=20,
                on_click=lambda e, r=i: on_click(r)
            )
        )
    return ft.Row(stars, spacing=0)


def create_empty_state(
    message: str,
    button_text: Optional[str] = None,
    on_button_click: Optional[Callable] = None
) -> ft.Container:
    """Create empty state component"""
    content = [
        ft.Icon(ft.icons.SEARCH_OFF, size=60, color=COLORS['secondary']),
        ft.Container(height=20),
        ft.Text(message, size=16, color=COLORS['text_secondary'], text_align=ft.TextAlign.CENTER),
    ]
    
    if button_text and on_button_click:
        content.extend([
            ft.Container(height=20),
            ft.ElevatedButton(
                button_text,
                bgcolor=COLORS['primary'],
                color='#000000',
                on_click=on_button_click
            )
        ])
    
    return ft.Container(
        content=ft.Column(content, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        alignment=ft.alignment.center
    )


def create_loading_indicator() -> ft.Container:
    """Create loading indicator"""
    return ft.Container(
        content=ft.CircularProgressIndicator(color=COLORS['primary']),
        expand=True,
        alignment=ft.alignment.center
    )


def create_snackbar_success(message: str) -> ft.SnackBar:
    """Create success snackbar"""
    return ft.SnackBar(
        content=ft.Text(message, color='#000000'),
        bgcolor=COLORS['success'],
        behavior=ft.SnackBarBehavior.FLOATING
    )


def create_snackbar_error(message: str) -> ft.SnackBar:
    """Create error snackbar"""
    return ft.SnackBar(
        content=ft.Text(message, color=COLORS['text_primary']),
        bgcolor=COLORS['error'],
        behavior=ft.SnackBarBehavior.FLOATING
    )


def create_search_field(
    hint_text: str = "Search...",
    on_change: Optional[Callable] = None,
    on_submit: Optional[Callable] = None
) -> ft.TextField:
    """Create search text field with debounce capability"""
    return ft.TextField(
        hint_text=hint_text,
        prefix_icon=ft.icons.SEARCH,
        bgcolor=COLORS['surface'],
        color=COLORS['text_primary'],
        border_color=COLORS['secondary'],
        focused_border_color=COLORS['primary'],
        content_padding=12,
        expand=True,
        on_change=on_change,
        on_submit=on_submit
    )


def create_position_dropdown(
    positions: List[str],
    label: str = "Position",
    on_change: Optional[Callable] = None
) -> ft.Dropdown:
    """Create position dropdown"""
    options = [ft.dropdown.Option(pos) for pos in positions]
    options.insert(0, ft.dropdown.Option("All"))
    
    return ft.Dropdown(
        label=label,
        options=options,
        bgcolor=COLORS['surface'],
        color=COLORS['text_primary'],
        border_color=COLORS['secondary'],
        focused_border_color=COLORS['primary'],
        expand=True,
        on_change=on_change
    )


def create_club_dropdown(
    clubs: List[Dict[str, str]],
    label: str = "Club",
    on_change: Optional[Callable] = None
) -> ft.Dropdown:
    """Create club dropdown"""
    options = [ft.dropdown.Option(c['club_id'], c['club_name']) for c in clubs]
    options.insert(0, ft.dropdown.Option("All", "All Clubs"))
    
    return ft.Dropdown(
        label=label,
        options=options,
        bgcolor=COLORS['surface'],
        color=COLORS['text_primary'],
        border_color=COLORS['secondary'],
        focused_border_color=COLORS['primary'],
        expand=True,
        on_change=on_change
    )


def create_back_button(on_click: Callable) -> ft.IconButton:
    """Create back navigation button"""
    return ft.IconButton(
        icon=ft.icons.ARROW_BACK,
        icon_color=COLORS['text_primary'],
        on_click=on_click
    )


def create_tab_container(tabs: List[ft.Tab]) -> ft.Container:
    """Create tab container with consistent styling"""
    return ft.Container(
        content=ft.Tabs(
            tabs=tabs,
            selected_label_color=COLORS['primary'],
            unselected_label_color=COLORS['text_secondary'],
            indicator_color=COLORS['primary'],
            divider_color=COLORS['secondary'],
            expand=True
        ),
        expand=True
    )
