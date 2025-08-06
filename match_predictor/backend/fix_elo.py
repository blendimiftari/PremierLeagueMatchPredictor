import sqlite3
import logging
from datetime import datetime
import os
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EloFixer:
    def __init__(self, db_path="premier_league.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup"
        self.K_FACTOR = 30  # Keep the same K-factor as used in training
        self.HOME_ADVANTAGE = 70  # Keep the same home advantage as used in training
        
    def backup_database(self):
        """Create a backup of the database before making changes."""
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"Created backup at {self.backup_path}")
        else:
            logger.error(f"Database file {self.db_path} not found")
            raise FileNotFoundError(f"Database file {self.db_path} not found")
            
    def reset_elo_ratings(self):
        """Reset all team ELO ratings to the base value of 1500.0."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE teams SET current_elo_rating = 1500.0')
            conn.commit()
            logger.info("Reset all team ELO ratings to 1500.0")
            
    def update_elo_ratings(self, match_id):
        """Update ELO ratings for a single match."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get match details
            cursor.execute('''
                SELECT home_team_id, away_team_id, home_goals, away_goals, result
                FROM matches WHERE match_id = ?
            ''', (match_id,))
            
            match = cursor.fetchone()
            if not match:
                logger.warning(f"Match with ID {match_id} not found")
                return
                
            home_team_id, away_team_id, home_goals, away_goals, result = match
            
            # Get current ELO ratings
            cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (home_team_id,))
            home_elo = cursor.fetchone()[0]
            
            cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (away_team_id,))
            away_elo = cursor.fetchone()[0]
            
            # Calculate expected scores with home advantage
            home_expected = 1 / (1 + 10 ** ((away_elo - (home_elo + self.HOME_ADVANTAGE)) / 400))
            away_expected = 1 - home_expected
            
            # Calculate actual scores (1 for win, 0.5 for draw, 0 for loss)
            if result == -1:  # Home win
                home_actual = 1
                away_actual = 0
            elif result == 0:  # Draw
                home_actual = 0.5
                away_actual = 0.5
            else:  # Away win
                home_actual = 0
                away_actual = 1
                
            # Update ELO ratings
            new_home_elo = home_elo + self.K_FACTOR * (home_actual - home_expected)
            new_away_elo = away_elo + self.K_FACTOR * (away_actual - away_expected)
            
            # Log the ELO changes
            logger.debug(f"Match {match_id}: Home {home_elo:.2f} -> {new_home_elo:.2f}, Away {away_elo:.2f} -> {new_away_elo:.2f}")
            
            # Update the database
            cursor.execute('''
                UPDATE teams 
                SET current_elo_rating = ?, updated_at = CURRENT_TIMESTAMP
                WHERE team_id = ?
            ''', (new_home_elo, home_team_id))
            
            cursor.execute('''
                UPDATE teams 
                SET current_elo_rating = ?, updated_at = CURRENT_TIMESTAMP
                WHERE team_id = ?
            ''', (new_away_elo, away_team_id))
            
            conn.commit()
            
    def process_matches_chronologically(self):
        """Process all matches in chronological order to update ELO ratings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all matches ordered by date
            cursor.execute('''
                SELECT match_id, date 
                FROM matches 
                ORDER BY date ASC
            ''')
            
            matches = cursor.fetchall()
            total_matches = len(matches)
            
            logger.info(f"Processing {total_matches} matches chronologically...")
            
            # Track processed matches to avoid duplicates
            processed_matches = set()
            
            for i, (match_id, date) in enumerate(matches):
                if match_id in processed_matches:
                    logger.warning(f"Skipping duplicate match {match_id} from {date}")
                    continue
                    
                try:
                    self.update_elo_ratings(match_id)
                    processed_matches.add(match_id)
                    
                    if i % 100 == 0:  # Log progress
                        logger.info(f"Processed {i}/{total_matches} matches...")
                        conn.commit()  # Commit periodically
                except Exception as e:
                    logger.error(f"Error processing match {match_id}: {str(e)}")
                    continue
            
            conn.commit()  # Final commit
            logger.info(f"Successfully processed {len(processed_matches)} matches")
            
    def verify_elo_ratings(self):
        """Verify that ELO ratings have been calculated correctly."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current ELO ratings
            cursor.execute('''
                SELECT t.team_id, t.name, t.current_elo_rating,
                       COUNT(m.match_id) as total_matches,
                       SUM(CASE WHEN m.result = -1 AND m.home_team_id = t.team_id THEN 1
                               WHEN m.result = 1 AND m.away_team_id = t.team_id THEN 1
                               ELSE 0 END) as wins,
                       SUM(CASE WHEN m.result = 0 AND (m.home_team_id = t.team_id OR m.away_team_id = t.team_id) THEN 1
                               ELSE 0 END) as draws
                FROM teams t
                LEFT JOIN matches m ON t.team_id = m.home_team_id OR t.team_id = m.away_team_id
                GROUP BY t.team_id
                ORDER BY t.current_elo_rating DESC
            ''')
            
            teams = cursor.fetchall()
            
            logger.info("\nCurrent ELO Ratings and Performance:")
            for team in teams:
                team_id, name, elo, total_matches, wins, draws = team
                win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
                logger.info(f"{name}:")
                logger.info(f"  ELO: {elo:.2f}")
                logger.info(f"  Matches: {total_matches}")
                logger.info(f"  Win Rate: {win_rate:.1f}%")
                logger.info(f"  Draws: {draws}")
                
    def fix_elo_ratings(self):
        """Main function to fix ELO ratings."""
        try:
            # Backup the database
            self.backup_database()
            
            # Reset all ELO ratings
            self.reset_elo_ratings()
            
            # Process matches chronologically
            self.process_matches_chronologically()
            
            # Verify the results
            self.verify_elo_ratings()
            
            logger.info("ELO ratings have been successfully recalculated")
            
        except Exception as e:
            logger.error(f"Error fixing ELO ratings: {str(e)}")
            logger.info(f"Restoring from backup {self.backup_path}")
            
            # Restore from backup if available
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.db_path)
                logger.info("Database restored from backup")
            else:
                logger.error("No backup available to restore from")
                
            raise

if __name__ == "__main__":
    fixer = EloFixer()
    fixer.fix_elo_ratings() 