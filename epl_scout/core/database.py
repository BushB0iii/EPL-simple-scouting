"""
Data Access Layer - Handles all database operations
Loose coupling: Only returns standard Python types or Pydantic/Dataclass objects
No UI dependencies, no direct SQL exposure to upper layers
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.entities import (
    Club, PlayerInfo, PlayerStats, 
    WatchlistEntry, ScoutingResult, PlayerHubItem
)


class DatabaseManager:
    """
    Singleton-like database manager
    Encapsulates all SQLite operations
    Returns only dataclasses or standard Python types
    """
    
    _instance = None
    _connection = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._connection is not None:
            return
            
        self.db_path = db_path or ":memory:"
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._enable_foreign_keys()
        self._create_tables()
    
    def _enable_foreign_keys(self):
        """Enable foreign key constraints"""
        self._connection.execute("PRAGMA foreign_keys = ON")
    
    def _create_tables(self):
        """Create database schema with proper normalization"""
        cursor = self._connection.cursor()
        
        # Clubs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                club_id VARCHAR(2) PRIMARY KEY,
                club_name VARCHAR(50) NOT NULL
            )
        """)
        
        # Players info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playersinfo (
                player_id VARCHAR(4) PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                name VARCHAR(100),
                last_season INTEGER,
                club_id VARCHAR(2),
                player_code VARCHAR(100),
                country_of_citizenship VARCHAR(50),
                date_of_birth DATE,
                sub_position VARCHAR(50),
                position VARCHAR(20),
                foot VARCHAR(10),
                height_in_cm INTEGER,
                contract_expiration_date DATE,
                image_url TEXT,
                url TEXT,
                current_club_name VARCHAR(100),
                market_value_in_eur INTEGER,
                FOREIGN KEY (club_id) REFERENCES clubs(club_id)
            )
        """)
        
        # Player stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playerstats (
                player_id VARCHAR(4),
                expected_goals REAL,
                expected_assists REAL,
                expected_goal_involvements REAL,
                expected_goals_conceded REAL,
                expected_goals_per_90 REAL,
                expected_assists_per_90 REAL,
                expected_goal_involvements_per_90 REAL,
                expected_goals_conceded_per_90 REAL,
                influence REAL,
                creativity REAL,
                threat REAL,
                ict_index REAL,
                gw INTEGER,
                first_name VARCHAR(50),
                second_name VARCHAR(50),
                name VARCHAR(100),
                news TEXT,
                news_added DATE,
                minutes REAL,
                goals_scored REAL,
                assists REAL,
                clean_sheets REAL,
                goals_conceded REAL,
                own_goals REAL,
                penalties_saved REAL,
                penalties_missed REAL,
                yellow_cards REAL,
                red_cards REAL,
                saves REAL,
                starts REAL,
                defensive_contribution REAL,
                saves_per_90 REAL,
                clean_sheets_per_90 REAL,
                goals_conceded_per_90 REAL,
                starts_per_90 REAL,
                defensive_contribution_per_90 REAL,
                tackles REAL,
                clearances_blocks_interceptions REAL,
                recoveries REAL,
                PRIMARY KEY (player_id, gw),
                FOREIGN KEY (player_id) REFERENCES playersinfo(player_id)
            )
        """)
        
        # Watchlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id VARCHAR(4) UNIQUE,
                rating INTEGER DEFAULT 0 CHECK(rating BETWEEN 1 AND 5),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES playersinfo(player_id)
            )
        """)
        
        self._connection.commit()
        cursor.close()
    
    def load_clubs_from_csv(self, csv_path: str) -> int:
        """Load clubs from CSV file, returns count of loaded records"""
        df = pd.read_csv(csv_path, sep='\t')
        cursor = self._connection.cursor()
        
        count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO clubs (club_id, club_name) VALUES (?, ?)",
                    (str(row['club_id']).zfill(2), row['club_name'])
                )
                count += 1
            except Exception as e:
                print(f"Error loading club: {e}")
        
        self._connection.commit()
        cursor.close()
        return count
    
    def load_players_from_csv(self, csv_path: str) -> int:
        """Load players from CSV file, returns count of loaded records"""
        df = pd.read_csv(csv_path, sep='\t')
        cursor = self._connection.cursor()
        
        count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO playersinfo 
                    (player_id, first_name, last_name, name, last_season, club_id, 
                     player_code, country_of_citizenship, date_of_birth, sub_position,
                     position, foot, height_in_cm, contract_expiration_date, 
                     image_url, url, current_club_name, market_value_in_eur)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['player_id']).zfill(4),
                    row.get('first_name', ''),
                    row.get('last_name', ''),
                    row.get('name', ''),
                    int(row.get('last_season', 0)),
                    str(row.get('club_id', '')).zfill(2),
                    row.get('player_code', ''),
                    row.get('country_of_citizenship', ''),
                    row.get('date_of_birth', ''),
                    row.get('sub_position', ''),
                    row.get('position', ''),
                    row.get('foot', ''),
                    int(row.get('height_in_cm', 0)),
                    row.get('contract_expiration_date', ''),
                    row.get('image_url', ''),
                    row.get('url', ''),
                    row.get('current_club_name', ''),
                    int(row.get('market_value_in_eur', 0))
                ))
                count += 1
            except Exception as e:
                print(f"Error loading player: {e}")
        
        self._connection.commit()
        cursor.close()
        return count
    
    def load_stats_from_csv(self, csv_path: str) -> int:
        """Load player stats from CSV file, returns count of loaded records"""
        df = pd.read_csv(csv_path)
        cursor = self._connection.cursor()
        
        count = 0
        for _, row in df.iterrows():
            try:
                # Build dynamic insert based on actual CSV columns
                columns = list(df.columns)
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)
                
                values = []
                for col in columns:
                    val = row.get(col)
                    if pd.isna(val):
                        values.append(None)
                    elif col == 'player_id' or col == 'gw':
                        values.append(str(val).zfill(4) if col == 'player_id' else int(val))
                    else:
                        try:
                            values.append(float(val))
                        except:
                            values.append(str(val) if val is not None else None)
                
                query = f"INSERT OR REPLACE INTO playerstats ({column_names}) VALUES ({placeholders})"
                cursor.execute(query, values)
                count += 1
            except Exception as e:
                print(f"Error loading stat: {e}")
        
        self._connection.commit()
        cursor.close()
        return count
    
    # ==================== QUERY METHODS ====================
    # All query methods return dataclasses or standard Python types
    # No raw SQL cursors exposed to upper layers
    
    def get_all_clubs(self) -> List[Club]:
        """Get all clubs as list of Club dataclass objects"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT club_id, club_name FROM clubs ORDER BY club_name")
        
        clubs = []
        for row in cursor.fetchall():
            clubs.append(Club(
                club_id=row['club_id'],
                club_name=row['club_name']
            ))
        cursor.close()
        return clubs
    
    def get_club_by_id(self, club_id: str) -> Optional[Club]:
        """Get single club by ID"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT club_id, club_name FROM clubs WHERE club_id = ?", (club_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return Club(club_id=row['club_id'], club_name=row['club_name'])
        return None
    
    def get_player_info(self, player_id: str) -> Optional[PlayerInfo]:
        """Get player info by ID"""
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT * FROM playersinfo WHERE player_id = ?
        """, (player_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return PlayerInfo(
                player_id=row['player_id'],
                first_name=row['first_name'] or '',
                last_name=row['last_name'] or '',
                name=row['name'] or '',
                last_season=row['last_season'] or 0,
                club_id=row['club_id'] or '',
                player_code=row['player_code'] or '',
                country_of_citizenship=row['country_of_citizenship'] or '',
                date_of_birth=row['date_of_birth'] or '',
                sub_position=row['sub_position'] or '',
                position=row['position'] or '',
                foot=row['foot'] or '',
                height_in_cm=row['height_in_cm'] or 0,
                contract_expiration_date=row['contract_expiration_date'] or '',
                image_url=row['image_url'] or '',
                url=row['url'] or '',
                current_club_name=row['current_club_name'] or '',
                market_value_in_eur=row['market_value_in_eur'] or 0
            )
        return None
    
    def get_players_for_hub(
        self, 
        position_filter: Optional[str] = None,
        club_filter: Optional[str] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        search_term: Optional[str] = None,
        min_minutes: int = 450
    ) -> List[PlayerHubItem]:
        """Get filtered players for hub view"""
        cursor = self._connection.cursor()
        
        # Build dynamic query with filters
        query = """
            SELECT 
                p.player_id, p.name, p.position, c.club_name, 
                p.market_value_in_eur, p.date_of_birth
            FROM playersinfo p
            LEFT JOIN clubs c ON p.club_id = c.club_id
            WHERE 1=1
        """
        params = []
        
        if position_filter:
            query += " AND p.position = ?"
            params.append(position_filter)
        
        if club_filter:
            query += " AND p.club_id = ?"
            params.append(club_filter)
        
        if min_value is not None:
            query += " AND p.market_value_in_eur >= ?"
            params.append(min_value)
        
        if max_value is not None:
            query += " AND p.market_value_in_eur <= ?"
            params.append(max_value)
        
        if search_term:
            query += " AND (p.name LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Filter by minimum minutes using subquery
        query += f"""
            AND p.player_id IN (
                SELECT player_id FROM playerstats 
                GROUP BY player_id 
                HAVING SUM(minutes) >= {min_minutes}
            )
        """
        
        query += " ORDER BY p.name"
        
        cursor.execute(query, params)
        
        players = []
        for row in cursor.fetchall():
            # Calculate age
            age = 0
            if row['date_of_birth']:
                try:
                    from datetime import datetime
                    dob = datetime.strptime(row['date_of_birth'], "%m/%d/%Y")
                    today = datetime.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                except:
                    pass
            
            players.append(PlayerHubItem(
                player_id=row['player_id'],
                name=row['name'] or '',
                position=row['position'] or '',
                club_name=row['club_name'] or 'Unknown',
                market_value=row['market_value_in_eur'] or 0,
                age=age
            ))
        
        cursor.close()
        return players
    
    def get_player_stats(self, player_id: str) -> List[PlayerStats]:
        """Get all gameweek stats for a player"""
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT * FROM playerstats WHERE player_id = ? ORDER BY gw
        """, (player_id,))
        
        stats = []
        for row in cursor.fetchall():
            stats.append(PlayerStats(
                player_id=row['player_id'],
                expected_goals=row['expected_goals'] or 0,
                expected_assists=row['expected_assists'] or 0,
                expected_goal_involvements=row['expected_goal_involvements'] or 0,
                expected_goals_conceded=row['expected_goals_conceded'] or 0,
                expected_goals_per_90=row['expected_goals_per_90'] or 0,
                expected_assists_per_90=row['expected_assists_per_90'] or 0,
                expected_goal_involvements_per_90=row['expected_goal_involvements_per_90'] or 0,
                expected_goals_conceded_per_90=row['expected_goals_conceded_per_90'] or 0,
                influence=row['influence'] or 0,
                creativity=row['creativity'] or 0,
                threat=row['threat'] or 0,
                ict_index=row['ict_index'] or 0,
                gw=row['gw'] or 0,
                first_name=row['first_name'] or '',
                second_name=row['second_name'] or '',
                name=row['name'] or '',
                news=row['news'] or '',
                news_added=row['news_added'] or '',
                minutes=row['minutes'] or 0,
                goals_scored=row['goals_scored'] or 0,
                assists=row['assists'] or 0,
                clean_sheets=row['clean_sheets'] or 0,
                goals_conceded=row['goals_conceded'] or 0,
                own_goals=row['own_goals'] or 0,
                penalties_saved=row['penalties_saved'] or 0,
                penalties_missed=row['penalties_missed'] or 0,
                yellow_cards=row['yellow_cards'] or 0,
                red_cards=row['red_cards'] or 0,
                saves=row['saves'] or 0,
                starts=row['starts'] or 0,
                defensive_contribution=row['defensive_contribution'] or 0,
                saves_per_90=row['saves_per_90'] or 0,
                clean_sheets_per_90=row['clean_sheets_per_90'] or 0,
                goals_conceded_per_90=row['goals_conceded_per_90'] or 0,
                starts_per_90=row['starts_per_90'] or 0,
                defensive_contribution_per_90=row['defensive_contribution_per_90'] or 0,
                tackles=row['tackles'] or 0,
                clearances_blocks_interceptions=row['clearances_blocks_interceptions'] or 0,
                recoveries=row['recoveries'] or 0
            ))
        
        cursor.close()
        return stats
    
    def get_all_positions(self) -> List[str]:
        """Get unique positions from database"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT DISTINCT position FROM playersinfo WHERE position != '' ORDER BY position")
        positions = [row['position'] for row in cursor.fetchall()]
        cursor.close()
        return positions
    
    # ==================== WATCHLIST METHODS ====================
    
    def add_to_watchlist(self, player_id: str, rating: int = 0, notes: str = "") -> bool:
        """Add player to watchlist"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist (player_id, rating, notes)
                VALUES (?, ?, ?)
            """, (player_id, rating, notes))
            self._connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, player_id: str) -> bool:
        """Remove player from watchlist"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM watchlist WHERE player_id = ?", (player_id,))
            self._connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False
    
    def update_watchlist_notes(self, player_id: str, notes: str) -> bool:
        """Update notes for a watchlist entry"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("UPDATE watchlist SET notes = ? WHERE player_id = ?", (notes, player_id))
            self._connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error updating notes: {e}")
            return False
    
    def update_watchlist_rating(self, player_id: str, rating: int) -> bool:
        """Update rating for a watchlist entry"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("UPDATE watchlist SET rating = ? WHERE player_id = ?", (rating, player_id))
            self._connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get full watchlist with player details"""
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT 
                w.watchlist_id, w.player_id, w.rating, w.notes, w.created_at,
                p.name, p.position, c.club_name
            FROM watchlist w
            JOIN playersinfo p ON w.player_id = p.player_id
            LEFT JOIN clubs c ON p.club_id = c.club_id
            ORDER BY w.created_at DESC
        """)
        
        watchlist = []
        for row in cursor.fetchall():
            watchlist.append({
                'watchlist_id': row['watchlist_id'],
                'player_id': row['player_id'],
                'rating': row['rating'],
                'notes': row['notes'] or '',
                'created_at': row['created_at'],
                'player_name': row['name'],
                'position': row['position'],
                'club_name': row['club_name'] or 'Unknown'
            })
        
        cursor.close()
        return watchlist
    
    def is_in_watchlist(self, player_id: str) -> bool:
        """Check if player is in watchlist"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE player_id = ?", (player_id,))
        result = cursor.fetchone() is not None
        cursor.close()
        return result
    
    def clear_watchlist(self) -> bool:
        """Clear entire watchlist"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM watchlist")
            self._connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error clearing watchlist: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
