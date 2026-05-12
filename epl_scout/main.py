#!/usr/bin/env python3
"""
EPL SCOUT 25/26 - Main Application Entry Point
Modular Architecture with Loose Coupling

Directory Structure:
/epl_scout/
├── data/           # CSV data files
├── models/         # Pure data structures (entities)
├── core/           # Business logic & Data Access
│   ├── database.py      # Database operations
│   └── algorithms.py    # Scouting algorithms
├── ui/             # Presentation layer
│   ├── components.py    # Reusable UI components
│   └── views.py         # Complete view implementations
└── main.py         # Application coordinator
"""
import flet as ft
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import ssl
import urllib.request

# Fix SSL certificate verification issue
ssl._create_default_https_context = ssl._create_unverified_context

# Import layers
from models.entities import PlayerInfo, PlayerStats
from core.database import DatabaseManager
from core.algorithms import AlgorithmService
from ui.components import COLORS, create_snackbar_success, create_snackbar_error
from ui.views import ViewFactory


class EPLScoutApp:
    """
    Main Application Coordinator
    - Manages navigation between views
    - Coordinates between UI and Business Logic layers
    - Handles application state
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = DatabaseManager(str(Path(__file__).parent / "data" / "epl_scout.db"))
        self.algorithms = AlgorithmService()
        
        # Application State
        self.current_view = "home"
        self.previous_view = "home"
        self.current_player_id: Optional[str] = None
        
        # Caches
        self.similar_players_cache: Dict[str, List[Dict]] = {}
        self.chart_cache: Dict[str, Dict[str, str]] = {}
        self.clubs_cache: List[Dict[str, str]] = []
        self.positions_cache: List[str] = []
        
        # Filter States
        self.hub_filters = {
            'position': None,
            'club': None,
            'min_value': None,
            'max_value': None,
            'search_term': ''
        }
        self.scouting_state = {
            'position_group': 'Forward',
            'slider_values': {
                'xG/90': 75,
                'xA/90': 75,
                'xGI/90': 75,
                'recoveries': 75
            },
            'hard_filters': {
                'min_age': 0,
                'max_age': 40,
                'min_value': 0,
                'max_value': 1000000000,
                'contract_year': None
            },
            'search_results': [],
            'is_searching': False
        }
        self.watchlist_search = ''
        
        # Initialize data
        self._initialize_data()
    
    def _initialize_data(self):
        """Load initial data from CSV files"""
        data_dir = Path(__file__).parent / "data"
        
        try:
            # Load clubs
            clubs_path = data_dir / "clubs.csv"
            if clubs_path.exists():
                count = self.db.load_clubs_from_csv(str(clubs_path))
                print(f"Loaded {count} clubs")
            
            # Load players
            players_path = data_dir / "playersinfo.csv"
            if players_path.exists():
                count = self.db.load_players_from_csv(str(players_path))
                print(f"Loaded {count} players")
            
            # Load stats
            stats_path = data_dir / "playerstats.csv"
            if stats_path.exists():
                count = self.db.load_stats_from_csv(str(stats_path))
                print(f"Loaded {count} stat records")
            
            # Cache clubs and positions
            self._refresh_caches()
            
        except Exception as e:
            print(f"Error initializing data: {e}")
    
    def _refresh_caches(self):
        """Refresh cached data from database"""
        # Cache clubs
        clubs = self.db.get_all_clubs()
        self.clubs_cache = [{'club_id': c.club_id, 'club_name': c.club_name} for c in clubs]
        
        # Cache positions
        self.positions_cache = self.db.get_all_positions()
    
    def build(self):
        """Build initial page content"""
        self.page.title = "EPL SCOUT 25/26"
        self.page.bgcolor = COLORS['background']
        self.page.padding = 0
        self.page.window_width = 1280
        self.page.window_height = 800
        self.page.window_resizable = False
        
        return self.create_home_view()
    
    # ==================== VIEW CREATION ====================
    
    def create_home_view(self) -> ft.Container:
        """Create and return Home View"""
        self.current_view = "home"
        
        # Get counts
        player_count = len(self.positions_cache)  # Approximate
        club_count = len(self.clubs_cache)
        
        return ViewFactory.create_home_view(
            on_navigate_players=lambda e: self.navigate_to('players_hub'),
            on_navigate_scouting=lambda e: self.navigate_to('scouting'),
            on_navigate_watchlist=lambda e: self.navigate_to('watchlist'),
            player_count=player_count,
            club_count=club_count
        )
    
    def create_players_hub_view(self) -> ft.Container:
        """Create and return Players Hub View"""
        self.current_view = "players_hub"
        
        # Get filtered players
        players = self.db.get_players_for_hub(
            position_filter=self.hub_filters.get('position'),
            club_filter=self.hub_filters.get('club') if self.hub_filters.get('club') != 'All' else None,
            min_value=self.hub_filters.get('min_value'),
            max_value=self.hub_filters.get('max_value'),
            search_term=self.hub_filters.get('search_term') if self.hub_filters.get('search_term') else None
        )
        
        # Convert to dict format for view
        players_data = [
            {
                'player_id': p.player_id,
                'name': p.name,
                'position': p.position,
                'club_name': p.club_name,
                'market_value': p.market_value,
                'age': p.age
            }
            for p in players
        ]
        
        # Calculate pagination
        total_players = len(players_data)
        items_per_page = 25
        total_pages = max(1, (total_players + items_per_page - 1) // items_per_page)
        current_page = 1
        
        # Paginate
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_players = players_data[start_idx:end_idx]
        
        return ViewFactory.create_player_hub_view(
            clubs=self.clubs_cache,
            positions=['All'] + self.positions_cache,
            on_filter_change=lambda field, value: self.on_hub_filter_change(field, value),
            on_search=lambda term: self.on_hub_search(term),
            on_player_click=lambda pid: self.navigate_to_player(pid),
            on_reset_filters=lambda e: self.reset_hub_filters(),
            players=paginated_players,
            current_page=current_page,
            total_pages=total_pages,
            search_term=self.hub_filters.get('search_term', '')
        )
    
    def create_scouting_view(self) -> ft.Container:
        """Create and return Scouting View"""
        self.current_view = "scouting"
        
        return ViewFactory.create_scouting_view(
            positions=self.positions_cache,
            on_position_change=lambda pos: self.on_scouting_position_change(pos),
            on_slider_change=lambda stat, val: self.on_scouting_slider_change(stat, val),
            on_hard_filter_change=lambda field, val: self.on_scouting_hard_filter_change(field, val),
            on_search=lambda e: self.run_scouting_search(),
            on_player_click=lambda pid: self.navigate_to_player(pid),
            slider_values=self.scouting_state['slider_values'],
            search_results=self.scouting_state['search_results'],
            is_searching=self.scouting_state['is_searching']
        )
    
    def create_watchlist_view(self) -> ft.Container:
        """Create and return Watchlist View"""
        self.current_view = "watchlist"
        
        # Get watchlist data
        watchlist_data = self.db.get_watchlist()
        
        # Filter by search term
        if self.watchlist_search:
            watchlist_data = [
                item for item in watchlist_data
                if self.watchlist_search.lower() in item['player_name'].lower()
            ]
        
        return ViewFactory.create_watchlist_view(
            watchlist_data=watchlist_data,
            on_notes_change=lambda pid, notes: self.db.update_watchlist_notes(pid, notes),
            on_rating_change=lambda pid, rating: self.db.update_watchlist_rating(pid, rating),
            on_delete_player=lambda pid: self.remove_from_watchlist(pid),
            on_delete_all=lambda e: self.clear_watchlist(),
            on_navigate_hub=lambda e: self.navigate_to('players_hub'),
            on_player_click=lambda pid: self.navigate_to_player(pid),
            search_term=self.watchlist_search
        )
    
    def create_player_dashboard_view(self, player_id: str) -> ft.Container:
        """Create and return Player Dashboard View"""
        self.current_view = "player_dashboard"
        self.current_player_id = player_id
        
        # Get player info
        player_info = self.db.get_player_info(player_id)
        if not player_info:
            return self.create_error_view("Player not found")
        
        # Get club name
        club = self.db.get_club_by_id(player_info.club_id)
        club_name = club.club_name if club else "Unknown Club"
        
        # Get player stats
        stats_list = self.db.get_player_stats(player_id)
        
        # Aggregate season stats
        season_stats = self.algorithms.aggregate_player_stats(stats_list)
        
        # Convert gw records to dict format
        gw_records = [
            {
                'gw': s.gw,
                'minutes': s.minutes,
                'goals_scored': s.goals_scored,
                'assists': s.assists,
                'clean_sheets': s.clean_sheets,
                'expected_goals': s.expected_goals,
                'expected_assists': s.expected_assists,
                'ict_index': s.ict_index,
            }
            for s in stats_list
        ]
        
        # Get similar players (cached)
        similar_players = self.similar_players_cache.get(player_id, [])
        
        # Generate charts (placeholder for now)
        charts = self._generate_player_charts(player_id, stats_list, player_info.position)
        
        # Check if in watchlist
        is_in_watchlist = self.db.is_in_watchlist(player_id)
        
        # Convert player_info to dict
        player_dict = {
            'name': player_info.name,
            'position': player_info.position,
            'sub_position': player_info.sub_position,
            'country_of_citizenship': player_info.country_of_citizenship,
            'age': player_info.age,
            'contract_expiration_date': player_info.contract_expiration_date,
            'market_value_in_eur': player_info.market_value_in_eur,
            'image_url': player_info.image_url,
        }
        
        return ViewFactory.create_player_dashboard_view(
            player_info=player_dict,
            club_name=club_name,
            season_stats=season_stats,
            gw_records=gw_records,
            similar_players=similar_players,
            on_back=lambda e: self.navigate_back(),
            on_add_to_watchlist=lambda e: self.toggle_watchlist(player_id),
            on_find_similar=lambda e: self.show_similar_players(player_id),
            on_tab_change=lambda e: None,
            charts=charts,
            is_in_watchlist=is_in_watchlist
        )
    
    def create_error_view(self, message: str) -> ft.Container:
        """Create error view"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=100),
                ft.Icon("error_outline", size=80, color=COLORS['error']),
                ft.Container(height=20),
                ft.Text(message, size=18, color=COLORS['text_primary'], text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Go Home",
                    bgcolor=COLORS['primary'],
                    color='#000000',
                    on_click=lambda e: self.navigate_to('home')
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            expand=True
        )
    
    # ==================== EVENT HANDLERS ====================
    
    def on_hub_filter_change(self, field: str, value: any):
        """Handle filter changes in Players Hub"""
        if value == 'All' or value == '':
            self.hub_filters[field] = None
        else:
            try:
                if 'value' in field:
                    self.hub_filters[field] = float(value) * 1000000 if value else None
                else:
                    self.hub_filters[field] = value
            except:
                self.hub_filters[field] = value
        
        self.refresh_current_view()
    
    def on_hub_search(self, search_term: str):
        """Handle search in Players Hub (with debounce capability)"""
        self.hub_filters['search_term'] = search_term
        self.refresh_current_view()
    
    def reset_hub_filters(self):
        """Reset all hub filters"""
        self.hub_filters = {
            'position': None,
            'club': None,
            'min_value': None,
            'max_value': None,
            'search_term': ''
        }
        self.refresh_current_view()
    
    def on_scouting_position_change(self, position: str):
        """Handle position change in Scouting view"""
        self.scouting_state['position_group'] = position
    
    def on_scouting_slider_change(self, stat: str, value: float):
        """Handle slider change in Scouting view"""
        self.scouting_state['slider_values'][stat] = value
    
    def on_scouting_hard_filter_change(self, field: str, value: str):
        """Handle hard filter change in Scouting view"""
        try:
            if 'age' in field or 'year' in field:
                self.scouting_state['hard_filters'][field] = int(value) if value else None
            elif 'value' in field:
                self.scouting_state['hard_filters'][field] = float(value) * 1000000 if value else None
            else:
                self.scouting_state['hard_filters'][field] = value
        except:
            self.scouting_state['hard_filters'][field] = value
    
    def run_scouting_search(self):
        """Execute scouting search algorithm"""
        self.scouting_state['is_searching'] = True
        self.refresh_current_view()
        
        # Prepare data for algorithm
        all_players = []
        all_stats = []
        
        # In a real app, you'd fetch all players and aggregate their stats
        # For demo purposes, we'll use a simplified approach
        
        # Simulate search delay
        def do_search():
            time.sleep(0.5)  # Simulate processing
            
            # Get all players from DB (simplified)
            players = self.db.get_players_for_hub(min_minutes=0)
            all_players = [
                {
                    'player_id': p.player_id,
                    'name': p.name,
                    'position': p.position,
                    'club_name': p.club_name,
                    'market_value_in_eur': p.market_value,
                    'age': p.age,
                    'contract_expiration_date': '',
                }
                for p in players
            ]
            
            # Run algorithm
            results = self.algorithms.scout_players(
                all_players=all_players,
                all_stats=all_stats,
                position_group=self.scouting_state['position_group'],
                targets=self.scouting_state['slider_values'],
                age_range=(
                    self.scouting_state['hard_filters'].get('min_age', 0) or 0,
                    self.scouting_state['hard_filters'].get('max_age', 40) or 40
                ),
                value_range=(
                    self.scouting_state['hard_filters'].get('min_value', 0) or 0,
                    self.scouting_state['hard_filters'].get('max_value', 1000000000) or 1000000000
                ),
                contract_year=self.scouting_state['hard_filters'].get('contract_year')
            )
            
            self.scouting_state['search_results'] = [
                {
                    'player_id': r.player_id,
                    'player_name': r.player_name,
                    'club_name': r.club_name,
                    'position': r.position,
                    'match_score': r.match_score,
                    'age': r.age,
                    'market_value': r.market_value,
                    'contract_year': r.contract_year,
                }
                for r in results
            ]
            self.scouting_state['is_searching'] = False
            
            self.page.update()
        
        # Run in background
        self.page.run_task(do_search)
    
    def remove_from_watchlist(self, player_id: str):
        """Remove player from watchlist"""
        if self.db.remove_from_watchlist(player_id):
            self.page.snack_bar = create_snackbar_success("Player removed from watchlist")
            self.page.snack_bar.open = True
            self.refresh_current_view()
        else:
            self.page.snack_bar = create_snackbar_error("Failed to remove player")
            self.page.snack_bar.open = True
    
    def clear_watchlist(self):
        """Clear entire watchlist"""
        if self.db.clear_watchlist():
            self.page.snack_bar = create_snackbar_success("Watchlist cleared")
            self.page.snack_bar.open = True
            self.refresh_current_view()
        else:
            self.page.snack_bar = create_snackbar_error("Failed to clear watchlist")
            self.page.snack_bar.open = True
    
    def toggle_watchlist(self, player_id: str):
        """Add/remove player from watchlist"""
        if self.db.is_in_watchlist(player_id):
            self.remove_from_watchlist(player_id)
        else:
            if self.db.add_to_watchlist(player_id):
                self.page.snack_bar = create_snackbar_success("Added to watchlist")
                self.page.snack_bar.open = True
                self.refresh_current_view()
            else:
                self.page.snack_bar = create_snackbar_error("Failed to add to watchlist")
                self.page.snack_bar.open = True
    
    def show_similar_players(self, player_id: str):
        """Show similar players modal"""
        # Get from cache or calculate
        if player_id not in self.similar_players_cache:
            # Calculate similar players
            player_info = self.db.get_player_info(player_id)
            if player_info:
                # Simplified - in production would fetch all players and stats
                self.similar_players_cache[player_id] = []
        
        similar = self.similar_players_cache.get(player_id, [])
        
        if similar:
            modal = ViewFactory.create_similar_players_modal(
                player_name=player_info.name if player_info else "Player",
                similar_players=similar,
                on_close=lambda e: self.close_modal(),
                on_player_select=lambda pid: self.navigate_to_player(pid)
            )
            self.page.dialog = modal
            modal.open = True
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("No similar players found (need more data)", color=COLORS['text_primary']),
                bgcolor=COLORS['warning'],
                behavior=ft.SnackBarBehavior.FLOATING
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def close_modal(self):
        """Close current dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()
    
    def _generate_player_charts(self, player_id: str, stats: List[PlayerStats], position: str) -> Dict[str, str]:
        """Generate charts for player dashboard (placeholder implementation)"""
        # In production, this would use matplotlib to generate actual charts
        # For now, return empty dict to show placeholders
        return {}
    
    # ==================== NAVIGATION ====================
    
    def navigate_to(self, view_name: str):
        """Navigate to a view"""
        self.previous_view = self.current_view
        self.current_view = view_name
        
        view_map = {
            'home': self.create_home_view,
            'players_hub': self.create_players_hub_view,
            'scouting': self.create_scouting_view,
            'watchlist': self.create_watchlist_view,
        }
        
        if view_name in view_map:
            self.page.content = view_map[view_name]()
            self.page.update()
    
    def navigate_to_player(self, player_id: str):
        """Navigate to player dashboard"""
        self.previous_view = self.current_view
        self.page.content = self.create_player_dashboard_view(player_id)
        self.page.update()
    
    def navigate_back(self):
        """Navigate to previous view"""
        self.navigate_to(self.previous_view)
    
    def refresh_current_view(self):
        """Refresh current view"""
        view_map = {
            'home': self.create_home_view,
            'players_hub': self.create_players_hub_view,
            'scouting': self.create_scouting_view,
            'watchlist': self.create_watchlist_view,
            'player_dashboard': lambda: self.create_player_dashboard_view(self.current_player_id),
        }
        
        if self.current_view in view_map:
            self.page.content = view_map[self.current_view]()
            self.page.update()


def main(page: ft.Page):
    """Main entry point for Flet application"""
    app = EPLScoutApp(page)
    page.content = app.build()
    page.update()


if __name__ == "__main__":
    ft.run(target=main, view=ft.AppView.FLET_APP)
