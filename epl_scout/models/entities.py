"""
Models Layer - Pure Data Structures
No dependencies on UI or Database layers
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date


@dataclass
class Club:
    """Pure data structure for club information"""
    club_id: str
    club_name: str


@dataclass
class PlayerInfo:
    """Pure data structure for player基本信息"""
    player_id: str
    first_name: str
    last_name: str
    name: str
    last_season: int
    club_id: str
    player_code: str
    country_of_citizenship: str
    date_of_birth: str
    sub_position: str
    position: str
    foot: str
    height_in_cm: int
    contract_expiration_date: str
    image_url: str
    url: str
    current_club_name: str
    market_value_in_eur: int
    
    @property
    def age(self) -> int:
        """Calculate age from date_of_birth"""
        try:
            from datetime import datetime
            dob = datetime.strptime(self.date_of_birth, "%m/%d/%Y")
            today = datetime.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            return 0
    
    @property
    def full_name(self) -> str:
        return self.name


@dataclass
class PlayerStats:
    """Pure data structure for player statistics per gameweek"""
    player_id: str
    expected_goals: float
    expected_assists: float
    expected_goal_involvements: float
    expected_goals_conceded: float
    expected_goals_per_90: float
    expected_assists_per_90: float
    expected_goal_involvements_per_90: float
    expected_goals_conceded_per_90: float
    influence: float
    creativity: float
    threat: float
    ict_index: float
    gw: int
    first_name: str
    second_name: str
    name: str
    news: str
    news_added: str
    minutes: float
    goals_scored: float
    assists: float
    clean_sheets: float
    goals_conceded: float
    own_goals: float
    penalties_saved: float
    penalties_missed: float
    yellow_cards: float
    red_cards: float
    saves: float
    starts: float
    defensive_contribution: float
    saves_per_90: float
    clean_sheets_per_90: float
    goals_conceded_per_90: float
    starts_per_90: float
    defensive_contribution_per_90: float
    tackles: float
    clearances_blocks_interceptions: float
    recoveries: float


@dataclass
class WatchlistEntry:
    """Pure data structure for watchlist entry"""
    watchlist_id: int
    player_id: str
    rating: int
    notes: str
    created_at: str


@dataclass
class PlayerDashboardData:
    """Aggregated data for player dashboard view"""
    player_info: PlayerInfo
    club_name: str
    season_stats: Dict[str, Any]
    gw_records: List[PlayerStats]
    similar_players: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScoutingResult:
    """Result from scouting algorithm"""
    player_id: str
    player_name: str
    club_name: str
    position: str
    match_score: float
    age: int
    market_value: int
    contract_year: str


@dataclass
class PlayerHubItem:
    """Display item for player hub table"""
    player_id: str
    name: str
    position: str
    club_name: str
    market_value: int
    age: int
