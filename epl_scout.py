"""
EPL SCOUT 25/26 - Desktop Application
Python + Flet (Material Design 3)
"""

import flet as ft
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from io import BytesIO
import base64
from datetime import datetime, date
import os
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

# Color Scheme
COLORS = {
    "background": "#1A1A1A",
    "surface": "#2D2D2D",
    "primary": "#FFD700",
    "secondary": "#4A4A4A",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "success": "#4CAF50",
    "error": "#F44336",
    "warning": "#FF9800",
}

# Position groups mapping
POSITION_GROUPS = {
    "GK": ["Goalkeeper"],
    "DEF": ["Centre-Back", "Left-Back", "Right-Back", "Defensive Midfield"],
    "MID": ["Central Midfield", "Attacking Midfield", "Left Winger", "Right Winger", "Left Midfield", "Right Midfield"],
    "FWD": ["Centre-Forward", "Second Striker", "Left Winger", "Right Winger"],
}

# Stats by position for radar chart
RADAR_STATS = {
    "GK": ["saves_per_90", "clean_sheets_per_90", "penalties_saved", "goals_conceded_per_90", "expected_goals_conceded_per_90"],
    "DEF": ["tackles", "clearances_blocks_interceptions", "defensive_contribution_per_90", "expected_goals_conceded_per_90", "influence"],
    "MID": ["creativity", "expected_assists_per_90", "recoveries", "expected_goal_involvements_per_90", "ict_index"],
    "FWD": ["expected_goals_per_90", "goals_scored", "threat", "expected_goal_involvements_per_90", "ict_index"],
}

