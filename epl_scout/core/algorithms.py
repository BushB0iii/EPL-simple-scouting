"""
Business Logic Layer - Algorithms and Calculations
No UI dependencies, operates purely on data structures
"""
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.entities import PlayerInfo, PlayerStats, ScoutingResult


class AlgorithmService:
    """
    Pure algorithm implementations
    No database or UI dependencies
    Operates on lists of dataclasses/dicts
    """
    
    # Position group mappings
    POSITION_GROUPS = {
        'Goalkeeper': ['Goalkeeper'],
        'Defender': ['Centre-Back', 'Left-Back', 'Right-Back', 'Defender'],
        'Midfielder': ['Central Midfield', 'Attacking Midfield', 'Defensive Midfield', 
                      'Left Midfield', 'Right Midfield', 'Midfielder'],
        'Forward': ['Centre-Forward', 'Left Winger', 'Right Winger', 'Second Striker', 'Forward']
    }
    
    # Stats by position for similarity calculation
    POSITION_STATS = {
        'Goalkeeper': ['saves_per_90', 'clean_sheets_per_90', 'goals_conceded_per_90', 
                       'expected_goals_conceded_per_90', 'influence'],
        'Defender': ['tackles', 'clearances_blocks_interceptions', 'defensive_contribution_per_90',
                     'expected_goals_conceded_per_90', 'influence'],
        'Midfielder': ['creativity', 'expected_assists_per_90', 'recoveries',
                       'expected_goal_involvements_per_90', 'ict_index'],
        'Forward': ['expected_goals_per_90', 'goals_scored', 'threat',
                    'expected_goal_involvements_per_90', 'ict_index']
    }
    
    @staticmethod
    def get_position_group(position: str) -> str:
        """Map specific position to position group"""
        for group, positions in AlgorithmService.POSITION_GROUPS.items():
            if position in positions:
                return group
        return 'Forward'  # Default
    
    @staticmethod
    def calculate_z_scores(values: List[float]) -> List[float]:
        """Calculate Z-scores for a list of values"""
        if len(values) == 0:
            return []
        
        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr)
        
        if std == 0:
            return [0.0] * len(values)
        
        return ((arr - mean) / std).tolist()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_similar_players(
        self,
        target_player_id: str,
        all_players: List[Dict[str, Any]],
        all_stats: List[Dict[str, Any]],
        position: str
    ) -> List[Dict[str, Any]]:
        """
        Find similar players using cosine similarity on Z-score normalized stats
        
        Args:
            target_player_id: ID of the player to find similarities for
            all_players: List of all player info dicts
            all_stats: List of all player stats dicts (aggregated per player)
            position: Target player's position
            
        Returns:
            List of similar players with match scores
        """
        # Get position group
        position_group = self.get_position_group(position)
        relevant_stats = self.POSITION_STATS.get(position_group, self.POSITION_STATS['Forward'])
        
        # Filter players by position group
        valid_positions = self.POSITION_GROUPS.get(position_group, [])
        candidates = [p for p in all_players if p.get('position') in valid_positions 
                     and p.get('player_id') != target_player_id]
        
        if not candidates:
            return []
        
        # Build stat vectors for all players
        player_vectors = {}
        for player in candidates:
            pid = player.get('player_id')
            stats = next((s for s in all_stats if s.get('player_id') == pid), None)
            
            if stats:
                vector = [stats.get(stat, 0) for stat in relevant_stats]
                player_vectors[pid] = vector
        
        if not player_vectors:
            return []
        
        # Get target player vector
        target_stats = next((s for s in all_stats if s.get('player_id') == target_player_id), None)
        if not target_stats:
            return []
        
        target_vector = [target_stats.get(stat, 0) for stat in relevant_stats]
        
        # Normalize all vectors using Z-score
        all_values = {stat: [] for stat in relevant_stats}
        for pid, vector in player_vectors.items():
            for i, stat in enumerate(relevant_stats):
                all_values[stat].append(vector[i])
        
        # Add target player values for normalization
        for i, stat in enumerate(relevant_stats):
            all_values[stat].append(target_vector[i])
        
        # Calculate Z-scores
        zscore_means = {}
        zscore_stds = {}
        for stat, values in all_values.items():
            arr = np.array(values)
            zscore_means[stat] = np.mean(arr)
            zscore_stds[stat] = np.std(arr) if np.std(arr) > 0 else 1.0
        
        # Normalize target vector
        target_zscore = []
        for i, stat in enumerate(relevant_stats):
            if zscore_stds[stat] > 0:
                target_zscore.append((target_vector[i] - zscore_means[stat]) / zscore_stds[stat])
            else:
                target_zscore.append(0.0)
        
        # Calculate similarity for each candidate
        results = []
        for player in candidates:
            pid = player.get('player_id')
            if pid not in player_vectors:
                continue
            
            # Normalize candidate vector
            candidate_zscore = []
            for i, stat in enumerate(relevant_stats):
                if zscore_stds[stat] > 0:
                    candidate_zscore.append((player_vectors[pid][i] - zscore_means[stat]) / zscore_stds[stat])
                else:
                    candidate_zscore.append(0.0)
            
            # Calculate cosine similarity
            similarity = self.cosine_similarity(target_zscore, candidate_zscore)
            
            # Convert to match score (0-100)
            match_score = ((similarity + 1) / 2) * 100
            
            results.append({
                'player_id': pid,
                'player_name': player.get('name', ''),
                'club_name': player.get('club_name', 'Unknown'),
                'position': player.get('position', ''),
                'match_score': round(match_score, 1)
            })
        
        # Sort by match score descending and return top 5
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:5]
    
    def scout_players(
        self,
        all_players: List[Dict[str, Any]],
        all_stats: List[Dict[str, Any]],
        position_group: str,
        targets: Dict[str, float],
        age_range: tuple = (0, 40),
        value_range: tuple = (0, 1000000000),
        contract_year: Optional[int] = None
    ) -> List[ScoutingResult]:
        """
        Scout players based on percentile targets
        
        Args:
            all_players: List of all player info dicts
            all_stats: List of all player stats dicts
            position_group: Target position group
            targets: Dict of stat_name -> target_percentile (e.g., {'xG/90': 80, 'xA/90': 70})
            age_range: (min_age, max_age)
            value_range: (min_value, max_value)
            contract_year: Filter by contract expiration year
        
        Returns:
            List of ScoutingResult sorted by match score
        """
        # Map position group to positions
        valid_positions = self.POSITION_GROUPS.get(position_group, [])
        
        # Calculate percentiles for all players
        stat_names = ['expected_goals_per_90', 'expected_assists_per_90', 
                      'expected_goal_involvements_per_90', 'recoveries']
        stat_display_names = {
            'expected_goals_per_90': 'xG/90',
            'expected_assists_per_90': 'xA/90',
            'expected_goal_involvements_per_90': 'xGI/90',
            'recoveries': 'recoveries'
        }
        
        # Build percentile lookup
        percentiles = self._calculate_percentiles(all_stats, stat_names)
        
        results = []
        for player in all_players:
            pid = player.get('player_id')
            
            # Check position filter
            if player.get('position') not in valid_positions:
                continue
            
            # Hard filters
            age = player.get('age', 0)
            if age < age_range[0] or age > age_range[1]:
                continue
            
            market_value = player.get('market_value_in_eur', 0)
            if market_value < value_range[0] or market_value > value_range[1]:
                continue
            
            # Contract filter
            if contract_year:
                contract_date = player.get('contract_expiration_date', '')
                if contract_date:
                    try:
                        from datetime import datetime
                        exp_year = int(contract_date.split('/')[-1])
                        if exp_year != contract_year:
                            continue
                    except:
                        pass
            
            # Get player stats
            stats = next((s for s in all_stats if s.get('player_id') == pid), None)
            if not stats:
                continue
            
            # Calculate match score for each target stat
            scores = []
            for stat_name, target_percentile in targets.items():
                if stat_name not in stat_names:
                    continue
                
                player_percentile = percentiles.get(stat_name, {}).get(pid, 50)
                
                # Score = 100 - abs difference from target
                score = 100 - abs(player_percentile - target_percentile)
                scores.append(score)
            
            if not scores:
                continue
            
            # Average match score
            match_score = sum(scores) / len(scores)
            
            results.append(ScoutingResult(
                player_id=pid,
                player_name=player.get('name', ''),
                club_name=player.get('club_name', 'Unknown'),
                position=player.get('position', ''),
                match_score=round(match_score, 1),
                age=age,
                market_value=market_value,
                contract_year=player.get('contract_expiration_date', '')[-4:] if player.get('contract_expiration_date') else ''
            ))
        
        # Sort by match score descending
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    
    def _calculate_percentiles(
        self, 
        all_stats: List[Dict[str, Any]], 
        stat_names: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate percentiles for all players for given stats
        
        Returns dict: {stat_name: {player_id: percentile}}
        """
        result = {}
        
        for stat_name in stat_names:
            # Collect all non-zero values
            values = [(s.get('player_id'), s.get(stat_name, 0)) 
                     for s in all_stats if s.get(stat_name, 0) > 0]
            
            if not values:
                continue
            
            # Sort by value
            values.sort(key=lambda x: x[1])
            
            # Calculate percentiles
            stat_percentiles = {}
            n = len(values)
            for i, (pid, value) in enumerate(values):
                percentile = (i + 1) / n * 100
                stat_percentiles[pid] = percentile
            
            result[stat_name] = stat_percentiles
        
        return result
    
    def aggregate_player_stats(self, stats_list: List[PlayerStats]) -> Dict[str, Any]:
        """
        Aggregate gameweek stats into season totals/averages
        
        Returns dict with aggregated statistics
        """
        if not stats_list:
            return {}
        
        total_minutes = sum(s.minutes for s in stats_list)
        total_goals = sum(s.goals_scored for s in stats_list)
        total_assists = sum(s.assists for s in stats_list)
        total_clean_sheets = sum(s.clean_sheets for s in stats_list)
        
        # Per 90 calculations
        if total_minutes > 0:
            goals_per_90 = (total_goals / total_minutes) * 90
            assists_per_90 = (total_assists / total_minutes) * 90
            goal_contributions_per_90 = ((total_goals + total_assists) / total_minutes) * 90
        else:
            goals_per_90 = 0
            assists_per_90 = 0
            goal_contributions_per_90 = 0
        
        # Minutes per goal contribution
        if total_goals + total_assists > 0:
            minutes_per_contribution = total_minutes / (total_goals + total_assists)
        else:
            minutes_per_contribution = float('inf')
        
        return {
            'total_minutes': total_minutes,
            'total_goals': total_goals,
            'total_assists': total_assists,
            'total_clean_sheets': total_clean_sheets,
            'goals_per_90': round(goals_per_90, 2),
            'assists_per_90': round(assists_per_90, 2),
            'goal_contributions_per_90': round(goal_contributions_per_90, 2),
            'minutes_per_contribution': round(minutes_per_contribution, 1) if minutes_per_contribution != float('inf') else 'N/A',
            'games_played': len(stats_list),
            'average_ict_index': round(sum(s.ict_index for s in stats_list) / len(stats_list), 2) if stats_list else 0
        }
