import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "premier_league.db", skip_historical_processing: bool = False):
        self.db_path = db_path
        self.skip_historical_processing = skip_historical_processing
        self._init_db()

    def connect(self):
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path, timeout=30.0)

    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False

    def get_all_teams(self) -> List[Dict]:
        """Get all teams from the database."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT team_id, name, current_elo_rating FROM teams ORDER BY name')
                teams = cursor.fetchall()
                return [
                    {
                        'team_id': team[0],
                        'name': team[1],
                        'elo_rating': team[2]
                    }
                    for team in teams
                ]
        except Exception as e:
            logger.error(f"Error getting teams: {str(e)}")
            raise

    def _init_db(self):
        """Initialize the database with required tables and handle migrations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if teams table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'")
            teams_table_exists = cursor.fetchone() is not None
            
            if not teams_table_exists:
                # Create Teams table with api_team_id
                cursor.execute('''
                    CREATE TABLE teams (
                        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_team_id INTEGER UNIQUE,
                        name TEXT NOT NULL,
                        current_elo_rating REAL NOT NULL DEFAULT 1500.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Create index on api_team_id for faster lookups
                cursor.execute('CREATE INDEX idx_teams_api_id ON teams(api_team_id)')
            else:
                # Check if api_team_id column exists
                cursor.execute("PRAGMA table_info(teams)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'api_team_id' not in columns:
                    # Drop the old table and create new one
                    cursor.execute('DROP TABLE teams')
                    cursor.execute('''
                        CREATE TABLE teams (
                            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            api_team_id INTEGER UNIQUE,
                            name TEXT NOT NULL,
                            current_elo_rating REAL NOT NULL DEFAULT 1500.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    # Create index on api_team_id for faster lookups
                    cursor.execute('CREATE INDEX idx_teams_api_id ON teams(api_team_id)')
                    logger.info("Recreated teams table with api_team_id column")

            # Create Matches table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches'")
            matches_table_exists = cursor.fetchone() is not None

            if not matches_table_exists:
                # Create new matches table with api_match_id
                cursor.execute('''
                    CREATE TABLE matches (
                        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_match_id INTEGER UNIQUE,
                        home_team_id INTEGER NOT NULL,
                        away_team_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        home_goals INTEGER NOT NULL,
                        away_goals INTEGER NOT NULL,
                        result INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                        FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
                    )
                ''')
                
                # Add unique constraint for matches without API ID
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS unique_match_constraint 
                    ON matches(date, home_team_id, away_team_id)
                    WHERE api_match_id IS NULL
                ''')
                
                # Add index for faster duplicate checking
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_matches_lookup 
                    ON matches(date, home_team_id, away_team_id)
                ''')
            else:
                # Check if api_match_id column exists
                cursor.execute("PRAGMA table_info(matches)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'api_match_id' not in columns:
                    # Create temporary table with new schema
                    cursor.execute('''
                        CREATE TABLE matches_new (
                            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            api_match_id INTEGER UNIQUE,
                            home_team_id INTEGER NOT NULL,
                            away_team_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            home_goals INTEGER NOT NULL,
                            away_goals INTEGER NOT NULL,
                            result INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                            FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
                        )
                    ''')
                    
                    # Copy data from old table to new table
                    cursor.execute('''
                        INSERT INTO matches_new (
                            match_id, home_team_id, away_team_id, date, 
                            home_goals, away_goals, result, created_at
                        )
                        SELECT match_id, home_team_id, away_team_id, date, 
                               home_goals, away_goals, result, created_at
                        FROM matches
                    ''')
                    
                    # Drop old table and rename new table
                    cursor.execute('DROP TABLE matches')
                    cursor.execute('ALTER TABLE matches_new RENAME TO matches')
            
            # Create system_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check if historical_matches_processed setting exists
            cursor.execute('SELECT value FROM system_settings WHERE key = ?', ('historical_matches_processed',))
            result = cursor.fetchone()
            
            if not result:
                # Initialize the setting to 'false'
                cursor.execute('''
                    INSERT INTO system_settings (key, value)
                    VALUES (?, ?)
                ''', ('historical_matches_processed', 'false'))
                conn.commit()
                
                # Process historical matches if this is a new database and not skipped
                if matches_table_exists and not self.skip_historical_processing:
                    logger.info("New database detected. Processing historical matches...")
                    self.process_historical_matches()
                    self._mark_historical_matches_processed()
            else:
                # Check if historical matches need to be processed
                if result[0] == 'false' and not self.skip_historical_processing:
                    logger.info("Historical matches not processed yet. Processing now...")
                    self.process_historical_matches()
                    self._mark_historical_matches_processed()
                else:
                    logger.info("Historical matches already processed or processing skipped.")
            
            # Create match_predictions table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    home_win_probability REAL NOT NULL,
                    draw_probability REAL NOT NULL,
                    away_win_probability REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(match_id),
                    FOREIGN KEY (match_id) REFERENCES matches(match_id)
                )
            ''')
    
    def _mark_historical_matches_processed(self):
        """Mark historical matches as processed in the system settings."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE system_settings 
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', ('true', 'historical_matches_processed'))
            conn.commit()
            logger.info("Marked historical matches as processed.")
    
    def is_historical_matches_processed(self) -> bool:
        """Check if historical matches have been processed."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM system_settings WHERE key = ?', ('historical_matches_processed',))
            result = cursor.fetchone()
            return result is not None and result[0] == 'true'
    
    def update_elo_ratings(self, match_id: int):
        """Update Elo ratings after a match."""
        K_FACTOR = 30  # K-factor for Elo ratings, updated from 32
        HOME_ADVANTAGE = 70  # Home advantage factor for Elo calculation
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get match details
            cursor.execute('''
                SELECT home_team_id, away_team_id, home_goals, away_goals, result
                FROM matches WHERE match_id = ?
            ''', (match_id,))
            
            match = cursor.fetchone()
            if not match:
                raise ValueError(f"Match with ID {match_id} not found")
            
            home_team_id, away_team_id, home_goals, away_goals, result = match
            
            # Get current Elo ratings
            cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (home_team_id,))
            home_elo = cursor.fetchone()[0]
            
            cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (away_team_id,))
            away_elo = cursor.fetchone()[0]
            
            # Calculate expected scores with home advantage
            home_expected = 1 / (1 + 10 ** ((away_elo - (home_elo + HOME_ADVANTAGE)) / 400))
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
            
            # Update Elo ratings
            new_home_elo = home_elo + K_FACTOR * (home_actual - home_expected)
            new_away_elo = away_elo + K_FACTOR * (away_actual - away_expected)
            
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
            logger.info(f"Updated ELO ratings for match {match_id}: Home {home_elo:.2f} -> {new_home_elo:.2f}, Away {away_elo:.2f} -> {new_away_elo:.2f}")

    def process_historical_matches(self):
        """Process historical matches chronologically and update Elo ratings."""
        with self.connect() as conn:
            cursor = conn.cursor()
            
            try:

                # Initialize all teams with 1500 Elo rating
                cursor.execute('UPDATE teams SET current_elo_rating = 1500.0')
                conn.commit()  # Commit after initialization
                
                # Get all matches ordered by date
                cursor.execute('''
                    SELECT match_id, date 
                    FROM matches 
                    ORDER BY date ASC
                ''')
                
                matches = cursor.fetchall()
                total_matches = len(matches)

                if total_matches == 0:
                   logger.warning("No historical matches found in database. Skipping processing.")
                   return


                
                # Track processed matches to avoid duplicates
                processed_matches = set()

                
                
                for i, (match_id, _) in enumerate(matches):
                    if match_id in processed_matches:
                        logger.warning(f"Skipping duplicate match {match_id}")
                        continue
                        
                    try:
                        self.update_elo_ratings(match_id)
                        processed_matches.add(match_id)
                        
                        if i % 500 == 0:  # Log progress
                            logger.info(f"Processed {i}/{total_matches} matches...")
                            conn.commit()  # Commit periodically
                    except Exception as e:
                        logger.error(f"Error processing match {match_id}: {str(e)}")
                        continue

                cursor.execute('SELECT MAX(date) FROM matches')
                max_date_str = cursor.fetchone()[0]
                if max_date_str:
                    max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
                    self.set_last_fetched_date(max_date)
                else:
                    logger.error("Failed to set last_fetched_date: No matches found")

                conn.commit()  # Final commit
                logger.info(f"Successfully processed {len(processed_matches)} historical matches")

            except Exception as e:
                logger.error(f"Error processing historical matches: {str(e)}")
                conn.rollback()
                raise

    def get_last_fetched_date(self) -> Optional[datetime.date]:
        """Retrieve the last date for which matches were fetched."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM system_settings WHERE key = "last_fetched_date"')
                result = cursor.fetchone()
                if result and result[0]:
                    return datetime.strptime(result[0], '%Y-%m-%d').date()
                return None
        except Exception as e:
            logger.error(f"Error getting last fetched date: {str(e)}")
            return None

    def set_last_fetched_date(self, date: datetime.date):
        """Set the last date for which matches were fetched."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                date_str = date.strftime('%Y-%m-%d')
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings (key, value)
                    VALUES ("last_fetched_date", ?)
                ''', (date_str,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error setting last fetched date: {str(e)}")

    def get_match_features(self, home_team_api_id: int, away_team_api_id: int) -> Dict:
        """Calculate features for match prediction."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, get the database team IDs from API IDs
                cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (home_team_api_id,))
                home_team_result = cursor.fetchone()
                if not home_team_result:
                    logger.error(f"Home team with API ID {home_team_api_id} not found in database")
                    return None
                home_team_id = home_team_result[0]
                
                cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (away_team_api_id,))
                away_team_result = cursor.fetchone()
                if not away_team_result:
                    logger.error(f"Away team with API ID {away_team_api_id} not found in database")
                    return None
                away_team_id = away_team_result[0]
                
                # Get current Elo ratings
                cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (home_team_id,))
                home_elo = cursor.fetchone()[0]
                
                cursor.execute('SELECT current_elo_rating FROM teams WHERE team_id = ?', (away_team_id,))
                away_elo = cursor.fetchone()[0]
                
                # Calculate Elo difference
                elo_difference = home_elo - away_elo
                
                # Get H2H draws in last 5 matches chronologically
                cursor.execute('''
                    WITH h2h_matches AS (
                        SELECT result,
                            ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                        FROM matches
                        WHERE (home_team_id = ? AND away_team_id = ?) OR
                            (home_team_id = ? AND away_team_id = ?)
                    )
                    SELECT COUNT(*) 
                    FROM h2h_matches 
                    WHERE rn <= 5 AND result = 0
                ''', (home_team_id, away_team_id, away_team_id, home_team_id))
                h2h_draws_last_5 = cursor.fetchone()[0] or 0
                
                # Get Average Goal Difference for Home Team (last 5 matches)
                cursor.execute('''
                    WITH home_matches AS (
                        SELECT (home_goals - away_goals) as goal_diff,
                            ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                        FROM matches
                        WHERE home_team_id = ?
                    )
                    SELECT AVG(CAST(goal_diff AS FLOAT))
                    FROM home_matches
                    WHERE rn <= 5
                ''', (home_team_id,))
                result = cursor.fetchone()
                avg_home_gd_last_5 = result[0] if result[0] is not None else 0
                
                # Get Average Goal Difference for Away Team (last 5 matches)
                cursor.execute('''
                    WITH away_matches AS (
                        SELECT (away_goals - home_goals) as goal_diff,
                            ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                        FROM matches
                        WHERE away_team_id = ?
                    )
                    SELECT AVG(CAST(goal_diff AS FLOAT))
                    FROM away_matches
                    WHERE rn <= 5
                ''', (away_team_id,))
                result = cursor.fetchone()
                avg_away_gd_last_5 = result[0] if result[0] is not None else 0
                
                # Get Draw Tendency for Home Team (last 5 matches)
                cursor.execute('''
                    WITH home_matches AS (
                        SELECT result,
                            ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                        FROM matches
                        WHERE home_team_id = ?
                    )
                    SELECT 
                        CAST(SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*), 0) as draw_tendency,
                        COUNT(*) as match_count
                    FROM home_matches
                    WHERE rn <= 5
                ''', (home_team_id,))
                result = cursor.fetchone()
                draw_tendency_home = result[0] if result[0] is not None else 0
                home_matches_count = result[1]
                
                # Get Draw Tendency for Away Team (last 5 matches)
                cursor.execute('''
                    WITH away_matches AS (
                        SELECT result,
                            ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                        FROM matches
                        WHERE away_team_id = ?
                    )
                    SELECT 
                        CAST(SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*), 0) as draw_tendency,
                        COUNT(*) as match_count
                    FROM away_matches
                    WHERE rn <= 5
                ''', (away_team_id,))
                result = cursor.fetchone()
                draw_tendency_away = result[0] if result[0] is not None else 0
                away_matches_count = result[1]
                
                # Log the calculated features with match counts
                logger.info("Calculated features from database:")
                logger.info(f"H2H_Draws_Last_5: {h2h_draws_last_5}")
                logger.info(f"Draw_Tendency_Home: {draw_tendency_home:.3f} (from {home_matches_count} matches)")
                logger.info(f"Draw_Tendency_Away: {draw_tendency_away:.3f} (from {away_matches_count} matches)")
                logger.info(f"Avg_Home_GD_Last_5: {avg_home_gd_last_5:.3f}")
                logger.info(f"Avg_Away_GD_Last_5: {avg_away_gd_last_5:.3f}")
                logger.info(f"Elo_Difference: {elo_difference:.3f}")
                
                # Return dictionary with features in the required order
                return {
                    'Away_Elo': away_elo,
                    'Home_Elo': home_elo,
                    'H2H_Draws_Last_5': h2h_draws_last_5,
                    'Draw_Tendency_Home': draw_tendency_home,
                    'Draw_Tendency_Away': draw_tendency_away,
                    'Avg_Home_GD_Last_5': avg_home_gd_last_5,
                    'Avg_Away_GD_Last_5': avg_away_gd_last_5,
                    'Elo_Difference': elo_difference
                }
            
        except sqlite3.Error as e:
            logger.error(f"Database error in get_match_features: {e}")
            return None
        except Exception as e:
                logger.error(f"Unexpected error in get_match_features: {e}")
                return None

    def add_new_match(self, match_data: Dict):
        """Add a new match to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First, try to find teams by API ID or name
            home_team_api_id = match_data['home_team_id']
            away_team_api_id = match_data['away_team_id']
            home_team_name = match_data.get('home_team_name', f'Team {home_team_api_id}')
            away_team_name = match_data.get('away_team_name', f'Team {away_team_api_id}')
            
            # Try to find home team by API ID first, then by name
            cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (home_team_api_id,))
            home_team_result = cursor.fetchone()
            if not home_team_result:
                # Try to find by name
                cursor.execute('SELECT team_id FROM teams WHERE name = ?', (home_team_name,))
                home_team_result = cursor.fetchone()
                if home_team_result:
                    # Update existing team with API ID
                    cursor.execute('''
                        UPDATE teams 
                        SET api_team_id = ? 
                        WHERE team_id = ?
                    ''', (home_team_api_id, home_team_result[0]))
                    home_team_id = home_team_result[0]
                    logger.info(f"Updated existing team {home_team_name} with API ID {home_team_api_id}")
                else:
                    # Create new team
                    cursor.execute('''
                        INSERT INTO teams (api_team_id, name, current_elo_rating)
                        VALUES (?, ?, 1500.0)
                    ''', (home_team_api_id, home_team_name))
                    home_team_id = cursor.lastrowid
                    logger.info(f"Created new team {home_team_name} with API ID {home_team_api_id}")
            else:
                home_team_id = home_team_result[0]
            
            # Try to find away team by API ID first, then by name
            cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (away_team_api_id,))
            away_team_result = cursor.fetchone()
            if not away_team_result:
                # Try to find by name
                cursor.execute('SELECT team_id FROM teams WHERE name = ?', (away_team_name,))
                away_team_result = cursor.fetchone()
                if away_team_result:
                    # Update existing team with API ID
                    cursor.execute('''
                        UPDATE teams 
                        SET api_team_id = ? 
                        WHERE team_id = ?
                    ''', (away_team_api_id, away_team_result[0]))
                    away_team_id = away_team_result[0]
                    logger.info(f"Updated existing team {away_team_name} with API ID {away_team_api_id}")
                else:
                    # Create new team
                    cursor.execute('''
                        INSERT INTO teams (api_team_id, name, current_elo_rating)
                        VALUES (?, ?, 1500.0)
                    ''', (away_team_api_id, away_team_name))
                    away_team_id = cursor.lastrowid
                    logger.info(f"Created new team {away_team_name} with API ID {away_team_api_id}")
            else:
                away_team_id = away_team_result[0]
            
            # Enhanced duplicate check
            if 'match_id' in match_data:
                # Check for duplicates using API match ID or same teams/date combination
                cursor.execute('''
                    SELECT 
                        m.match_id,
                        m.api_match_id,
                        ht.name as home_team,
                        at.name as away_team,
                        m.date
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.team_id
                    JOIN teams at ON m.away_team_id = at.team_id
                    WHERE 
                        (m.api_match_id = ? AND m.api_match_id IS NOT NULL)
                        OR (
                            m.date = ? 
                            AND m.home_team_id = ? 
                            AND m.away_team_id = ?
                        )
                ''', (
                    match_data['match_id'],  # This is the API match ID
                    match_data['date'],
                    home_team_id,
                    away_team_id
                ))
                
                existing_match = cursor.fetchone()
                if existing_match:
                    match_id, api_match_id, home_team, away_team, match_date = existing_match
                    logger.info(
                        f"Match already exists: ID={match_id}, API_ID={api_match_id}, "
                        f"Date={match_date}, Teams={home_team} vs {away_team}"
                    )
                    return None
            else:
                # For matches without API ID, check only for team/date combination
                cursor.execute('''
                    SELECT 
                        m.match_id,
                        ht.name as home_team,
                        at.name as away_team,
                        m.date
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.team_id
                    JOIN teams at ON m.away_team_id = at.team_id
                    WHERE 
                        m.date = ? 
                        AND m.home_team_id = ? 
                        AND m.away_team_id = ?
                ''', (
                    match_data['date'],
                    home_team_id,
                    away_team_id
                ))
                
                existing_match = cursor.fetchone()
                if existing_match:
                    match_id, home_team, away_team, match_date = existing_match
                    logger.info(
                        f"Match already exists: ID={match_id}, "
                        f"Date={match_date}, Teams={home_team} vs {away_team}"
                    )
                    return None
            
            try:
                cursor.execute('''
                    INSERT INTO matches (
                        api_match_id, home_team_id, away_team_id, date, 
                        home_goals, away_goals, result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_data.get('match_id'),  # This is the API match ID
                    home_team_id,
                    away_team_id,
                    match_data['date'],
                    match_data['home_goals'],
                    match_data['away_goals'],
                    match_data['result']
                ))
                
                match_id = cursor.lastrowid
                conn.commit()
                
                logger.info(
                    f"Added new match: ID={match_id}, API_ID={match_data.get('match_id')}, "
                    f"Teams={match_data.get('home_team_name', f'Team {home_team_api_id}')} vs "
                    f"{match_data.get('away_team_name', f'Team {away_team_api_id}')}, "
                    f"Date={match_data['date']}"
                )
                
                return match_id
                
            except sqlite3.IntegrityError as e:
                logger.error(f"Database integrity error while adding match: {str(e)}")
                return None 


    def get_match_features2(self, home_team_api_id: int, away_team_api_id: int, match_date: Optional[str] = None) -> Dict:

     with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        
        # Map api_team_id to team_id
        cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (home_team_api_id,))
        home_team_result = cursor.fetchone()
        if not home_team_result:
            logger.error(f"Home team with API ID {home_team_api_id} not found")
            return None
        home_team_id = home_team_result[0]
        
        cursor.execute('SELECT team_id FROM teams WHERE api_team_id = ?', (away_team_api_id,))
        away_team_result = cursor.fetchone()
        if not away_team_result:
            logger.error(f"Away team with API ID {away_team_api_id} not found")
            return None
        away_team_id = away_team_result[0]
        
        # Get Elo ratings
        elo_query = 'SELECT current_elo_rating FROM teams WHERE team_id = ?'
        elo_params = (home_team_id,)
        if match_date:
            elo_query += ' AND updated_at < ?'
            elo_params = (home_team_id, match_date)
        cursor.execute(elo_query, elo_params)
        home_elo = cursor.fetchone()[0] if cursor.fetchone() else 1500.0
        
        cursor.execute(elo_query, (away_team_id,) if not match_date else (away_team_id, match_date))
        away_elo = cursor.fetchone()[0] if cursor.fetchone() else 1500.0
        
        elo_difference = home_elo - away_elo
        
        # Get H2H draws in last 5 matches
        h2h_query = '''
            WITH h2h_matches AS (
                SELECT result, ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                FROM matches
                WHERE (home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?)
        '''
        h2h_params = (home_team_id, away_team_id, away_team_id, home_team_id)
        if match_date:
            h2h_query += ' AND date < ?'
            h2h_params += (match_date,)
        h2h_query += '''
            )
            SELECT COUNT(*) FROM h2h_matches WHERE rn <= 5 AND result = 0
        '''
        cursor.execute(h2h_query, h2h_params)
        h2h_draws_last_5 = cursor.fetchone()[0] or 0
        
        # Get Avg Goal Difference for Home Team (last 5 matches)
        home_gd_query = '''
            WITH home_matches AS (
                SELECT (home_goals - away_goals) as goal_diff, ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                FROM matches WHERE home_team_id = ?
        '''
        home_gd_params = (home_team_id,)
        if match_date:
            home_gd_query += ' AND date < ?'
            home_gd_params += (match_date,)
        home_gd_query += '''
            )
            SELECT AVG(CAST(goal_diff AS FLOAT)) FROM home_matches WHERE rn <= 5
        '''
        cursor.execute(home_gd_query, home_gd_params)
        avg_home_gd_last_5 = cursor.fetchone()[0] or 0
        
        # Get Avg Goal Difference for Away Team (last 5 matches)
        away_gd_query = '''
            WITH away_matches AS (
                SELECT (away_goals - home_goals) as goal_diff, ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                FROM matches WHERE away_team_id = ?
        '''
        away_gd_params = (away_team_id,)
        if match_date:
            away_gd_query += ' AND date < ?'
            away_gd_params += (match_date,)
        away_gd_query += '''
            )
            SELECT AVG(CAST(goal_diff AS FLOAT)) FROM away_matches WHERE rn <= 5
        '''
        cursor.execute(away_gd_query, away_gd_params)
        avg_away_gd_last_5 = cursor.fetchone()[0] or 0
        
        # Get Draw Tendency for Home Team (last 5 matches)
        home_draw_query = '''
            WITH home_matches AS (
                SELECT result, ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                FROM matches WHERE home_team_id = ?
        '''
        home_draw_params = (home_team_id,)
        if match_date:
            home_draw_query += ' AND date < ?'
            home_draw_params += (match_date,)
        home_draw_query += '''
            )
            SELECT CAST(SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*), 0), COUNT(*)
            FROM home_matches WHERE rn <= 5
        '''
        cursor.execute(home_draw_query, home_draw_params)
        result = cursor.fetchone()
        draw_tendency_home = result[0] or 0
        home_matches_count = result[1]
        
        # Get Draw Tendency for Away Team (last 5 matches)
        away_draw_query = '''
            WITH away_matches AS (
                SELECT result, ROW_NUMBER() OVER (ORDER BY date DESC) as rn
                FROM matches WHERE away_team_id = ?
        '''
        away_draw_params = (away_team_id,)
        if match_date:
            away_draw_query += ' AND date < ?'
            away_draw_params += (match_date,)
        away_draw_query += '''
            )
            SELECT CAST(SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*), 0), COUNT(*)
            FROM away_matches WHERE rn <= 5
        '''
        cursor.execute(away_draw_query, away_draw_params)
        result = cursor.fetchone()
        draw_tendency_away = result[0] or 0
        away_matches_count = result[1]
        
        logger.info("Calculated features from database:")
        logger.info(f"H2H_Draws_Last_5: {h2h_draws_last_5}")
        logger.info(f"Draw_Tendency_Home: {draw_tendency_home:.3f} (from {home_matches_count} matches)")
        logger.info(f"Draw_Tendency_Away: {draw_tendency_away:.3f} (from {away_matches_count} matches)")
        logger.info(f"Avg_Home_GD_Last_5: {avg_home_gd_last_5:.3f}")
        logger.info(f"Avg_Away_GD_Last_5: {avg_away_gd_last_5:.3f}")
        logger.info(f"Elo_Difference: {elo_difference:.3f}")
        
        return {
            'Away_Elo': away_elo,
            'Home_Elo': home_elo,
            'H2H_Draws_Last_5': h2h_draws_last_5,
            'Draw_Tendency_Home': draw_tendency_home,
            'Draw_Tendency_Away': draw_tendency_away,
            'Avg_Home_GD_Last_5': avg_home_gd_last_5,
            'Avg_Away_GD_Last_5': avg_away_gd_last_5,
            'Elo_Difference': elo_difference
        }
    



    def insert_match_prediction(self, match_id: int, home_win: float, draw: float, away_win: float):
        """Insert a prediction for a match if it doesn't already exist."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO match_predictions (match_id, home_win_probability, draw_probability, away_win_probability)
                VALUES (?, ?, ?, ?)
            ''', (match_id, home_win, draw, away_win))
            conn.commit()

    def get_prediction_for_match(self, match_id: int):
        """Get the stored prediction for a match, or None if not found."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT home_win_probability, draw_probability, away_win_probability
                FROM match_predictions
                WHERE match_id = ?
            ''', (match_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'home_win_probability': row[0],
                    'draw_probability': row[1],
                    'away_win_probability': row[2]
                } 
            return None 