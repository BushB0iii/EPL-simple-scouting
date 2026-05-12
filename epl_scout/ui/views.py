"""
UI Views Layer - Complete view implementations
No business logic, only presentation and event callbacks
Communicates with services layer through callbacks
"""
import flet as ft
from typing import Callable, Optional, List, Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.components import (
    COLORS, create_bento_card, create_player_row, create_scouting_slider,
    create_star_rating, create_empty_state, create_loading_indicator,
    create_snackbar_success, create_snackbar_error, create_search_field,
    create_position_dropdown, create_club_dropdown, create_back_button,
    create_tab_container, format_market_value
)


class ViewFactory:
    """
    Factory for creating complete views
    All views are created as pure UI components
    Business logic is delegated through callbacks
    """
    
    @staticmethod
    def create_home_view(
        on_navigate_players: Callable,
        on_navigate_scouting: Callable,
        on_navigate_watchlist: Callable,
        player_count: int = 0,
        club_count: int = 0
    ) -> ft.Container:
        """Create Home View with Bento Grid"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.Text("EPL SCOUT 25/26", size=32, weight=ft.FontWeight.BOLD, 
                       color=COLORS['text_primary'], text_align=ft.TextAlign.CENTER),
                ft.Text("Premier League Analytics Platform", size=14, 
                       color=COLORS['text_secondary'], text_align=ft.TextAlign.CENTER),
                ft.Container(height=40),
                
                # Bento Grid
                ft.Row([
                    create_bento_card(
                        title="PLAYERS HUB",
                        subtitle="Browse all players",
                        icon=ft.icons.PERSON_SEARCH,
                        on_click=lambda e: on_navigate_players(),
                        stats_label="Total Players",
                        stats_value=f"{player_count}+" if player_count > 0 else "Loading..."
                    ),
                    create_bento_card(
                        title="SCOUTING",
                        subtitle="Find your ideal profile",
                        icon=ft.icons.TUNE,
                        on_click=lambda e: on_navigate_scouting(),
                        stats_label="Position Groups",
                        stats_value="4"
                    ),
                    create_bento_card(
                        title="MY WATCHLIST",
                        subtitle="Track your targets",
                        icon=ft.icons.STAR,
                        on_click=lambda e: on_navigate_watchlist(),
                        stats_label="Watchlisted",
                        stats_value=f"{club_count}+" if club_count > 0 else "0"
                    ),
                ], spacing=20, expand=True),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            expand=True
        )
    
    @staticmethod
    def create_player_hub_view(
        clubs: List[Dict[str, str]],
        positions: List[str],
        on_filter_change: Callable,
        on_search: Callable,
        on_player_click: Callable,
        on_reset_filters: Callable,
        players: List[Dict[str, Any]] = None,
        current_page: int = 1,
        total_pages: int = 1,
        search_term: str = ""
    ) -> ft.Container:
        """Create Player Hub View"""
        # Filter controls
        filter_controls = ft.Row([
            create_position_dropdown(positions, "Position", 
                                    lambda e: on_filter_change('position', e.control.value)),
            create_club_dropdown(clubs, "Club",
                                lambda e: on_filter_change('club', e.control.value)),
            ft.TextField(
                label="Min Value (€M)",
                bgcolor=COLORS['surface'],
                color=COLORS['text_primary'],
                border_color=COLORS['secondary'],
                focused_border_color=COLORS['primary'],
                width=120,
                on_change=lambda e: on_filter_change('min_value', e.control.value)
            ),
            ft.TextField(
                label="Max Value (€M)",
                bgcolor=COLORS['surface'],
                color=COLORS['text_primary'],
                border_color=COLORS['secondary'],
                focused_border_color=COLORS['primary'],
                width=120,
                on_change=lambda e: on_filter_change('max_value', e.control.value)
            ),
        ], spacing=15)
        
        search_bar = ft.Row([
            create_search_field(
                hint_text="Search players...",
                on_change=lambda e: on_search(e.control.value)
            ),
            ft.IconButton(
                icon=ft.icons.FILTER_LIST,
                icon_color=COLORS['primary'],
                tooltip="Filters"
            )
        ], spacing=10)
        
        # Results table
        if players and len(players) > 0:
            table_content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Name", color=COLORS['text_primary'])),
                    ft.DataColumn(ft.Text("Position", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Club", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Market Value", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Age", color=COLORS['text_secondary'])),
                ],
                rows=[
                    create_player_row(
                        player_id=p['player_id'],
                        name=p['name'],
                        position=p['position'],
                        club_name=p['club_name'],
                        market_value=p['market_value'],
                        age=p.get('age', 0),
                        on_click=on_player_click
                    ) for p in players
                ],
                heading_row_color=COLORS['surface'],
                data_row_color=COLORS['surface'],
                data_row_hover_color=COLORS['secondary'],
            )
        else:
            table_content = create_empty_state(
                message="No players found matching your criteria",
                button_text="Reset Filters",
                on_button_click=lambda e: on_reset_filters()
            )
        
        # Pagination
        pagination = ft.Row([
            ft.IconButton(
                icon=ft.icons.CHEVRON_LEFT,
                disabled=current_page <= 1,
                icon_color=COLORS['primary'],
                on_click=lambda e: None  # Will be handled by parent
            ),
            ft.Text(f"Page {current_page} of {total_pages}", 
                   color=COLORS['text_primary']),
            ft.IconButton(
                icon=ft.icons.CHEVRON_RIGHT,
                disabled=current_page >= total_pages,
                icon_color=COLORS['primary'],
                on_click=lambda e: None  # Will be handled by parent
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        return ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                ft.Text("Players Hub", size=24, weight=ft.FontWeight.BOLD, 
                       color=COLORS['text_primary']),
                ft.Container(height=20),
                filter_controls,
                ft.Container(height=15),
                search_bar,
                ft.Container(height=20),
                ft.Container(
                    content=table_content,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                ft.Container(height=10),
                pagination,
            ], spacing=0),
            padding=30,
            expand=True
        )
    
    @staticmethod
    def create_scouting_view(
        positions: List[str],
        on_position_change: Callable,
        on_slider_change: Callable,
        on_hard_filter_change: Callable,
        on_search: Callable,
        on_player_click: Callable,
        slider_values: Dict[str, float] = None,
        search_results: List[Dict[str, Any]] = None,
        is_searching: bool = False
    ) -> ft.Container:
        """Create Scouting View"""
        if slider_values is None:
            slider_values = {
                'xG/90': 75,
                'xA/90': 75,
                'xGI/90': 75,
                'recoveries': 75
            }
        
        # Position selection
        position_section = ft.Column([
            ft.Text("Select Position Group", size=16, weight=ft.FontWeight.BOLD, 
                   color=COLORS['text_primary']),
            ft.Dropdown(
                label="Position Group",
                options=[
                    ft.dropdown.Option("Goalkeeper"),
                    ft.dropdown.Option("Defender"),
                    ft.dropdown.Option("Midfielder"),
                    ft.dropdown.Option("Forward"),
                ],
                bgcolor=COLORS['surface'],
                color=COLORS['text_primary'],
                border_color=COLORS['secondary'],
                focused_border_color=COLORS['primary'],
                expand=True,
                on_change=lambda e: on_position_change(e.control.value)
            ),
        ], spacing=10)
        
        # Sliders section
        sliders_section = ft.Column([
            ft.Text("Define Your Ideal Profile", size=16, weight=ft.FontWeight.BOLD, 
                   color=COLORS['text_primary']),
            ft.Container(height=10),
            create_scouting_slider(
                "xG/90 (Expected Goals per 90)",
                value=slider_values.get('xG/90', 75),
                on_change=lambda e: on_slider_change('xG/90', e.control.value)
            ),
            create_scouting_slider(
                "xA/90 (Expected Assists per 90)",
                value=slider_values.get('xA/90', 75),
                on_change=lambda e: on_slider_change('xA/90', e.control.value)
            ),
            create_scouting_slider(
                "xGI/90 (Expected Goal Involvements per 90)",
                value=slider_values.get('xGI/90', 75),
                on_change=lambda e: on_slider_change('xGI/90', e.control.value)
            ),
            create_scouting_slider(
                "Recoveries/90",
                value=slider_values.get('recoveries', 75),
                on_change=lambda e: on_slider_change('recoveries', e.control.value)
            ),
        ], spacing=15)
        
        # Hard filters (collapsible)
        hard_filters = ft.Column([
            ft.Text("Hard Filters", size=16, weight=ft.FontWeight.BOLD, 
                   color=COLORS['text_primary']),
            ft.Row([
                ft.TextField(
                    label="Min Age",
                    bgcolor=COLORS['surface'],
                    color=COLORS['text_primary'],
                    border_color=COLORS['secondary'],
                    width=100,
                    on_change=lambda e: on_hard_filter_change('min_age', e.control.value)
                ),
                ft.TextField(
                    label="Max Age",
                    bgcolor=COLORS['surface'],
                    color=COLORS['text_primary'],
                    border_color=COLORS['secondary'],
                    width=100,
                    on_change=lambda e: on_hard_filter_change('max_age', e.control.value)
                ),
                ft.TextField(
                    label="Min Value (€M)",
                    bgcolor=COLORS['surface'],
                    color=COLORS['text_primary'],
                    border_color=COLORS['secondary'],
                    width=120,
                    on_change=lambda e: on_hard_filter_change('min_value', e.control.value)
                ),
                ft.TextField(
                    label="Max Value (€M)",
                    bgcolor=COLORS['surface'],
                    color=COLORS['text_primary'],
                    border_color=COLORS['secondary'],
                    width=120,
                    on_change=lambda e: on_hard_filter_change('max_value', e.control.value)
                ),
            ], spacing=15),
            ft.TextField(
                label="Contract Expiration Year",
                hint_text="e.g., 2027",
                bgcolor=COLORS['surface'],
                color=COLORS['text_primary'],
                border_color=COLORS['secondary'],
                width=150,
                on_change=lambda e: on_hard_filter_change('contract_year', e.control.value)
            ),
        ], spacing=15)
        
        # Search button
        search_button = ft.ElevatedButton(
            "SEARCH",
            bgcolor=COLORS['primary'],
            color='#000000',
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda e: on_search()
        )
        
        # Results section
        if is_searching:
            results_section = create_loading_indicator()
        elif search_results and len(search_results) > 0:
            results_section = ft.Column([
                ft.Text(f"Found {len(search_results)} players", 
                       size=14, color=COLORS['text_secondary']),
                ft.Container(height=10),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("#", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("Player", color=COLORS['text_primary'])),
                        ft.DataColumn(ft.Text("Club", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("Position", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("Match Score", color=COLORS['primary'])),
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(i+1), color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(r['player_name'], color=COLORS['text_primary'])),
                            ft.DataCell(ft.Text(r['club_name'], color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(r['position'], color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(f"{r['match_score']}%", 
                                             color=COLORS['primary'], 
                                             weight=ft.FontWeight.BOLD)),
                        ])
                        for i, r in enumerate(search_results)
                    ],
                    heading_row_color=COLORS['surface'],
                    data_row_color=COLORS['surface'],
                    data_row_hover_color=COLORS['secondary'],
                )
            ], spacing=10)
        else:
            results_section = ft.Container()
        
        return ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                ft.Text("Scouting", size=24, weight=ft.FontWeight.BOLD, 
                       color=COLORS['text_primary']),
                ft.Text("Find players matching your ideal profile", size=14, 
                       color=COLORS['text_secondary']),
                ft.Container(height=20),
                
                ft.Column([
                    position_section,
                    ft.Divider(color=COLORS['secondary']),
                    sliders_section,
                    ft.Divider(color=COLORS['secondary']),
                    hard_filters,
                    ft.Container(height=20),
                    search_button,
                    ft.Container(height=20),
                    results_section,
                ], spacing=20, scroll=ft.ScrollMode.AUTO),
            ], spacing=0),
            padding=30,
            expand=True
        )
    
    @staticmethod
    def create_watchlist_view(
        watchlist_data: List[Dict[str, Any]],
        on_notes_change: Callable,
        on_rating_change: Callable,
        on_delete_player: Callable,
        on_delete_all: Callable,
        on_navigate_hub: Callable,
        on_player_click: Callable,
        search_term: str = ""
    ) -> ft.Container:
        """Create Watchlist View"""
        # Toolbar
        toolbar = ft.Row([
            create_search_field(
                hint_text="Search watchlist...",
                on_change=lambda e: None  # Handled by parent
            ).build(),
            ft.IconButton(
                icon=ft.icons.DELETE_SWEEP,
                icon_color=COLORS['error'],
                tooltip="Delete All",
                on_click=lambda e: on_delete_all()
            ),
        ], spacing=10)
        
        # Watchlist table
        if watchlist_data and len(watchlist_data) > 0:
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Name", color=COLORS['text_primary'])),
                    ft.DataColumn(ft.Text("Club", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Position", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Notes", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("Rating", color=COLORS['text_secondary'])),
                    ft.DataColumn(ft.Text("", color=COLORS['text_secondary'])),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item['player_name'], 
                                           color=COLORS['text_primary'])),
                        ft.DataCell(ft.Text(item['club_name'], 
                                           color=COLORS['text_secondary'])),
                        ft.DataCell(ft.Text(item['position'], 
                                           color=COLORS['text_secondary'])),
                        ft.DataCell(ft.TextField(
                            value=item.get('notes', ''),
                            hint_text="Add notes...",
                            bgcolor=COLORS['surface'],
                            color=COLORS['text_primary'],
                            border_color=COLORS['secondary'],
                            focused_border_color=COLORS['primary'],
                            width=150,
                            content_padding=8,
                            text_size=12,
                            on_change=lambda e, pid=item['player_id']: 
                                on_notes_change(pid, e.control.value)
                        )),
                        ft.DataCell(create_star_rating(
                            item.get('rating', 0),
                            lambda r, pid=item['player_id']: on_rating_change(pid, r)
                        )),
                        ft.DataCell(ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=COLORS['error'],
                            on_click=lambda e, pid=item['player_id']: on_delete_player(pid)
                        )),
                    ])
                    for item in watchlist_data
                ],
                heading_row_color=COLORS['surface'],
                data_row_color=COLORS['surface'],
                data_row_hover_color=COLORS['secondary'],
            )
            
            content = ft.Column([
                ft.Container(height=20),
                ft.Row([
                    ft.Text("My Watchlist", size=24, weight=ft.FontWeight.BOLD, 
                           color=COLORS['text_primary']),
                    ft.Text(f"({len(watchlist_data)} players)", size=14, 
                           color=COLORS['text_secondary']),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=20),
                toolbar,
                ft.Container(height=15),
                ft.Container(
                    content=table,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO
                ),
            ], spacing=0)
        else:
            content = create_empty_state(
                message="Your watchlist is empty. Add players from the Hub.",
                button_text="Go to Players Hub",
                on_button_click=lambda e: on_navigate_hub()
            )
        
        return ft.Container(
            content=content,
            padding=30,
            expand=True
        )
    
    @staticmethod
    def create_player_dashboard_view(
        player_info: Dict[str, Any],
        club_name: str,
        season_stats: Dict[str, Any],
        gw_records: List[Dict[str, Any]],
        similar_players: List[Dict[str, Any]],
        on_back: Callable,
        on_add_to_watchlist: Callable,
        on_find_similar: Callable,
        on_tab_change: Callable,
        charts: Dict[str, str] = None,
        is_in_watchlist: bool = False
    ) -> ft.Container:
        """Create Player Dashboard View"""
        if charts is None:
            charts = {}
        
        # Header
        header = ft.Row([
            create_back_button(on_back),
            ft.Column([
                ft.Text(player_info.get('name', 'Unknown'), 
                       size=24, weight=ft.FontWeight.BOLD, color=COLORS['text_primary']),
                ft.Row([
                    ft.Text(club_name, color=COLORS['text_secondary']),
                    ft.Text(" • ", color=COLORS['text_secondary']),
                    ft.Text(player_info.get('position', ''), color=COLORS['text_secondary']),
                ]),
            ], spacing=2),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.icons.STAR if is_in_watchlist else ft.icons.STAR_BORDER,
                icon_color=COLORS['primary'],
                tooltip="Add to Watchlist",
                on_click=lambda e: on_add_to_watchlist()
            ),
        ], alignment=ft.MainAxisAlignment.START)
        
        # Info sidebar
        info_sidebar = ft.Column([
            ft.Container(
                content=ft.Image(
                    src=player_info.get('image_url', ''),
                    width=200,
                    height=200,
                    fit=ft.ImageFit.COVER,
                    error_content=ft.Container(
                        content=ft.Icon(ft.icons.PERSON, size=80, color=COLORS['secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=100,
                        width=200,
                        height=200,
                        alignment=ft.alignment.center
                    )
                ),
                border_radius=12,
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            ),
            ft.Container(height=20),
            ft.Column([
                ft.Row([
                    ft.Text("Nationality:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(player_info.get('country_of_citizenship', 'N/A'), 
                           color=COLORS['text_primary']),
                ]),
                ft.Row([
                    ft.Text("Age:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(str(player_info.get('age', 'N/A')), color=COLORS['text_primary']),
                ]),
                ft.Row([
                    ft.Text("Position:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(player_info.get('sub_position', player_info.get('position', 'N/A')), 
                           color=COLORS['text_primary']),
                ]),
                ft.Row([
                    ft.Text("Club:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(club_name, color=COLORS['text_primary']),
                ]),
                ft.Row([
                    ft.Text("Contract:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(player_info.get('contract_expiration_date', 'N/A'), 
                           color=COLORS['text_primary']),
                ]),
                ft.Row([
                    ft.Text("Market Value:", size=12, color=COLORS['text_secondary'], width=100),
                    ft.Text(format_market_value(player_info.get('market_value_in_eur', 0)), 
                           color=COLORS['primary'], weight=ft.FontWeight.BOLD),
                ]),
            ], spacing=8),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Find Similar",
                bgcolor=COLORS['primary'],
                color='#000000',
                on_click=lambda e: on_find_similar()
            ),
        ], spacing=10)
        
        # Overview tab content
        overview_content = ft.Row([
            ft.Container(
                content=info_sidebar,
                width=280
            ),
            ft.VerticalDivider(width=20, color=COLORS['secondary']),
            ft.Column([
                ft.Text("Performance Radar", size=16, weight=ft.FontWeight.BOLD, 
                       color=COLORS['text_primary']),
                ft.Container(
                    content=ft.Image(src=charts.get('radar', '')) if charts.get('radar') 
                    else ft.Container(
                        content=ft.Text("Chart unavailable", color=COLORS['text_secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=20,
                        alignment=ft.alignment.center
                    ),
                    width=400,
                    height=400
                ),
                ft.Container(height=20),
                ft.Text("Season Statistics", size=16, weight=ft.FontWeight.BOLD, 
                       color=COLORS['text_primary']),
                ft.Container(
                    content=ViewFactory._create_stats_grid(season_stats, player_info.get('position', '')),
                    expand=True
                ),
            ], spacing=15, expand=True, scroll=ft.ScrollMode.AUTO),
        ], spacing=20, expand=True)
        
        # GW Records tab content
        gw_content = ft.Column([
            ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("GW", color=COLORS['text_primary'])),
                        ft.DataColumn(ft.Text("Min", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("G", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("A", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("CS", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("xG", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("xA", color=COLORS['text_secondary'])),
                        ft.DataColumn(ft.Text("ICT", color=COLORS['text_secondary'])),
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(r.get('gw', 0)), color=COLORS['text_primary'])),
                            ft.DataCell(ft.Text(str(int(r.get('minutes', 0))), color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(str(int(r.get('goals_scored', 0))), color=COLORS['text_primary'])),
                            ft.DataCell(ft.Text(str(int(r.get('assists', 0))), color=COLORS['text_primary'])),
                            ft.DataCell(ft.Text(str(int(r.get('clean_sheets', 0))), color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(f"{r.get('expected_goals', 0):.2f}", color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(f"{r.get('expected_assists', 0):.2f}", color=COLORS['text_secondary'])),
                            ft.DataCell(ft.Text(f"{r.get('ict_index', 0):.1f}", color=COLORS['primary'])),
                        ])
                        for r in gw_records
                    ],
                    heading_row_color=COLORS['surface'],
                    data_row_color=COLORS['surface'],
                ),
                scroll=ft.ScrollMode.HORIZONTAL,
                expand=True
            ),
            ft.Container(height=10),
            ft.Row([
                ft.Text(f"Games: {len(gw_records)}", color=COLORS['text_secondary']),
                ft.Text(f"Total Goals: {sum(r.get('goals_scored', 0) for r in gw_records)}", 
                       color=COLORS['text_secondary']),
                ft.Text(f"Total Assists: {sum(r.get('assists', 0) for r in gw_records)}", 
                       color=COLORS['text_secondary']),
            ], spacing=30),
        ], expand=True)
        
        # Performance tab content
        performance_content = ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Image(src=charts.get('minutes_gw', '')) if charts.get('minutes_gw')
                    else ft.Container(
                        content=ft.Text("Minutes/GW Chart", color=COLORS['text_secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=20,
                        width=300,
                        height=250,
                        alignment=ft.alignment.center
                    ),
                    width=350,
                    height=280
                ),
                ft.Container(
                    content=ft.Image(src=charts.get('goals_xg', '')) if charts.get('goals_xg')
                    else ft.Container(
                        content=ft.Text("Goals vs xG Chart", color=COLORS['text_secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=20,
                        width=350,
                        height=280,
                        alignment=ft.alignment.center
                    ),
                    width=350,
                    height=280
                ),
            ], spacing=20),
            ft.Row([
                ft.Container(
                    content=ft.Image(src=charts.get('assists_xa', '')) if charts.get('assists_xa')
                    else ft.Container(
                        content=ft.Text("Assists vs xA Chart", color=COLORS['text_secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=20,
                        width=350,
                        height=280,
                        alignment=ft.alignment.center
                    ),
                    width=350,
                    height=280
                ),
                ft.Container(
                    content=ft.Image(src=charts.get('ict', '')) if charts.get('ict')
                    else ft.Container(
                        content=ft.Text("ICT Index Chart", color=COLORS['text_secondary']),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=20,
                        width=350,
                        height=280,
                        alignment=ft.alignment.center
                    ),
                    width=350,
                    height=280
                ),
            ], spacing=20),
        ], expand=True, scroll=ft.ScrollMode.AUTO)
        
        # Create tabs
        tabs = [
            ft.Tab(text="Overview", content=overview_content),
            ft.Tab(text="GW Records", content=gw_content),
            ft.Tab(text="Performance", content=performance_content),
        ]
        
        return ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                header,
                ft.Container(height=20),
                create_tab_container(tabs),
            ], spacing=0),
            padding=30,
            expand=True
        )
    
    @staticmethod
    def _create_stats_grid(stats: Dict[str, Any], position: str) -> ft.GridView:
        """Create statistics grid based on position"""
        # Common stats display
        stat_items = []
        
        if stats:
            display_stats = [
                ('Minutes', stats.get('total_minutes', 0)),
                ('Goals', stats.get('total_goals', 0)),
                ('Assists', stats.get('total_assists', 0)),
                ('G/A per 90', f"{stats.get('goal_contributions_per_90', 0):.2f}"),
                ('Games', stats.get('games_played', 0)),
                ('Avg ICT', stats.get('average_ict_index', 0)),
            ]
            
            for label, value in display_stats:
                stat_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(label, size=11, color=COLORS['text_secondary']),
                            ft.Text(str(value), size=16, weight=ft.FontWeight.BOLD, 
                                   color=COLORS['primary']),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        bgcolor=COLORS['surface'],
                        border_radius=8,
                        padding=15,
                    )
                )
        
        return ft.GridView(
            runs_count=3,
            max_extent=150,
            children=stat_items,
            spacing=10,
            run_spacing=10,
            expand=True
        )
    
    @staticmethod
    def create_similar_players_modal(
        player_name: str,
        similar_players: List[Dict[str, Any]],
        on_close: Callable,
        on_player_select: Callable
    ) -> ft.AlertDialog:
        """Create modal dialog for similar players"""
        return ft.AlertDialog(
            title=ft.Text(f"Similar Players to {player_name}", 
                         color=COLORS['text_primary']),
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Text(f"{i+1}.", color=COLORS['text_secondary'], width=30),
                        title=ft.Text(p.get('player_name', ''), color=COLORS['text_primary']),
                        subtitle=ft.Text(f"{p.get('club_name', '')} • {p.get('position', '')}", 
                                       color=COLORS['text_secondary']),
                        trailing=ft.Text(f"{p.get('match_score', 0)}%", 
                                       color=COLORS['primary'], 
                                       weight=ft.FontWeight.BOLD),
                        on_click=lambda e, pid=p.get('player_id'): on_player_select(pid)
                    )
                    for i, p in enumerate(similar_players)
                ], spacing=5),
                width=400
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: on_close()),
            ],
            bgcolor=COLORS['surface'],
            actions_alignment=ft.MainAxisAlignment.END
        )