# Season stats by position
SEASON_STATS = {
    "GK": [
        ("saves", "Saves"), ("goals_conceded", "Goals Conceded"), ("clean_sheets", "Clean Sheets"),
        ("penalties_saved", "Penalties Saved"), ("saves_per_90", "Saves/90"), ("goals_conceded_per_90", "GC/90"),
        ("clean_sheets_per_90", "CS/90"), ("expected_goals_conceded", "xGC"), ("expected_goals_conceded_per_90", "xGC/90"),
        ("minutes", "Minutes"), ("starts", "Starts"), ("ict_index", "ICT Index")
    ],
    "DEF": [
        ("tackles", "Tackles"), ("clearances_blocks_interceptions", "Clearances/Blocks/Interceptions"),
        ("defensive_contribution", "Defensive Contribution"), ("expected_goals_conceded", "xGC"),
        ("expected_goals_conceded_per_90", "xGC/90"), ("influence", "Influence"), ("creativity", "Creativity"),
        ("threat", "Threat"), ("ict_index", "ICT Index"), ("minutes", "Minutes"), ("starts", "Starts"),
        ("goals_scored", "Goals"), ("assists", "Assists"), ("yellow_cards", "Yellow Cards")
    ],
    "MID": [
        ("goals_scored", "Goals"), ("assists", "Assists"), ("expected_goals", "xG"), ("expected_assists", "xA"),
        ("expected_goal_involvements", "xGI"), ("tackles", "Tackles"), ("recoveries", "Recoveries"),
        ("clearances_blocks_interceptions", "Clearances/Blocks/Interceptions"), ("defensive_contribution", "Defensive Contribution"),
        ("threat", "Threat"), ("creativity", "Creativity"), ("influence", "Influence"), ("ict_index", "ICT Index"),
        ("minutes", "Minutes"), ("starts", "Starts"), ("yellow_cards", "Yellow Cards")
    ],
    "FWD": [
        ("goals_scored", "Goals"), ("assists", "Assists"), ("expected_goals", "xG"), ("expected_assists", "xA"),
        ("expected_goal_involvements", "xGI"), ("threat", "Threat"), ("ict_index", "ICT Index"), ("influence", "Influence"),
        ("creativity", "Creativity"), ("minutes", "Minutes"), ("starts", "Starts"), ("yellow_cards", "Yellow Cards")
    ],
}


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "epl_scout.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def close(self):
        if self.conn:
            self.conn.close()
            
    def create_tables(self):
        """Create database tables according to schema"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clubs (
                club_id VARCHAR(2) PRIMARY KEY,
                club_name VARCHAR(50) NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playersinfo (
                player_id VARCHAR(4) PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                name VARCHAR(100),
                last_season INTEGER,
                club_id VARCHAR(2),
                country_of_citizenship VARCHAR(50),
                date_of_birth DATE,
                sub_position VARCHAR(50),
                position VARCHAR(20),
                foot VARCHAR(10),
                height_in_cm INTEGER,
                contract_expiration_date DATE,
                image_url TEXT,
                current_club_name VARCHAR(100),
                market_value_in_eur INTEGER,
                FOREIGN KEY (club_id) REFERENCES clubs(club_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playerstats (
                player_id VARCHAR(4),
                gw INTEGER,
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
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id VARCHAR(4) UNIQUE,
                rating INTEGER DEFAULT 0 CHECK(rating BETWEEN 1 AND 5),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES playersinfo(player_id)
            )
        ''')
        
        self.conn.commit()
        
    def load_csv_to_table(self, csv_path: str, table_name: str, columns: List[str]):
        """Load CSV data into a table"""
        if not os.path.exists(csv_path):
            return False
            
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            placeholders = ",".join(["?" for _ in columns])
            values = [row.get(col, None) for col in columns]
            
            # Handle duplicates with REPLACE
            if table_name == "clubs":
                self.cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", values)
            elif table_name == "playersinfo":
                self.cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", values)
            elif table_name == "playerstats":
                self.cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", values)
                
        self.conn.commit()
        return True


class DataProcessor:
    """Handles data processing and calculations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.clubs_df: Optional[pd.DataFrame] = None
        self.players_df: Optional[pd.DataFrame] = None
        self.league_percentiles: Dict[str, Dict[str, float]] = {}
        self.similar_players_cache: Dict[str, List[Dict]] = {}
        self.charts_cache: Dict[str, Dict[str, str]] = {}
        
    def load_data(self, clubs_csv: str, players_csv: str, stats_csv: str):
        """Load CSV files into memory and SQLite"""
        # Load clubs and players into memory
        if os.path.exists(clubs_csv):
            self.clubs_df = pd.read_csv(clubs_csv)
            self.db.load_csv_to_table(clubs_csv, "clubs", ["club_id", "club_name"])
            
        if os.path.exists(players_csv):
            self.players_df = pd.read_csv(players_csv)
            columns = ["player_id", "first_name", "last_name", "name", "last_season", "club_id",
                      "country_of_citizenship", "date_of_birth", "sub_position", "position",
                      "foot", "height_in_cm", "contract_expiration_date", "image_url",
                      "current_club_name", "market_value_in_eur"]
            self.db.load_csv_to_table(players_csv, "playersinfo", columns)
            
        # Load playerstats into SQLite only
        if os.path.exists(stats_csv):
            columns = ["player_id", "gw", "expected_goals", "expected_assists", "expected_goal_involvements",
                      "expected_goals_conceded", "expected_goals_per_90", "expected_assists_per_90",
                      "expected_goal_involvements_per_90", "expected_goals_conceded_per_90",
                      "influence", "creativity", "threat", "ict_index", "news", "news_added",
                      "minutes", "goals_scored", "assists", "clean_sheets", "goals_conceded",
                      "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", "red_cards",
                      "saves", "starts", "defensive_contribution", "saves_per_90", "clean_sheets_per_90",
                      "goals_conceded_per_90", "starts_per_90", "defensive_contribution_per_90",
                      "tackles", "clearances_blocks_interceptions", "recoveries"]
            self.db.load_csv_to_table(stats_csv, "playerstats", columns)
            
        # Refresh data from DB
        self.refresh_dataframes()
        
    def refresh_dataframes(self):
        """Refresh DataFrames from database"""
        self.clubs_df = pd.read_sql_query("SELECT * FROM clubs", self.db.conn)
        self.players_df = pd.read_sql_query("SELECT * FROM playersinfo", self.db.conn)
        
    def calculate_league_percentiles(self):
        """Pre-calculate league percentiles for per_90 stats and indices"""
        query = """
            SELECT ps.*, pi.position 
            FROM playerstats ps 
            JOIN playersinfo pi ON ps.player_id = pi.player_id
            WHERE ps.minutes >= 450
        """
        stats_df = pd.read_sql_query(query, self.db.conn)
        
        if stats_df.empty:
            return
            
        # Calculate total season stats per player
        per_90_cols = [
            "expected_goals_per_90", "expected_assists_per_90", "expected_goal_involvements_per_90",
            "expected_goals_conceded_per_90", "saves_per_90", "clean_sheets_per_90",
            "goals_conceded_per_90", "starts_per_90", "defensive_contribution_per_90"
        ]
        
        index_cols = ["influence", "creativity", "threat", "ict_index"]
        
        # Aggregate per player
        player_totals = stats_df.groupby("player_id").agg({
            **{col: "sum" for col in ["minutes", "goals_scored", "assists", "tackles", 
                                      "clearances_blocks_interceptions", "recoveries"]},
            **{col: "mean" for col in per_90_cols + index_cols}
        }).reset_index()
        
        # Merge with position info
        player_totals = player_totals.merge(
            self.players_df[["player_id", "position"]], on="player_id"
        )
        
        # Calculate percentiles by position group
        for pos_group, positions in POSITION_GROUPS.items():
            mask = player_totals["position"].isin(positions)
            pos_data = player_totals[mask]
            
            if pos_data.empty:
                continue
                
            self.league_percentiles[pos_group] = {}
            
            for col in per_90_cols + index_cols:
                if col in pos_data.columns:
                    for percentile in [50, 75, 90, 95]:
                        key = f"{col}_{percentile}"
                        self.league_percentiles[pos_group][key] = pos_data[col].quantile(percentile / 100)
                        
    def get_position_group(self, position: str) -> str:
        """Get position group from position name"""
        for group, positions in POSITION_GROUPS.items():
            if position in positions:
                return group
        return "MID"  # Default
        
    def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Get aggregated stats for a player"""
        query = """
            SELECT ps.*, pi.position, pi.name, pi.club_id, pi.market_value_in_eur,
                   pi.country_of_citizenship, pi.date_of_birth, pi.contract_expiration_date,
                   pi.image_url, pi.current_club_name, c.club_name
            FROM playerstats ps
            JOIN playersinfo pi ON ps.player_id = pi.player_id
            LEFT JOIN clubs c ON pi.club_id = c.club_id
            WHERE ps.player_id = ?
        """
        stats_df = pd.read_sql_query(query, self.db.conn, params=(player_id,))
        
        if stats_df.empty:
            return None
            
        # Aggregate stats
        agg = {
            "player_id": player_id,
            "name": stats_df["name"].iloc[0],
            "position": stats_df["position"].iloc[0],
            "club_name": stats_df["club_name"].iloc[0] if "club_name" in stats_df.columns else "",
            "minutes": stats_df["minutes"].sum(),
            "goals_scored": stats_df["goals_scored"].sum(),
            "assists": stats_df["assists"].sum(),
            "clean_sheets": stats_df["clean_sheets"].sum(),
            "tackles": stats_df["tackles"].sum(),
            "clearances_blocks_interceptions": stats_df["clearances_blocks_interceptions"].sum(),
            "recoveries": stats_df["recoveries"].sum(),
            "yellow_cards": stats_df["yellow_cards"].sum(),
            "red_cards": stats_df["red_cards"].sum(),
            "saves": stats_df["saves"].sum(),
            "starts": stats_df["starts"].sum(),
            "expected_goals": stats_df["expected_goals"].sum(),
            "expected_assists": stats_df["expected_assists"].sum(),
            "expected_goal_involvements": stats_df["expected_goal_involvements"].sum(),
            "expected_goals_conceded": stats_df["expected_goals_conceded"].sum(),
            "influence": stats_df["influence"].mean(),
            "creativity": stats_df["creativity"].mean(),
            "threat": stats_df["threat"].mean(),
            "ict_index": stats_df["ict_index"].mean(),
        }
        
        # Per 90 stats
        if agg["minutes"] > 0:
            agg["goals_per_90"] = agg["goals_scored"] / agg["minutes"] * 90
            agg["assists_per_90"] = agg["assists"] / agg["minutes"] * 90
            agg["expected_goals_per_90"] = stats_df["expected_goals_per_90"].mean()
            agg["expected_assists_per_90"] = stats_df["expected_assists_per_90"].mean()
            agg["expected_goal_involvements_per_90"] = stats_df["expected_goal_involvements_per_90"].mean()
            agg["defensive_contribution_per_90"] = stats_df["defensive_contribution_per_90"].mean()
            
        return agg
        
    def get_gw_records(self, player_id: str) -> pd.DataFrame:
        """Get gameweek records for a player"""
        query = """
            SELECT * FROM playerstats 
            WHERE player_id = ? 
            ORDER BY gw
        """
        return pd.read_sql_query(query, self.db.conn, params=(player_id,))
        
    def find_similar_players(self, player_id: str, top_n: int = 5) -> List[Dict]:
        """Find similar players using cosine similarity"""
        # Check cache
        if player_id in self.similar_players_cache:
            return self.similar_players_cache[player_id]
            
        # Get target player info
        player_info = self.players_df[self.players_df["player_id"] == player_id]
        if player_info.empty:
            return []
            
        position = player_info["position"].iloc[0]
        pos_group = self.get_position_group(position)
        
        # Get all players in same position group with sufficient minutes
        query = """
            SELECT ps.player_id, pi.name, pi.position, pi.current_club_name,
                   SUM(ps.minutes) as total_minutes
            FROM playerstats ps
            JOIN playersinfo pi ON ps.player_id = pi.player_id
            WHERE pi.position IN ({})
            GROUP BY ps.player_id
            HAVING total_minutes >= 450
        """.format(",".join(["?" for _ in POSITION_GROUPS[pos_group]]))
        
        candidates = pd.read_sql_query(query, self.db.conn, 
                                       params=POSITION_GROUPS[pos_group])
        
        if len(candidates) < 2:
            return []
            
        # Define features based on position group
        if pos_group == "GK":
            features = ["saves_per_90", "clean_sheets_per_90", "expected_goals_conceded_per_90"]
        elif pos_group == "DEF":
            features = ["tackles", "clearances_blocks_interceptions", "defensive_contribution_per_90", "influence"]
        elif pos_group == "MID":
            features = ["creativity", "expected_assists_per_90", "recoveries", "ict_index"]
        else:  # FWD
            features = ["expected_goals_per_90", "threat", "ict_index", "goals_scored"]
            
        # Get feature values for all candidates
        feature_query = """
            SELECT ps.player_id,
                   AVG(ps.{}) as avg_{}
            FROM playerstats ps
            WHERE ps.player_id IN ({})
            GROUP BY ps.player_id
        """
        
        candidate_ids = candidates["player_id"].tolist()
        placeholders = ",".join(["?" for _ in candidate_ids])
        
        feature_cols = []
        for f in features:
            feature_cols.append(f"AVG(ps.{f}) as {f}")
            
        feature_query = f"""
            SELECT ps.player_id, {','.join(feature_cols)}
            FROM playerstats ps
            WHERE ps.player_id IN ({placeholders})
            GROUP BY ps.player_id
        """
        
        feature_df = pd.read_sql_query(feature_query, self.db.conn, params=candidate_ids)
        
        if feature_df.empty or not all(f in feature_df.columns for f in features):
            return []
            
        # Calculate Z-scores
        feature_matrix = feature_df[features].values
        mean = np.mean(feature_matrix, axis=0)
        std = np.std(feature_matrix, axis=0) + 1e-8
        normalized = (feature_matrix - mean) / std
        
        # Get target player features
        target_row = feature_df[feature_df["player_id"] == player_id]
        if target_row.empty:
            return []
            
        target_features = target_row[features].values[0]
        target_normalized = (target_features - mean) / std
        
        # Calculate cosine similarity
        similarities = []
        for i, row in feature_df.iterrows():
            if row["player_id"] == player_id:
                continue
                
            idx = feature_df.index.get_loc(i)
            sim = np.dot(target_normalized, normalized[idx]) / (
                np.linalg.norm(target_normalized) * np.linalg.norm(normalized[idx]) + 1e-8
            )
            score = ((sim + 1) / 2) * 100
            
            similarities.append({
                "player_id": row["player_id"],
                "name": row.get("name", ""),
                "club": "",  # Will be filled later
                "score": round(score, 1)
            })
            
        # Sort by score and get top N
        similarities.sort(key=lambda x: x["score"], reverse=True)
        result = similarities[:top_n]
        
        # Cache result
        self.similar_players_cache[player_id] = result
        
        return result
        
    def scout_players(self, position_group: str, sliders: Dict[str, float],
                     age_range: tuple = None, market_value_range: tuple = None,
                     contract_year: int = None) -> List[Dict]:
        """Find players matching scouting criteria"""
        positions = POSITION_GROUPS.get(position_group, POSITION_GROUPS["MID"])
        placeholders = ",".join(["?" for _ in positions])
        
        # Get players with stats
        query = f"""
            SELECT ps.player_id, pi.name, pi.position, pi.current_club_name,
                   pi.market_value_in_eur, pi.date_of_birth, pi.contract_expiration_date,
                   SUM(ps.minutes) as total_minutes,
                   AVG(ps.expected_goals_per_90) as xG_per_90,
                   AVG(ps.expected_assists_per_90) as xA_per_90,
                   AVG(ps.expected_goal_involvements_per_90) as xGI_per_90,
                   AVG(ps.recoveries) as recoveries_avg
            FROM playerstats ps
            JOIN playersinfo pi ON ps.player_id = pi.player_id
            WHERE pi.position IN ({placeholders})
            GROUP BY ps.player_id
            HAVING total_minutes >= 450
        """
        
        players = pd.read_sql_query(query, self.db.conn, params=positions)
        
        if players.empty:
            return []
            
        # Calculate match scores
        results = []
        percentile_cols = ["xG_per_90", "xA_per_90", "xGI_per_90"]
        
        for _, row in players.iterrows():
            scores = []
            
            for col in percentile_cols:
                if col in sliders and col in row:
                    slider_val = sliders[col]
                    player_val = row[col] if pd.notna(row[col]) else 50
                    
                    # Simple scoring based on difference from target
                    score = 100 - abs(player_val - slider_val)
                    scores.append(max(0, score))
                    
            if scores:
                match_score = np.mean(scores)
            else:
                match_score = 50
                
            # Apply hard filters
            if age_range:
                # Calculate age from birth date
                if pd.notna(row.get("date_of_birth")):
                    try:
                        birth = pd.to_datetime(row["date_of_birth"])
                        age = (datetime.now() - birth).days // 365
                        if not (age_range[0] <= age <= age_range[1]):
                            continue
                    except:
                        pass
                        
            if market_value_range:
                mv = row.get("market_value_in_eur", 0)
                if pd.isna(mv) or not (market_value_range[0] <= mv <= market_value_range[1]):
                    continue
                    
            if contract_year and pd.notna(row.get("contract_expiration_date")):
                try:
                    contract = pd.to_datetime(row["contract_expiration_date"])
                    if contract.year != contract_year:
                        continue
                except:
                    pass
                    
            results.append({
                "player_id": row["player_id"],
                "name": row["name"],
                "club": row.get("current_club_name", ""),
                "position": row["position"],
                "match_score": round(match_score, 1),
                "market_value": row.get("market_value_in_eur", 0),
            })
            
        # Sort by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        return results
        
    def render_chart_to_base64(self, fig: Figure) -> str:
        """Render matplotlib figure to base64 string"""
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor="#1A1A1A")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return f"data:image/png;base64,{img_base64}"
        
    def create_radar_chart(self, player_id: str, stats: Dict) -> str:
        """Create performance radar chart"""
        if player_id in self.charts_cache and "radar" in self.charts_cache[player_id]:
            return self.charts_cache[player_id]["radar"]
            
        position = stats.get("position", "MID")
        pos_group = self.get_position_group(position)
        
        # Get appropriate stats for position
        stat_mapping = {
            "saves_per_90": stats.get("saves_per_90", 0),
            "clean_sheets_per_90": stats.get("clean_sheets_per_90", 0),
            "penalties_saved": stats.get("penalties_saved", 0),
            "goals_conceded_per_90": stats.get("goals_conceded_per_90", 0),
            "expected_goals_conceded_per_90": stats.get("expected_goals_conceded_per_90", 0),
            "tackles": stats.get("tackles", 0),
            "clearances_blocks_interceptions": stats.get("clearances_blocks_interceptions", 0),
            "defensive_contribution_per_90": stats.get("defensive_contribution_per_90", 0),
            "influence": stats.get("influence", 0),
            "creativity": stats.get("creativity", 0),
            "expected_assists_per_90": stats.get("expected_assists_per_90", 0),
            "recoveries": stats.get("recoveries", 0),
            "expected_goal_involvements_per_90": stats.get("expected_goal_involvements_per_90", 0),
            "ict_index": stats.get("ict_index", 0),
            "expected_goals_per_90": stats.get("expected_goals_per_90", 0),
            "goals_scored": stats.get("goals_scored", 0),
            "threat": stats.get("threat", 0),
        }
        
        labels = RADAR_STATS.get(pos_group, RADAR_STATS["MID"])
        values = [stat_mapping.get(label, 0) for label in labels]
        
        # Normalize values for radar chart
        max_vals = {
            "saves_per_90": 5, "clean_sheets_per_90": 0.5, "penalties_saved": 5,
            "goals_conceded_per_90": 2, "expected_goals_conceded_per_90": 2,
            "tackles": 100, "clearances_blocks_interceptions": 150, "defensive_contribution_per_90": 15,
            "influence": 150, "creativity": 100, "expected_assists_per_90": 0.5,
            "recoveries": 100, "expected_goal_involvements_per_90": 0.8,
            "ict_index": 200, "expected_goals_per_90": 0.8, "goals_scored": 30, "threat": 150
        }
        
        normalized_values = [min(v / max_vals.get(l, 1), 1) * 100 for v, l in zip(values, labels)]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        normalized_values += normalized_values[:1]
        labels = list(labels) + [labels[0]]
        
        ax.plot(angles, normalized_values, color=COLORS["primary"], linewidth=2)
        ax.fill(angles, normalized_values, color=COLORS["primary"], alpha=0.25)
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels[:-1], color=COLORS["text_primary"], size=9)
        ax.set_facecolor(COLORS["background"])
        ax.spines["polar"].set_color(COLORS["secondary"])
        
        chart_data = self.render_chart_to_base64(fig)
        
        if player_id not in self.charts_cache:
            self.charts_cache[player_id] = {}
        self.charts_cache[player_id]["radar"] = chart_data
        
        return chart_data
        
    def create_gw_charts(self, player_id: str, gw_df: pd.DataFrame) -> Dict[str, str]:
        """Create gameweek performance charts"""
        if player_id in self.charts_cache and "gw_charts" in self.charts_cache[player_id]:
            return self.charts_cache[player_id]["gw_charts"]
            
        charts = {}
        
        if gw_df.empty:
            return charts
            
        # Chart 1: Minutes per GW
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        gw_nums = gw_df["gw"].tolist()
        minutes = gw_df["minutes"].tolist()
        goals = gw_df["goals_scored"].tolist()
        assists = gw_df["assists"].tolist()
        
        bars = ax1.bar(gw_nums, minutes, color=COLORS["primary"], alpha=0.7)
        ax1.set_xlabel("Gameweek", color=COLORS["text_primary"])
        ax1.set_ylabel("Minutes", color=COLORS["text_primary"])
        ax1.set_facecolor(COLORS["background"])
        ax1.tick_params(colors=COLORS["text_secondary"])
        
        # Add goals/assists labels
        for i, (g, a) in enumerate(zip(goals, assists)):
            if g > 0 or a > 0:
                label = ""
                if g > 0:
                    label += f"G:{int(g)} "
                if a > 0:
                    label += f"A:{int(a)}"
                ax1.text(gw_nums[i], minutes[i], label.strip(), ha="center", va="bottom", 
                        color=COLORS["text_primary"], fontsize=8)
                        
        charts["minutes"] = self.render_chart_to_base64(fig1)
        
        # Chart 2: Goals vs Expected Goals (Cumulative)
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        gw_df_sorted = gw_df.sort_values("gw")
        cumulative_goals = gw_df_sorted["goals_scored"].cumsum()
        cumulative_xg = gw_df_sorted["expected_goals"].cumsum()
        
        ax2.plot(gw_df_sorted["gw"], cumulative_goals, color=COLORS["primary"], 
                label="Actual Goals", linewidth=2, marker="o")
        ax2.plot(gw_df_sorted["gw"], cumulative_xg, color=COLORS["success"], 
                label="Expected Goals", linewidth=2, marker="s")
        ax2.set_xlabel("Gameweek", color=COLORS["text_primary"])
        ax2.set_ylabel("Cumulative", color=COLORS["text_primary"])
        ax2.legend(facecolor=COLORS["surface"], labelcolor=COLORS["text_primary"])
        ax2.set_facecolor(COLORS["background"])
        ax2.tick_params(colors=COLORS["text_secondary"])
        
        charts["goals_vs_xg"] = self.render_chart_to_base64(fig2)
        
        # Chart 3: Assists vs Expected Assists (Cumulative)
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        cumulative_assists = gw_df_sorted["assists"].cumsum()
        cumulative_xa = gw_df_sorted["expected_assists"].cumsum()
        
        ax3.plot(gw_df_sorted["gw"], cumulative_assists, color=COLORS["primary"], 
                label="Actual Assists", linewidth=2, marker="o")
        ax3.plot(gw_df_sorted["gw"], cumulative_xa, color=COLORS["warning"], 
                label="Expected Assists", linewidth=2, marker="s")
        ax3.set_xlabel("Gameweek", color=COLORS["text_primary"])
        ax3.set_ylabel("Cumulative", color=COLORS["text_primary"])
        ax3.legend(facecolor=COLORS["surface"], labelcolor=COLORS["text_primary"])
        ax3.set_facecolor(COLORS["background"])
        ax3.tick_params(colors=COLORS["text_secondary"])
        
        charts["assists_vs_xa"] = self.render_chart_to_base64(fig3)
        
        # Chart 4: ICT Index Components
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        
        ax4.plot(gw_df_sorted["gw"], gw_df_sorted["influence"], color="#FF6B6B", 
                label="Influence", linewidth=2)
        ax4.plot(gw_df_sorted["gw"], gw_df_sorted["creativity"], color="#4ECDC4", 
                label="Creativity", linewidth=2)
        ax4.plot(gw_df_sorted["gw"], gw_df_sorted["threat"], color="#FFE66D", 
                label="Threat", linewidth=2)
        ax4.set_xlabel("Gameweek", color=COLORS["text_primary"])
        ax4.set_ylabel("ICT Score", color=COLORS["text_primary"])
        ax4.legend(facecolor=COLORS["surface"], labelcolor=COLORS["text_primary"])
        ax4.set_facecolor(COLORS["background"])
        ax4.tick_params(colors=COLORS["text_secondary"])
        
        charts["ict_components"] = self.render_chart_to_base64(fig4)
        
        # Chart 5 (GK only): Saves vs Goals Conceded
        position = self.players_df[self.players_df["player_id"] == player_id]["position"]
        if not position.empty and position.iloc[0] in ["Goalkeeper"]:
            fig5, ax5 = plt.subplots(figsize=(10, 4))
            
            x = np.arange(len(gw_df_sorted))
            width = 0.35
            
            ax5.bar(x - width/2, gw_df_sorted["saves"], width, label="Saves", color=COLORS["primary"])
            ax5.bar(x + width/2, gw_df_sorted["goals_conceded"], width, label="Goals Conceded", color=COLORS["error"])
            ax5.set_xlabel("Gameweek", color=COLORS["text_primary"])
            ax5.set_ylabel("Count", color=COLORS["text_primary"])
            ax5.set_xticks(x)
            ax5.set_xticklabels(gw_df_sorted["gw"].tolist())
            ax5.legend(facecolor=COLORS["surface"], labelcolor=COLORS["text_primary"])
            ax5.set_facecolor(COLORS["background"])
            ax5.tick_params(colors=COLORS["text_secondary"])
            
            charts["gk_saves_gc"] = self.render_chart_to_base64(fig5)
            
        if player_id not in self.charts_cache:
            self.charts_cache[player_id] = {}
        self.charts_cache[player_id]["gw_charts"] = charts
        
        return charts


class AppState:
    """Global application state"""
    
    def __init__(self):
        self.current_player_id: Optional[str] = None
        self.watchlist_cache: Dict[str, Dict] = {}
        self.previous_view: str = "home"
        self.data_processor: Optional[DataProcessor] = None
        

# Global state
app_state = AppState()


def create_header(page: ft.Page, title: str, show_back: bool = False) -> ft.Container:
    """Create consistent header component"""
    content = []
    
    if show_back:
        content.append(
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=COLORS["primary"],
                on_click=lambda e: go_back(page),
                tooltip="Go Back"
            )
        )
        
    content.append(
        ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
    )
    
    return ft.Container(
        content=ft.Row(content, alignment=ft.MainAxisAlignment.START),
        padding=ft.padding.all(20),
        bgcolor=COLORS["surface"],
    )


def go_back(page: ft.Page):
    """Navigate back to previous view"""
    if app_state.previous_view == "home":
        page.content = create_home_view(page)
    elif app_state.previous_view == "players_hub":
        page.content = create_players_hub_view(page)
    elif app_state.previous_view == "scouting":
        page.content = create_scouting_view(page)
    elif app_state.previous_view == "watchlist":
        page.content = create_watchlist_view(page)
    elif app_state.previous_view == "player_dashboard":
        # Go back to where we came from
        page.content = create_players_hub_view(page)
        
    page.update()


def create_home_view(page: ft.Page) -> ft.Container:
    """Create Home View with Bento Grid layout"""
    
    def navigate_to(view: str):
        app_state.previous_view = "home"
        if view == "players_hub":
            page.content = create_players_hub_view(page)
        elif view == "scouting":
            page.content = create_scouting_view(page)
        elif view == "watchlist":
            page.content = create_watchlist_view(page)
        page.update()
        
    card_style = {
        "bgcolor": COLORS["surface"],
        "border_radius": 16,
        "padding": 24,
        "expand": True,
    }
    
    def create_card(title: str, subtitle: str, icon: str, navigate_to_view: str) -> ft.GestureDetector:
        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=48, color=COLORS["primary"]),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Text(subtitle, size=14, color=COLORS["text_secondary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
            ),
            on_tap=lambda e: navigate_to(navigate_to_view),
            **card_style
        )
        
    bento_grid = ft.Row([
        ft.Column([
            create_card("PLAYERS HUB", "Browse 60+ Players", ft.icons.PERSON_SEARCH, "players_hub"),
        ], expand=1),
        ft.Column([
            create_card("SCOUTING", "Find Your Ideal Profile", ft.icons.TUNE, "scouting"),
            create_card("MY WATCHLIST", "Track Your Targets", ft.icons.STAR, "watchlist"),
        ], expand=1),
    ], spacing=16)
    
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("EPL SCOUT 25/26", size=32, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                padding=ft.padding.only(top=40, bottom=20),
            ),
            ft.Text("Premier League Player Analysis & Scouting Tool", 
                   size=16, color=COLORS["text_secondary"]),
            ft.Container(height=20),
            bento_grid,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=40,
        expand=True,
    )


def create_players_hub_view(page: ft.Page) -> ft.Container:
    """Create Players Hub View"""
    
    # State for filters
    filter_state = {
        "position": None,
        "club": None,
        "market_value_min": 0,
        "market_value_max": 100000000,
        "search_query": "",
        "current_page": 0,
    }
    players_per_page = 25
    
    def apply_filters(e=None):
        """Filter players based on criteria"""
        if app_state.data_processor is None or app_state.data_processor.players_df is None:
            return []
            
        df = app_state.data_processor.players_df.copy()
        
        # Filter by position
        if filter_state["position"]:
            df = df[df["position"] == filter_state["position"]]
            
        # Filter by club
        if filter_state["club"]:
            df = df[df["club_id"] == filter_state["club"]]
            
        # Filter by market value
        df = df[(df["market_value_in_eur"] >= filter_state["market_value_min"]) & 
                (df["market_value_in_eur"] <= filter_state["market_value_max"])]
                
        # Filter by search query
        if filter_state["search_query"]:
            query = filter_state["search_query"].lower()
            df = df[df["name"].str.lower().str.contains(query, na=False)]
            
        # Filter out players with < 450 minutes
        stats_query = """
            SELECT player_id, SUM(minutes) as total_minutes 
            FROM playerstats 
            GROUP BY player_id 
            HAVING total_minutes >= 450
        """
        valid_players = pd.read_sql_query(stats_query, app_state.data_processor.db.conn)
        df = df[df["player_id"].isin(valid_players["player_id"])]
        
        return df
        
    def get_unique_positions() -> List[str]:
        if app_state.data_processor and app_state.data_processor.players_df is not None:
            return sorted(app_state.data_processor.players_df["position"].dropna().unique().tolist())
        return []
        
    def get_unique_clubs() -> List[tuple]:
        if app_state.data_processor and app_state.data_processor.clubs_df is not None:
            return [(row["club_id"], row["club_name"]) 
                    for _, row in app_state.data_processor.clubs_df.iterrows()]
        return []
        
    def on_search_change(e):
        """Handle search input with debounce simulation"""
        filter_state["search_query"] = e.control.value
        filter_state["current_page"] = 0
        update_results()
        
    def on_position_change(e):
        filter_state["position"] = e.control.value
        filter_state["current_page"] = 0
        update_results()
        
    def on_club_change(e):
        filter_state["club"] = e.control.value
        filter_state["current_page"] = 0
        update_results()
        
    def on_mv_min_change(e):
        try:
            filter_state["market_value_min"] = int(e.control.value) * 1000000
        except:
            filter_state["market_value_min"] = 0
        filter_state["current_page"] = 0
        update_results()
        
    def on_mv_max_change(e):
        try:
            filter_state["market_value_max"] = int(e.control.value) * 1000000
        except:
            filter_state["market_value_max"] = 100000000
        filter_state["current_page"] = 0
        update_results()
        
    def on_player_click(player_id: str):
        app_state.current_player_id = player_id
        app_state.previous_view = "players_hub"
        page.content = create_player_dashboard_view(page, player_id)
        page.update()
        
    results_container = ft.Container()
    
    def update_results():
        """Update the results table"""
        filtered_df = apply_filters()
        total_players = len(filtered_df)
        
        if total_players == 0:
            results_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SEARCH_OFF, size=64, color=COLORS["text_secondary"]),
                    ft.Text("No players found", size=18, color=COLORS["text_primary"]),
                    ft.Text("Try adjusting your filters", size=14, color=COLORS["text_secondary"]),
                    ft.ElevatedButton(
                        "Reset Filters",
                        bgcolor=COLORS["primary"],
                        color=COLORS["background"],
                        on_click=lambda e: reset_filters()
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=300,
            )
        else:
            # Pagination
            total_pages = (total_players + players_per_page - 1) // players_per_page
            filter_state["current_page"] = min(filter_state["current_page"], total_pages - 1)
            
            start_idx = filter_state["current_page"] * players_per_page
            end_idx = min(start_idx + players_per_page, total_players)
            page_df = filtered_df.iloc[start_idx:end_idx]
            
            # Create table rows
            rows = []
            for _, row in page_df.iterrows():
                mv = row.get("market_value_in_eur", 0)
                mv_str = f"€{mv/1e6:.1f}M" if mv else "N/A"
                
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.TextButton(
                                row.get("name", "Unknown"),
                                on_click=lambda e, pid=row["player_id"]: on_player_click(pid),
                                style=ft.ButtonStyle(color=COLORS["primary"])
                            )),
                            ft.DataCell(ft.Text(row.get("position", ""), color=COLORS["text_secondary"])),
                            ft.DataCell(ft.Text(row.get("current_club_name", ""), color=COLORS["text_secondary"])),
                            ft.DataCell(ft.Text(mv_str, color=COLORS["text_primary"])),
                        ]
                    )
                )
                
            # Pagination controls
            page_controls = ft.Row([
                ft.IconButton(
                    icon=ft.icons.CHEVRON_LEFT,
                    disabled=filter_state["current_page"] == 0,
                    on_click=lambda e: prev_page()
                ),
                ft.Text(f"Page {filter_state['current_page'] + 1} of {max(1, total_pages)}", 
                       color=COLORS["text_secondary"]),
                ft.IconButton(
                    icon=ft.icons.CHEVRON_RIGHT,
                    disabled=filter_state["current_page"] >= total_pages - 1,
                    on_click=lambda e: next_page()
                ),
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            results_container.content = ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Name", color=COLORS["text_secondary"])),
                        ft.DataColumn(ft.Text("Position", color=COLORS["text_secondary"])),
                        ft.DataColumn(ft.Text("Club", color=COLORS["text_secondary"])),
                        ft.DataColumn(ft.Text("Market Value", color=COLORS["text_secondary"])),
                    ],
                    rows=rows,
                    heading_row_color=COLORS["surface"],
                    data_row_color=COLORS["background"],
                ),
                page_controls,
            ])
            
        page.update()
        
    def prev_page():
        filter_state["current_page"] = max(0, filter_state["current_page"] - 1)
        update_results()
        
    def next_page():
        filter_state["current_page"] += 1
        update_results()
        
    def reset_filters():
        filter_state.update({
            "position": None,
            "club": None,
            "market_value_min": 0,
            "market_value_max": 100000000,
            "search_query": "",
            "current_page": 0,
        })
        search_field.value = ""
        position_dropdown.value = None
        club_dropdown.value = None
        mv_min_field.value = "0"
        mv_max_field.value = "100"
        update_results()
        
    # Create filter controls
    positions = get_unique_positions()
    clubs = get_unique_clubs()
    
    search_field = ft.TextField(
        hint_text="Search players...",
        prefix_icon=ft.icons.SEARCH,
        bgcolor=COLORS["surface"],
        border_color=COLORS["secondary"],
        color=COLORS["text_primary"],
        on_change=on_search_change,
        expand=True,
    )
    
    position_dropdown = ft.Dropdown(
        label="Position",
        options=[ft.dropdown.Option(p) for p in positions],
        bgcolor=COLORS["surface"],
        border_color=COLORS["secondary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        on_change=on_position_change,
        width=200,
    )
    
    club_dropdown = ft.Dropdown(
        label="Club",
        options=[ft.dropdown.Option(str(cid), text=cname) for cid, cname in clubs],
        bgcolor=COLORS["surface"],
        border_color=COLORS["secondary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        on_change=on_club_change,
        width=200,
    )
    
    mv_min_field = ft.TextField(
        label="Min Value (€M)",
        value="0",
        bgcolor=COLORS["surface"],
        border_color=COLORS["secondary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        on_change=on_mv_min_change,
        width=150,
    )
    
    mv_max_field = ft.TextField(
        label="Max Value (€M)",
        value="100",
        bgcolor=COLORS["surface"],
        border_color=COLORS["secondary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        on_change=on_mv_max_change,
        width=150,
    )
    
    filters_row = ft.Row([
        search_field,
        position_dropdown,
        club_dropdown,
        mv_min_field,
        mv_max_field,
    ], wrap=True)
    
    return ft.Container(
        content=ft.Column([
            create_header(page, "Players Hub", show_back=True),
            ft.Container(height=16),
            filters_row,
            ft.Container(height=16),
            ft.Divider(color=COLORS["secondary"]),
            ft.Container(height=8),
            results_container,
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor=COLORS["background"],
        expand=True,
    )


def create_scouting_view(page: ft.Page) -> ft.Container:
    """Create Scouting View"""
    
    scout_state = {
        "position_group": "MID",
        "sliders": {
            "xG_per_90": 50,
            "xA_per_90": 50,
            "xGI_per_90": 50,
            "recoveries": 50,
        },
        "age_min": 18,
        "age_max": 35,
        "mv_min": 0,
        "mv_max": 100000000,
        "contract_year": None,
        "results": [],
    }
    
    results_container = ft.Container()
    
    def on_position_change(e):
        scout_state["position_group"] = e.control.value
        
    def on_slider_change(slider_name: str, e):
        scout_state["sliders"][slider_name] = float(e.control.value)
        # Update label
        if slider_name in slider_labels:
            val = float(e.control.value)
            if val >= 90:
                slider_labels[slider_name].value = f"Elite ({val:.0f}th)"
            elif val >= 75:
                slider_labels[slider_name].value = f"Very Good ({val:.0f}th)"
            elif val >= 50:
                slider_labels[slider_name].value = f"Good ({val:.0f}th)"
            else:
                slider_labels[slider_name].value = f"Average ({val:.0f}th)"
            page.update()
            
    def on_age_min_change(e):
        try:
            scout_state["age_min"] = int(e.control.value)
        except:
            pass
            
    def on_age_max_change(e):
        try:
            scout_state["age_max"] = int(e.control.value)
        except:
            pass
            
    def on_mv_min_change(e):
        try:
            scout_state["mv_min"] = int(e.control.value) * 1000000
        except:
            pass
            
    def on_mv_max_change(e):
        try:
            scout_state["mv_max"] = int(e.control.value) * 1000000
        except:
            pass
            
    def on_contract_change(e):
        val = e.control.value
        scout_state["contract_year"] = int(val) if val else None
        
    def run_search(e):
        """Execute scouting search"""
        if app_state.data_processor is None:
            page.snack_bar = ft.SnackBar(ft.Text("Data not loaded yet!"))
            page.update()
            return
            
        results = app_state.data_processor.scout_players(
            position_group=scout_state["position_group"],
            sliders=scout_state["sliders"],
            age_range=(scout_state["age_min"], scout_state["age_max"]),
            market_value_range=(scout_state["mv_min"], scout_state["mv_max"]),
            contract_year=scout_state["contract_year"],
        )
        
        scout_state["results"] = results
        update_results()
        
    def update_results():
        """Display search results"""
        results = scout_state["results"]
        
        if not results:
            results_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SCOUT, size=64, color=COLORS["text_secondary"]),
                    ft.Text("No results yet", size=18, color=COLORS["text_primary"]),
                    ft.Text("Adjust filters and click Search", size=14, color=COLORS["text_secondary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=200,
            )
        else:
            rows = []
            for i, player in enumerate(results[:20], 1):  # Show top 20
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"#{i}", color=COLORS["text_secondary"])),
                            ft.DataCell(ft.TextButton(
                                player["name"],
                                on_click=lambda e, pid=player["player_id"]: on_player_click(pid),
                                style=ft.ButtonStyle(color=COLORS["primary"])
                            )),
                            ft.DataCell(ft.Text(player.get("club", ""), color=COLORS["text_secondary"])),
                            ft.DataCell(ft.Container(
                                content=ft.Text(f"{player['match_score']}%", 
                                             color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                                bgcolor=COLORS["surface"],
                                padding=8,
                                border_radius=8,
                            )),
                        ]
                    )
                )
                
            results_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Rank", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Player", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Club", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Match Score", color=COLORS["text_secondary"])),
                ],
                rows=rows,
                heading_row_color=COLORS["surface"],
                data_row_color=COLORS["background"],
            )
            
        page.update()
        
    def on_player_click(player_id: str):
        app_state.current_player_id = player_id
        app_state.previous_view = "scouting"
        page.content = create_player_dashboard_view(page, player_id)
        page.update()
        
    slider_labels = {}
    
    def create_slider(label: str, key: str) -> ft.Column:
        slider_labels[key] = ft.Text(f"Good (50th)", size=12, color=COLORS["text_secondary"])
        return ft.Column([
            ft.Text(label, color=COLORS["text_primary"]),
            ft.Slider(
                min=0, max=99, divisions=99,
                value=50,
                active_color=COLORS["primary"],
                on_change=lambda e, k=key: on_slider_change(k, e),
            ),
            slider_labels[key],
        ])
        
    position_options = [
        ft.dropdown.Option("GK", "Goalkeepers"),
        ft.dropdown.Option("DEF", "Defenders"),
        ft.dropdown.Option("MID", "Midfielders"),
        ft.dropdown.Option("FWD", "Forwards"),
    ]
    
    return ft.Container(
        content=ft.Column([
            create_header(page, "Scouting", show_back=True),
            ft.Container(height=16),
            
            # Section 1: Position Group
            ft.Text("1. Select Position Group", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.Dropdown(
                value="MID",
                options=position_options,
                bgcolor=COLORS["surface"],
                border_color=COLORS["secondary"],
                color=COLORS["text_primary"],
                label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                on_change=on_position_change,
                width=300,
            ),
            
            ft.Container(height=24),
            
            # Section 2: Ideal Profile
            ft.Text("2. Define Your Ideal Profile", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.Row([
                create_slider("xG/90 Percentile", "xG_per_90"),
                create_slider("xA/90 Percentile", "xA_per_90"),
                create_slider("xGI/90 Percentile", "xGI_per_90"),
                create_slider("Recoveries/90 Percentile", "recoveries"),
            ], wrap=True),
            
            ft.Container(height=24),
            
            # Section 3: Hard Filters
            ft.Text("3. Hard Filters (Optional)", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.TextField(
                    label="Min Age",
                    value="18",
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_age_min_change,
                    width=120,
                ),
                ft.TextField(
                    label="Max Age",
                    value="35",
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_age_max_change,
                    width=120,
                ),
                ft.TextField(
                    label="Min Value (€M)",
                    value="0",
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_mv_min_change,
                    width=150,
                ),
                ft.TextField(
                    label="Max Value (€M)",
                    value="100",
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_mv_max_change,
                    width=150,
                ),
                ft.Dropdown(
                    label="Contract Year",
                    options=[ft.dropdown.Option(str(y)) for y in range(2025, 2031)],
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_contract_change,
                    width=150,
                ),
            ], wrap=True),
            
            ft.Container(height=24),
            
            # Search Button
            ft.ElevatedButton(
                "SEARCH",
                bgcolor=COLORS["primary"],
                color=COLORS["background"],
                height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=run_search,
            ),
            
            ft.Container(height=24),
            
            # Results
            ft.Text("Results", size=18, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            results_container,
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor=COLORS["background"],
        padding=24,
        expand=True,
    )


def create_watchlist_view(page: ft.Page) -> ft.Container:
    """Create Watchlist View"""
    
    watchlist_state = {
        "search_query": "",
        "position_filter": None,
        "club_filter": None,
        "selected_players": set(),
    }
    
    results_container = ft.Container()
    
    def load_watchlist() -> List[Dict]:
        """Load watchlist from database"""
        query = """
            SELECT w.player_id, w.rating, w.notes, w.created_at,
                   pi.name, pi.position, pi.current_club_name, pi.market_value_in_eur
            FROM watchlist w
            JOIN playersinfo pi ON w.player_id = pi.player_id
        """
        df = pd.read_sql_query(query, app_state.data_processor.db.conn)
        return df.to_dict("records")
        
    def save_watchlist_entry(player_id: str, rating: int = None, notes: str = None):
        """Save or update watchlist entry"""
        if rating is not None:
            app_state.data_processor.db.cursor.execute(
                "INSERT OR REPLACE INTO watchlist (player_id, rating, notes) VALUES (?, ?, ?)",
                (player_id, rating, notes)
            )
        elif notes is not None:
            # Get current rating
            app_state.data_processor.db.cursor.execute(
                "SELECT rating FROM watchlist WHERE player_id = ?", (player_id,)
            )
            row = app_state.data_processor.db.cursor.fetchone()
            rating = row[0] if row else 0
            app_state.data_processor.db.cursor.execute(
                "INSERT OR REPLACE INTO watchlist (player_id, rating, notes) VALUES (?, ?, ?)",
                (player_id, rating, notes)
            )
        app_state.data_processor.db.conn.commit()
        
    def delete_from_watchlist(player_id: str):
        """Delete player from watchlist"""
        app_state.data_processor.db.cursor.execute(
            "DELETE FROM watchlist WHERE player_id = ?", (player_id,)
        )
        app_state.data_processor.db.conn.commit()
        
    def delete_all_from_watchlist():
        """Delete all players from watchlist"""
        app_state.data_processor.db.cursor.execute("DELETE FROM watchlist")
        app_state.data_processor.db.conn.commit()
        
    def on_search_change(e):
        watchlist_state["search_query"] = e.control.value.lower()
        update_results()
        
    def on_position_filter(e):
        watchlist_state["position_filter"] = e.control.value
        update_results()
        
    def on_club_filter(e):
        watchlist_state["club_filter"] = e.control.value
        update_results()
        
    def on_rating_click(player_id: str, rating: int):
        save_watchlist_entry(player_id, rating=rating)
        update_results()
        
    def on_notes_change(e, player_id: str):
        save_watchlist_entry(player_id, notes=e.control.value)
        
    def on_delete(player_id: str):
        delete_from_watchlist(player_id)
        update_results()
        
    def on_delete_all(e):
        delete_all_from_watchlist()
        update_results()
        
    def on_player_click(player_id: str):
        app_state.current_player_id = player_id
        app_state.previous_view = "watchlist"
        page.content = create_player_dashboard_view(page, player_id)
        page.update()
        
    def create_star_rating(player_id: str, current_rating: int) -> ft.Row:
        """Create clickable star rating"""
        stars = []
        for i in range(1, 6):
            stars.append(
                ft.IconButton(
                    icon=ft.icons.STAR if i <= current_rating else ft.icons.STAR_BORDER,
                    icon_color=COLORS["primary"] if i <= current_rating else COLORS["text_secondary"],
                    icon_size=20,
                    on_click=lambda e, pid=player_id, r=i: on_rating_click(pid, r),
                    tooltip=f"Rate {i} stars",
                )
            )
        return ft.Row(stars, spacing=0)
        
    def update_results():
        """Update watchlist display"""
        watchlist = load_watchlist()
        
        # Apply filters
        filtered = watchlist
        
        if watchlist_state["search_query"]:
            filtered = [p for p in filtered if watchlist_state["search_query"] in p.get("name", "").lower()]
            
        if watchlist_state["position_filter"]:
            filtered = [p for p in filtered if p.get("position") == watchlist_state["position_filter"]]
            
        if watchlist_state["club_filter"]:
            filtered = [p for p in filtered if p.get("current_club_name") == watchlist_state["club_filter"]]
            
        if not filtered:
            results_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.STAR_BORDER, size=64, color=COLORS["text_secondary"]),
                    ft.Text("Your watchlist is empty", size=18, color=COLORS["text_primary"]),
                    ft.Text("Add players from the Hub", size=14, color=COLORS["text_secondary"]),
                    ft.ElevatedButton(
                        "Go to Players Hub",
                        bgcolor=COLORS["primary"],
                        color=COLORS["background"],
                        on_click=lambda e: navigate_to_hub()
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=300,
            )
        else:
            rows = []
            for player in filtered:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.TextButton(
                                player.get("name", "Unknown"),
                                on_click=lambda e, pid=player["player_id"]: on_player_click(pid),
                                style=ft.ButtonStyle(color=COLORS["primary"])
                            )),
                            ft.DataCell(ft.Text(player.get("current_club_name", ""), color=COLORS["text_secondary"])),
                            ft.DataCell(ft.Text(player.get("position", ""), color=COLORS["text_secondary"])),
                            ft.DataCell(ft.TextField(
                                value=player.get("notes", ""),
                                hint_text="Add notes...",
                                bgcolor=COLORS["surface"],
                                border_color=COLORS["secondary"],
                                color=COLORS["text_primary"],
                                content_padding=8,
                                on_change=lambda e, pid=player["player_id"]: on_notes_change(e, pid),
                                width=200,
                            )),
                            ft.DataCell(create_star_rating(player["player_id"], player.get("rating", 0))),
                            ft.DataCell(ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_color=COLORS["error"],
                                on_click=lambda e, pid=player["player_id"]: on_delete(pid),
                            )),
                        ]
                    )
                )
                
            results_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Name", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Club", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Position", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Notes", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Rating", color=COLORS["text_secondary"])),
                    ft.DataColumn(ft.Text("Delete", color=COLORS["text_secondary"])),
                ],
                rows=rows,
                heading_row_color=COLORS["surface"],
                data_row_color=COLORS["background"],
            )
            
        page.update()
        
    def navigate_to_hub():
        app_state.previous_view = "watchlist"
        page.content = create_players_hub_view(page)
        page.update()
        
    # Get unique positions and clubs from watchlist
    watchlist = load_watchlist()
    positions = sorted(set(p.get("position") for p in watchlist if p.get("position")))
    clubs = sorted(set(p.get("current_club_name") for p in watchlist if p.get("current_club_name")))
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=COLORS["primary"],
                    on_click=lambda e: go_back(page),
                ),
                ft.Text("My Watchlist", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Spacer(),
                ft.ElevatedButton(
                    "Delete All",
                    bgcolor=COLORS["error"],
                    color=COLORS["text_primary"],
                    on_click=on_delete_all,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=16),
            
            # Toolbar
            ft.Row([
                ft.TextField(
                    hint_text="Search watchlist...",
                    prefix_icon=ft.icons.SEARCH,
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    on_change=on_search_change,
                    expand=True,
                ),
                ft.Dropdown(
                    label="Position",
                    options=[ft.dropdown.Option(p) for p in positions],
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_position_filter,
                    width=150,
                ),
                ft.Dropdown(
                    label="Club",
                    options=[ft.dropdown.Option(c) for c in clubs],
                    bgcolor=COLORS["surface"],
                    border_color=COLORS["secondary"],
                    color=COLORS["text_primary"],
                    label_style=ft.TextStyle(color=COLORS["text_secondary"]),
                    on_change=on_club_filter,
                    width=150,
                ),
            ]),
            
            ft.Container(height=16),
            ft.Divider(color=COLORS["secondary"]),
            ft.Container(height=8),
            
            results_container,
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor=COLORS["background"],
        padding=24,
        expand=True,
    )


def create_player_dashboard_view(page: ft.Page, player_id: str) -> ft.Container:
    """Create Player Dashboard View"""
    
    dashboard_state = {
        "current_tab": "overview",
    }
    
    # Get player data
    if app_state.data_processor is None:
        return ft.Container(
            content=ft.Text("Data not loaded"),
            bgcolor=COLORS["background"],
        )
        
    player_stats = app_state.data_processor.get_player_stats(player_id)
    gw_records = app_state.data_processor.get_gw_records(player_id)
    
    if not player_stats:
        return ft.Container(
            content=ft.Text("Player not found"),
            bgcolor=COLORS["background"],
        )
        
    content_area = ft.Container()
    
    def switch_tab(tab: str):
        dashboard_state["current_tab"] = tab
        update_content()
        
    def update_content():
        """Update content based on selected tab"""
        tab = dashboard_state["current_tab"]
        
        if tab == "overview":
            content_area.content = create_overview_tab(page, player_id, player_stats)
        elif tab == "gw_records":
            content_area.content = create_gw_records_tab(page, player_id, gw_records)
        elif tab == "performance":
            content_area.content = create_performance_tab(page, player_id, gw_records)
            
        page.update()
        
    def add_to_watchlist(e):
        """Add player to watchlist"""
        if app_state.data_processor:
            app_state.data_processor.db.cursor.execute(
                "INSERT OR REPLACE INTO watchlist (player_id, rating, notes) VALUES (?, ?, ?)",
                (player_id, 0, "")
            )
            app_state.data_processor.db.conn.commit()
            page.snack_bar = ft.SnackBar(
                ft.Text(f"{player_stats['name']} added to watchlist!"),
                bgcolor=COLORS["success"],
            )
            page.update()
            
    def show_similar_players(e):
        """Show similar players modal"""
        similar = app_state.data_processor.find_similar_players(player_id)
        
        items = []
        for player in similar:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(player.get("name", ""), color=COLORS["text_primary"]),
                            ft.Text(player.get("club", ""), size=12, color=COLORS["text_secondary"]),
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(f"{player['score']}%", 
                                         color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                            bgcolor=COLORS["surface"],
                            padding=8,
                            border_radius=8,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=12,
                    margin=ft.margin.only(bottom=8),
                    bgcolor=COLORS["surface"],
                    border_radius=8,
                )
            )
            
        dialog = ft.AlertDialog(
            title=ft.Text(f"Similar Players to {player_stats['name']}", color=COLORS["text_primary"]),
            content=ft.Column(items, scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_dialog()),
            ],
            bgcolor=COLORS["background"],
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
        
    def close_dialog():
        page.dialog.open = False
        page.update()
        
    # Tabs
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Overview"),
            ft.Tab(text="GW Records"),
            ft.Tab(text="Performance"),
        ],
        on_change=lambda e: switch_tab(e.control.selected_index),
        bgcolor=COLORS["background"],
        indicator_color=COLORS["primary"],
        label_color=COLORS["text_primary"],
        unselected_label_color=COLORS["text_secondary"],
    )
    
    update_content()
    
    return ft.Container(
        content=ft.Column([
            create_header(page, player_stats.get("name", "Player"), show_back=True),
            ft.Container(height=8),
            ft.Row([
                ft.Text(player_stats.get("position", ""), color=COLORS["text_secondary"]),
                ft.Text(" • ", color=COLORS["text_secondary"]),
                ft.Text(player_stats.get("club_name", ""), color=COLORS["text_secondary"]),
            ]),
            tabs,
            ft.Container(height=16),
            content_area,
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor=COLORS["background"],
        padding=24,
        expand=True,
    )


def create_overview_tab(page: ft.Page, player_id: str, stats: Dict) -> ft.Container:
    """Create Overview Tab content"""
    
    def add_to_watchlist(e):
        if app_state.data_processor:
            app_state.data_processor.db.cursor.execute(
                "INSERT OR REPLACE INTO watchlist (player_id, rating, notes) VALUES (?, ?, ?)",
                (player_id, 0, "")
            )
            app_state.data_processor.db.conn.commit()
            page.snack_bar = ft.SnackBar(
                ft.Text(f"{stats['name']} added to watchlist!"),
                bgcolor=COLORS["success"],
            )
            page.update()
            
    def show_similar_players(e):
        similar = app_state.data_processor.find_similar_players(player_id)
        
        items = []
        for player in similar:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(player.get("name", "Unknown"), color=COLORS["text_primary"]),
                            ft.Text(player.get("club", ""), size=12, color=COLORS["text_secondary"]),
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(f"{player['score']}%", 
                                         color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                            bgcolor=COLORS["surface"],
                            padding=8,
                            border_radius=8,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=12,
                    margin=ft.margin.only(bottom=8),
                    bgcolor=COLORS["surface"],
                    border_radius=8,
                )
            )
            
        dialog = ft.AlertDialog(
            title=ft.Text(f"Similar Players to {stats['name']}", color=COLORS["text_primary"]),
            content=ft.Column(items, scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Close", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
            ],
            bgcolor=COLORS["background"],
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
        
    # Left sidebar with player info
    position = stats.get("position", "MID")
    pos_group = app_state.data_processor.get_position_group(position) if app_state.data_processor else "MID"
    
    # Get radar chart
    radar_chart = ""
    if app_state.data_processor:
        radar_chart = app_state.data_processor.create_radar_chart(player_id, stats)
        
    # Season stats grid
    stats_items = SEASON_STATS.get(pos_group, SEASON_STATS["MID"])
    stats_grid = []
    
    for stat_key, stat_label in stats_items:
        value = stats.get(stat_key, 0)
        if isinstance(value, float):
            value = f"{value:.2f}" if value < 10 else f"{value:.1f}"
            
        stats_grid.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(stat_label, size=11, color=COLORS["text_secondary"]),
                    ft.Text(str(value), size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=COLORS["surface"],
                padding=12,
                border_radius=8,
            )
        )
        
    # Derived stats
    derived_stats = []
    if stats.get("minutes", 0) > 0:
        goals_assists = stats.get("goals_scored", 0) + stats.get("assists", 0)
        if goals_assists > 0:
            min_per_gc = stats["minutes"] / goals_assists
            derived_stats.append(("Min per Goal Contribution", f"{min_per_gc:.1f}"))
            
        tackles = stats.get("tackles", 0)
        clearances = stats.get("clearances_blocks_interceptions", 0)
        def_actions_90 = (tackles + clearances) / stats["minutes"] * 90
        derived_stats.append(("Defensive Actions/90", f"{def_actions_90:.1f}"))
        
    derived_grid = []
    for label, value in derived_stats:
        derived_grid.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(label, size=11, color=COLORS["text_secondary"]),
                    ft.Text(value, size=14, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=COLORS["surface"],
                padding=12,
                border_radius=8,
            )
        )
        
    left_sidebar = ft.Column([
        # Player image placeholder
        ft.Container(
            content=ft.Icon(ft.icons.PERSON, size=80, color=COLORS["text_secondary"]),
            bgcolor=COLORS["surface"],
            border_radius=8,
            padding=20,
            alignment=ft.alignment.center,
            width=150,
            height=150,
        ),
        
        # Info grid
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Nationality", size=12, color=COLORS["text_secondary"]),
                    ft.Text(stats.get("country_of_citizenship", "N/A"), size=12, color=COLORS["text_primary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Age", size=12, color=COLORS["text_secondary"]),
                    ft.Text("N/A", size=12, color=COLORS["text_primary"]),  # Would need to calculate
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Position", size=12, color=COLORS["text_secondary"]),
                    ft.Text(stats.get("position", ""), size=12, color=COLORS["text_primary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Club", size=12, color=COLORS["text_secondary"]),
                    ft.Text(stats.get("club_name", ""), size=12, color=COLORS["text_primary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Market Value", size=12, color=COLORS["text_secondary"]),
                    ft.Text(f"€{stats.get('market_value_in_eur', 0)/1e6:.1f}M", size=12, color=COLORS["text_primary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=8),
            bgcolor=COLORS["surface"],
            padding=16,
            border_radius=8,
        ),
        
        # Add to watchlist button
        ft.ElevatedButton(
            "Add to Watchlist",
            icon=ft.icons.STAR,
            bgcolor=COLORS["primary"],
            color=COLORS["background"],
            on_click=add_to_watchlist,
        ),
        
        # Find similar button
        ft.OutlinedButton(
            "Find Similar",
            icon=ft.icons.SEARCH,
            side=ft.BorderSide(1, COLORS["primary"]),
            on_click=show_similar_players,
        ),
    ], spacing=16)
    
    return ft.Row([
        # Left sidebar
        ft.Column([left_sidebar], width=250),
        
        # Main content
        ft.Column([
            # Radar chart
            ft.Text("Performance Radar", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Image(src=radar_chart, height=300, width=300) if radar_chart else ft.Text("Chart unavailable"),
                alignment=ft.alignment.center,
            ),
            
            ft.Container(height=24),
            
            # Season statistics
            ft.Text("Season Statistics", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.GridView(
                runs_count=4,
                child_aspect_ratio=1.5,
                children=stats_grid,
                spacing=8,
                run_spacing=8,
            ),
            
            ft.Container(height=16),
            
            # Derived stats
            ft.Text("Derived Statistics", size=16, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
            ft.GridView(
                runs_count=2,
                child_aspect_ratio=2,
                children=derived_grid,
                spacing=8,
                run_spacing=8,
            ),
        ], expand=True),
    ], spacing=24)


def create_gw_records_tab(page: ft.Page, player_id: str, gw_df: pd.DataFrame) -> ft.Container:
    """Create GW Records Tab content"""
    
    if gw_df.empty:
        return ft.Container(
            content=ft.Text("No gameweek records available"),
            bgcolor=COLORS["background"],
        )
        
    # Create table rows
    rows = []
    for _, row in gw_df.iterrows():
        cells = [
            ft.DataCell(ft.Text(f"GW{int(row['gw'])}", color=COLORS["text_primary"])),
            ft.DataCell(ft.Text(f"{int(row['minutes'])}" if pd.notna(row["minutes"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['starts'])}" if pd.notna(row["starts"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['goals_scored'])}" if pd.notna(row["goals_scored"]) and row["goals_scored"] > 0 else "-", color=COLORS["success"] if pd.notna(row["goals_scored"]) and row["goals_scored"] > 0 else COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['assists'])}" if pd.notna(row["assists"]) and row["assists"] > 0 else "-", color=COLORS["primary"] if pd.notna(row["assists"]) and row["assists"] > 0 else COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['clean_sheets'])}" if pd.notna(row["clean_sheets"]) and row["clean_sheets"] > 0 else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['yellow_cards'])}" if pd.notna(row["yellow_cards"]) and row["yellow_cards"] > 0 else "-", color=COLORS["warning"] if pd.notna(row["yellow_cards"]) and row["yellow_cards"] > 0 else COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['red_cards'])}" if pd.notna(row["red_cards"]) and row["red_cards"] > 0 else "-", color=COLORS["error"] if pd.notna(row["red_cards"]) and row["red_cards"] > 0 else COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_goals']:.2f}" if pd.notna(row["expected_goals"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_assists']:.2f}" if pd.notna(row["expected_assists"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_goal_involvements']:.2f}" if pd.notna(row["expected_goal_involvements"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_goals_per_90']:.2f}" if pd.notna(row["expected_goals_per_90"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_assists_per_90']:.2f}" if pd.notna(row["expected_assists_per_90"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['expected_goal_involvements_per_90']:.2f}" if pd.notna(row["expected_goal_involvements_per_90"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['influence']:.1f}" if pd.notna(row["influence"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['creativity']:.1f}" if pd.notna(row["creativity"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['threat']:.1f}" if pd.notna(row["threat"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{row['ict_index']:.1f}" if pd.notna(row["ict_index"]) else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['saves'])}" if pd.notna(row["saves"]) and row["saves"] > 0 else "-", color=COLORS["text_secondary"])),
            ft.DataCell(ft.Text(f"{int(row['penalties_saved'])}" if pd.notna(row["penalties_saved"]) and row["penalties_saved"] > 0 else "-", color=COLORS["text_secondary"])),
        ]
        rows.append(ft.DataRow(cells=cells))
        
    # Footer summary
    total_games = len(gw_df)
    total_goals = gw_df["goals_scored"].sum()
    total_assists = gw_df["assists"].sum()
    total_mins = gw_df["minutes"].sum()
    
    return ft.Column([
        ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("GW", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("Min", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("ST", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("G", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("A", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("CS", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("YC", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("RC", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xG", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xA", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xGI", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xG/90", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xA/90", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("xGI/90", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("Inf", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("Cre", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("Thr", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("ICT", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("Sv", color=COLORS["text_secondary"], size=10)),
                    ft.DataColumn(ft.Text("PS", color=COLORS["text_secondary"], size=10)),
                ],
                rows=rows,
                heading_row_color=COLORS["surface"],
                data_row_color=COLORS["background"],
                column_spacing=4,
            ),
            scroll=ft.ScrollMode.HORIZONTAL,
        ),
        
        ft.Container(height=16),
        ft.Divider(color=COLORS["secondary"]),
        ft.Container(height=8),
        
        # Footer summary
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("Games Played", size=12, color=COLORS["text_secondary"]),
                    ft.Text(str(total_games), size=18, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                padding=16,
                border_radius=8,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Total Goals", size=12, color=COLORS["text_secondary"]),
                    ft.Text(str(int(total_goals)), size=18, color=COLORS["success"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                padding=16,
                border_radius=8,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Total Assists", size=12, color=COLORS["text_secondary"]),
                    ft.Text(str(int(total_assists)), size=18, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                padding=16,
                border_radius=8,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Total Minutes", size=12, color=COLORS["text_secondary"]),
                    ft.Text(str(int(total_mins)), size=18, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                padding=16,
                border_radius=8,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
    ])


def create_performance_tab(page: ft.Page, player_id: str, gw_df: pd.DataFrame) -> ft.Container:
    """Create Performance Tab content"""
    
    if gw_df.empty or app_state.data_processor is None:
        return ft.Container(
            content=ft.Text("No performance data available"),
            bgcolor=COLORS["background"],
        )
        
    # Generate charts
    charts = app_state.data_processor.create_gw_charts(player_id, gw_df)
    
    chart_widgets = []
    
    if "minutes" in charts:
        chart_widgets.append(
            ft.Column([
                ft.Text("Minutes per Gameweek", size=14, color=COLORS["text_primary"]),
                ft.Image(src=charts["minutes"], height=200),
            ])
        )
        
    if "goals_vs_xg" in charts:
        chart_widgets.append(
            ft.Column([
                ft.Text("Goals vs Expected Goals (Cumulative)", size=14, color=COLORS["text_primary"]),
                ft.Image(src=charts["goals_vs_xg"], height=200),
            ])
        )
        
    if "assists_vs_xa" in charts:
        chart_widgets.append(
            ft.Column([
                ft.Text("Assists vs Expected Assists (Cumulative)", size=14, color=COLORS["text_primary"]),
                ft.Image(src=charts["assists_vs_xa"], height=200),
            ])
        )
        
    if "ict_components" in charts:
        chart_widgets.append(
            ft.Column([
                ft.Text("ICT Index Components", size=14, color=COLORS["text_primary"]),
                ft.Image(src=charts["ict_components"], height=200),
            ])
        )
        
    if "gk_saves_gc" in charts:
        chart_widgets.append(
            ft.Column([
                ft.Text("Saves vs Goals Conceded", size=14, color=COLORS["text_primary"]),
                ft.Image(src=charts["gk_saves_gc"], height=200),
            ])
        )
        
    return ft.Column([
        ft.GridView(
            runs_count=2,
            child_aspect_ratio=2,
            children=chart_widgets,
            spacing=16,
            run_spacing=16,
        ),
    ])


def initialize_app_data():
    """Initialize application data from CSV files"""
    db_manager = DatabaseManager()
    db_manager.connect()
    db_manager.create_tables()
    
    data_processor = DataProcessor(db_manager)
    
    # Try to load CSV files if they exist
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    clubs_csv = os.path.join(data_dir, "clubs.csv")
    players_csv = os.path.join(data_dir, "playersinfo.csv")
    stats_csv = os.path.join(data_dir, "playerstats.csv")
    
    # If data directory doesn't exist, create sample data
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        create_sample_data(data_dir)
        
    data_processor.load_data(clubs_csv, players_csv, stats_csv)
    data_processor.calculate_league_percentiles()
    
    app_state.data_processor = data_processor
    
    return data_processor


def create_sample_data(data_dir: str):
    """Create sample data for testing"""
    import random
    
    # Sample clubs
    clubs = [
        ("ARS", "Arsenal"), ("AVL", "Aston Villa"), ("BOU", "Bournemouth"),
        ("BRE", "Brentford"), ("BHA", "Brighton"), ("CHE", "Chelsea"),
        ("CRY", "Crystal Palace"), ("EVE", "Everton"), ("FUL", "Fulham"),
        ("IPS", "Ipswich"), ("LEI", "Leicester"), ("LIV", "Liverpool"),
        ("MCI", "Man City"), ("MUN", "Man Utd"), ("NEW", "Newcastle"),
        ("NFO", "Nott'm Forest"), ("SOU", "Southampton"), ("TOT", "Tottenham"),
        ("WHU", "West Ham"), ("WOL", "Wolves"),
    ]
    
    clubs_df = pd.DataFrame(clubs, columns=["club_id", "club_name"])
    clubs_df.to_csv(os.path.join(data_dir, "clubs.csv"), index=False)
    
    # Sample players
    positions = ["Goalkeeper", "Centre-Back", "Left-Back", "Right-Back", "Defensive Midfield",
                "Central Midfield", "Attacking Midfield", "Left Winger", "Right Winger", "Centre-Forward"]
    
    players = []
    for i in range(60):
        player_id = f"P{i:04d}"
        club_id = random.choice([c[0] for c in clubs])
        club_name = next(c[1] for c in clubs if c[0] == club_id)
        position = random.choice(positions)
        
        players.append({
            "player_id": player_id,
            "first_name": f"Player{i}",
            "last_name": f"Name{i}",
            "name": f"Player{i} Name{i}",
            "last_season": 2025,
            "club_id": club_id,
            "country_of_citizenship": random.choice(["England", "Spain", "France", "Brazil", "Argentina"]),
            "date_of_birth": f"199{random.randint(0, 9)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "sub_position": position,
            "position": position,
            "foot": random.choice(["Left", "Right", "Both"]),
            "height_in_cm": random.randint(170, 195),
            "contract_expiration_date": f"202{random.randint(5, 9)}-06-30",
            "image_url": "",
            "current_club_name": club_name,
            "market_value_in_eur": random.randint(1000000, 100000000),
        })
        
    players_df = pd.DataFrame(players)
    players_df.to_csv(os.path.join(data_dir, "playersinfo.csv"), index=False)
    
    # Sample player stats
    stats_rows = []
    for player in players:
        for gw in range(1, random.randint(10, 20)):
            stats_rows.append({
                "player_id": player["player_id"],
                "gw": gw,
                "expected_goals": random.uniform(0, 1.5),
                "expected_assists": random.uniform(0, 1),
                "expected_goal_involvements": random.uniform(0, 2),
                "expected_goals_conceded": random.uniform(0, 2) if "Goalkeeper" in position or "Back" in position else 0,
                "expected_goals_per_90": random.uniform(0, 1.5),
                "expected_assists_per_90": random.uniform(0, 1),
                "expected_goal_involvements_per_90": random.uniform(0, 2),
                "expected_goals_conceded_per_90": random.uniform(0, 2),
                "influence": random.uniform(0, 150),
                "creativity": random.uniform(0, 100),
                "threat": random.uniform(0, 150),
                "ict_index": random.uniform(0, 200),
                "news": "",
                "news_added": None,
                "minutes": random.randint(0, 90),
                "goals_scored": random.randint(0, 3) if "Forward" in position or "Midfield" in position else random.randint(0, 1),
                "assists": random.randint(0, 2),
                "clean_sheets": random.randint(0, 1) if "Goalkeeper" in position or "Back" in position else 0,
                "goals_conceded": random.randint(0, 3) if "Goalkeeper" in position else 0,
                "own_goals": 0,
                "penalties_saved": random.randint(0, 1) if "Goalkeeper" in position else 0,
                "penalties_missed": 0,
                "yellow_cards": random.randint(0, 2),
                "red_cards": 0,
                "saves": random.randint(0, 8) if "Goalkeeper" in position else 0,
                "starts": random.randint(0, 1),
                "defensive_contribution": random.uniform(0, 15),
                "saves_per_90": random.uniform(0, 8),
                "clean_sheets_per_90": random.uniform(0, 0.5),
                "goals_conceded_per_90": random.uniform(0, 2),
                "starts_per_90": random.uniform(0, 1),
                "defensive_contribution_per_90": random.uniform(0, 15),
                "tackles": random.randint(0, 10),
                "clearances_blocks_interceptions": random.randint(0, 15),
                "recoveries": random.randint(0, 15),
            })
            
    stats_df = pd.DataFrame(stats_rows)
    stats_df.to_csv(os.path.join(data_dir, "playerstats.csv"), index=False)


def main(page: ft.Page):
    """Main application entry point"""
    
    # Page configuration
    page.title = "EPL Scout 25/26"
    page.bgcolor = COLORS["background"]
    page.window.width = 1280
    page.window.height = 800
    page.window.resizable = False
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    # Initialize data
    def on_load(e):
        try:
            initialize_app_data()
            page.snack_bar = ft.SnackBar(
                ft.Text("Application initialized successfully!"),
                bgcolor=COLORS["success"],
            )
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Error loading data: {str(ex)}"),
                bgcolor=COLORS["error"],
            )
        finally:
            page.content = create_home_view(page)
            page.update()
            
    page.on_load = on_load
    
    # Show loading screen
    page.content = ft.Container(
        content=ft.Column([
            ft.CircularProgressIndicator(color=COLORS["primary"]),
            ft.Text("Loading EPL Scout...", color=COLORS["text_primary"]),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=COLORS["background"],
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
