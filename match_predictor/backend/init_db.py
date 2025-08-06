import pandas as pd
import logging
from database import Database
import os
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_historical_data(csv_path: str):
    """Import historical match data from CSV file and initialize ELO ratings."""
    try:
        logger.info("Reading CSV file...")
        df = pd.read_csv(csv_path)
        
        # Initialize database
        db = Database()
        
        with db.connect() as conn:
            logger.info("Clearing existing data...")
            cursor = conn.cursor()
            cursor.execute('DELETE FROM matches')
            cursor.execute('DELETE FROM teams')
            cursor.execute('DELETE FROM system_settings')
            conn.commit()
            
            logger.info("Processing teams...")
            # Get unique teams
            teams_df = pd.concat([
                df[['HomeTeam']].rename(columns={'HomeTeam': 'name'}),
                df[['AwayTeam']].rename(columns={'AwayTeam': 'name'})
            ]).drop_duplicates()
            
            # Insert teams
            teams_df.to_sql('teams', conn, if_exists='append', index=False)
            
            # Get team IDs mapping
            team_ids = pd.read_sql('SELECT team_id, name FROM teams', conn)
            team_id_map = dict(zip(team_ids['name'], team_ids['team_id']))
            
            logger.info("Processing dates...")
            # Convert dates to datetime and format for SQLite
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
            
            logger.info("Preparing matches data...")
            # Prepare matches data
            matches_df = pd.DataFrame({
                'home_team_id': df['HomeTeam'].map(team_id_map),
                'away_team_id': df['AwayTeam'].map(team_id_map),
                'date': df['Date'].dt.strftime('%Y-%m-%d'),  # Format dates as YYYY-MM-DD for SQLite
                'home_goals': df['FTHG'],
                'away_goals': df['FTAG'],
                'result': df['FTR'].map({'H': -1, 'D': 0, 'A': 1})
            })
            
            logger.info("Inserting matches...")
            # Insert matches
            matches_df.to_sql('matches', conn, if_exists='append', index=False)
            
            logger.info(f"Successfully imported {len(matches_df)} matches and {len(teams_df)} teams")
            
            # Initialize system settings
            cursor.execute('''
                INSERT INTO system_settings (key, value)
                VALUES (?, ?)
            ''', ('historical_matches_processed', 'false'))
            conn.commit()
            
            logger.info("Database initialized with historical data. ELO ratings will be calculated on next startup.")
            
    except Exception as e:
        logger.error(f"Error importing historical data: {str(e)}")
        raise

def recreate_match_predictions_table(db_path="premier_league.db"):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Drop the table if it exists
        cursor.execute('DROP TABLE IF EXISTS match_predictions;')
        # Recreate with the correct schema
        cursor.execute('''
            CREATE TABLE match_predictions (
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
        conn.commit()
        print("match_predictions table dropped and recreated with correct schema.")

if __name__ == "__main__":
    # Check if historical data file exists
    csv_path = "historical-data.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Historical data file {csv_path} not found.")
        exit(1)
        
    # Import historical data
    import_historical_data(csv_path)
    
    # Initialize database to trigger ELO calculation
    db = Database()
    logger.info("Database initialization complete. ELO ratings have been calculated.")

    # Recreate match predictions table
    recreate_match_predictions_table() 