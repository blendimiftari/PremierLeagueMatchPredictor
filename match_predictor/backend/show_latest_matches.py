import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys
import argparse

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import Database

def show_match_by_api_id(api_match_id):
    """
    Display a match with the given API match ID.
    
    Args:
        api_match_id: The API match ID to search for
    """
    db = Database()
    
    try:
        with db.connect() as conn:
            # Query to get the match with the given API match ID
            query = """
            SELECT 
                m.match_id,
                m.api_match_id,
                m.date,
                ht.name AS home_team,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,
                m.result,
                ht.current_elo_rating AS home_elo,
                at.current_elo_rating AS away_elo,
                ht.current_elo_rating - at.current_elo_rating AS elo_difference,
                m.created_at
            FROM 
                matches m
            JOIN 
                teams ht ON m.home_team_id = ht.team_id
            JOIN 
                teams at ON m.away_team_id = at.team_id
            WHERE
                m.api_match_id = ?
            """
            
            # Execute the query and load results into a DataFrame
            df = pd.read_sql_query(query, conn, params=(api_match_id,))
            
            if df.empty:
                print(f"No match found with API match ID: {api_match_id}")
                return
            
            # Format the date columns
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the result column
            df['result'] = df['result'].map({-1: 'Home Win', 0: 'Draw', 1: 'Away Win'})
            
            # Format ELO ratings to 1 decimal place
            df['home_elo'] = df['home_elo'].round(1)
            df['away_elo'] = df['away_elo'].round(1)
            df['elo_difference'] = df['elo_difference'].round(1)
            
            # Add a column for the score
            df['score'] = df['home_goals'].astype(str) + ' - ' + df['away_goals'].astype(str)
            
            # Display the match information
            print(f"\nMATCH WITH API ID {api_match_id}:")
            print("=" * 100)
            print(f"Match ID: {df['match_id'].iloc[0]}")
            print(f"API Match ID: {df['api_match_id'].iloc[0]}")
            print(f"Date: {df['date'].iloc[0]}")
            print(f"Home Team: {df['home_team'].iloc[0]} (ELO: {df['home_elo'].iloc[0]})")
            print(f"Away Team: {df['away_team'].iloc[0]} (ELO: {df['away_elo'].iloc[0]})")
            print(f"Score: {df['score'].iloc[0]}")
            print(f"Result: {df['result'].iloc[0]}")
            print(f"ELO Difference: {df['elo_difference'].iloc[0]}")
            print(f"Added to Database: {df['created_at'].iloc[0]}")
            print("=" * 100)
            
            # Check if ELO prediction matched the result
            elo_diff = df['elo_difference'].iloc[0]
            result = df['result'].iloc[0]
            
            prediction_correct = False
            if (elo_diff > 0 and result == 'Home Win') or \
               (elo_diff < 0 and result == 'Away Win') or \
               (abs(elo_diff) < 50 and result == 'Draw'):
                prediction_correct = True
            
            print(f"ELO Prediction: {'Correct' if prediction_correct else 'Incorrect'}")
            
    except Exception as e:
        print(f"Error retrieving match: {str(e)}")

def show_last_match():
    """
    Display the last match that was inserted into the database with detailed information.
    """
    db = Database()
    
    try:
        with db.connect() as conn:
            # Query to get the last match with team names and ELO ratings
            query = """
            SELECT 
                m.match_id,
                m.api_match_id,
                m.date,
                ht.name AS home_team,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,
                m.result,
                ht.current_elo_rating AS home_elo,
                at.current_elo_rating AS away_elo,
                ht.current_elo_rating - at.current_elo_rating AS elo_difference,
                m.created_at
            FROM 
                matches m
            JOIN 
                teams ht ON m.home_team_id = ht.team_id
            JOIN 
                teams at ON m.away_team_id = at.team_id
            ORDER BY 
                m.match_id DESC
            LIMIT 1
            """
            
            # Execute the query and load results into a DataFrame
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print("No matches found in the database.")
                return
            
            # Format the date columns
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the result column
            df['result'] = df['result'].map({-1: 'Home Win', 0: 'Draw', 1: 'Away Win'})
            
            # Format ELO ratings to 1 decimal place
            df['home_elo'] = df['home_elo'].round(1)
            df['away_elo'] = df['away_elo'].round(1)
            df['elo_difference'] = df['elo_difference'].round(1)
            
            # Add a column for the score
            df['score'] = df['home_goals'].astype(str) + ' - ' + df['away_goals'].astype(str)
            
            # Display the match information
            print("\nLAST MATCH IN DATABASE:")
            print("=" * 100)
            print(f"Match ID: {df['match_id'].iloc[0]}")
            print(f"API Match ID: {df['api_match_id'].iloc[0]}")
            print(f"Date: {df['date'].iloc[0]}")
            print(f"Home Team: {df['home_team'].iloc[0]} (ELO: {df['home_elo'].iloc[0]})")
            print(f"Away Team: {df['away_team'].iloc[0]} (ELO: {df['away_elo'].iloc[0]})")
            print(f"Score: {df['score'].iloc[0]}")
            print(f"Result: {df['result'].iloc[0]}")
            print(f"ELO Difference: {df['elo_difference'].iloc[0]}")
            print(f"Added to Database: {df['created_at'].iloc[0]}")
            print("=" * 100)
            
            # Check if ELO prediction matched the result
            elo_diff = df['elo_difference'].iloc[0]
            result = df['result'].iloc[0]
            
            prediction_correct = False
            if (elo_diff > 0 and result == 'Home Win') or \
               (elo_diff < 0 and result == 'Away Win') or \
               (abs(elo_diff) < 50 and result == 'Draw'):
                prediction_correct = True
            
            print(f"ELO Prediction: {'Correct' if prediction_correct else 'Incorrect'}")
            
    except Exception as e:
        print(f"Error retrieving last match: {str(e)}")

