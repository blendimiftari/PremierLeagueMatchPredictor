import pandas as pd
from database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_teams():
    """List all teams in the database with their IDs and ELO ratings."""
    try:
        # Initialize database connection without processing historical matches
        db = Database(skip_historical_processing=True)
        
        # Get all teams from the database
        teams = db.get_all_teams()
        
        if not teams:
            logger.info("No teams found in the database.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(teams)
        
        # Reorder columns for better readability
        columns = ['team_id', 'name', 'elo_rating',]
        df = df[columns]
        
        # Rename columns for display
        df.columns = ['Team ID', 'Team Name', 'ELO Rating']
        
        # Display teams
        print("\n=== Teams in Database ===")
        print(df.to_string(index=False))
        print(f"\nTotal teams: {len(teams)}")
        
    except Exception as e:
        logger.error(f"Error listing teams: {str(e)}")
        raise

if __name__ == "__main__":
    list_teams() 