def show_latest_matches(limit=20):
    """
    Display the latest matches from the database with detailed information.
    
    Args:
        limit: Number of matches to display (default: 20)
    """
    db = Database()
    
    try:
        with db.connect() as conn:
            # Query to get the latest matches with team names, ELO ratings, and API Match ID
            query = """
            SELECT 
                m.match_id,
                m.api_match_id,
                m.date,
                ht.name AS home_team,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,
                m.result,
                ht.current_elo_rating AS home_elo,
                at.current_elo_rating AS away_elo,
                ht.current_elo_rating - at.current_elo_rating AS elo_difference
            FROM 
                matches m
            JOIN 
                teams ht ON m.home_team_id = ht.team_id
            JOIN 
                teams at ON m.away_team_id = at.team_id
            ORDER BY 
                m.date DESC, m.match_id DESC
            LIMIT ?
            """
            
            # Execute the query and load results into a DataFrame
            df = pd.read_sql_query(query, conn, params=(limit,))
            
            if df.empty:
                print("No matches found in the database.")
                return
            
            # Format the date column
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Format the result column
            df['result'] = df['result'].map({-1: 'Home Win', 0: 'Draw', 1: 'Away Win'})
            
            # Format ELO ratings to 1 decimal place
            df['home_elo'] = df['home_elo'].round(1)
            df['away_elo'] = df['away_elo'].round(1)
            df['elo_difference'] = df['elo_difference'].round(1)
            
            # Add a column for the score
            df['score'] = df['home_goals'].astype(str) + ' - ' + df['away_goals'].astype(str)
            
            # Reorder columns for better display, including API Match ID
            display_df = df[[
                'date', 'api_match_id', 'home_team', 'away_team', 'score', 'result', 
                'home_elo', 'away_elo', 'elo_difference'
            ]]
            
            # Rename columns for better readability
            display_df.columns = [
                'Date', 'API Match ID', 'Home Team', 'Away Team', 'Score', 'Result', 
                'Home ELO', 'Away ELO', 'ELO Diff'
            ]
            
            # Display the DataFrame
            print(f"\nLatest {len(display_df)} matches in the database:")
            print("=" * 100)
            print(display_df.to_string(index=False))
            print("=" * 100)
            
            # Print summary statistics
            print("\nMatch Result Distribution:")
            result_counts = df['result'].value_counts()
            for result, count in result_counts.items():
                print(f"  {result}: {count} ({count/len(df)*100:.1f}%)")
            
            # Print ELO statistics
            print("\nELO Rating Statistics:")
            print(f"  Average Home ELO: {df['home_elo'].mean():.1f}")
            print(f"  Average Away ELO: {df['away_elo'].mean():.1f}")
            print(f"  Average ELO Difference: {df['elo_difference'].mean():.1f}")
            
            # Check if ELO predictions match results
            correct_predictions = 0
            for _, row in df.iterrows():
                elo_diff = row['elo_difference']
                result = row['result']
                
                if (elo_diff > 0 and result == 'Home Win') or \
                   (elo_diff < 0 and result == 'Away Win') or \
                   (abs(elo_diff) < 50 and result == 'Draw'):
                    correct_predictions += 1
            
            print(f"\nELO Prediction Accuracy: {correct_predictions}/{len(df)} ({correct_predictions/len(df)*100:.1f}%)")
            
    except Exception as e:
        print(f"Error retrieving matches: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display match information from the database")
    parser.add_argument("--last", action="store_true", help="Show only the last match in the database")
    parser.add_argument("--latest", type=int, nargs="?", const=20, help="Show the latest N matches (default: 20)")
    parser.add_argument("--api-id", type=int, help="Show match with specific API match ID")
    
    args = parser.parse_args()
    
    if args.api_id:
        show_match_by_api_id(args.api_id)
    elif args.latest:
        show_latest_matches(args.latest)
    else:
        # Default to showing the last match
        show_last_match() 