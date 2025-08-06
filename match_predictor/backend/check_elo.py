import sqlite3
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_elo_calculations():
    """Diagnostic function to check ELO rating calculations."""
    try:
        # Connect to database
        conn = sqlite3.connect("premier_league.db")
        cursor = conn.cursor()
        
        # 1. Check for duplicate matches
        cursor.execute('''
            SELECT date, home_team_id, away_team_id, COUNT(*) as count
            FROM matches
            GROUP BY date, home_team_id, away_team_id
            HAVING count > 1
        ''')
        duplicates = cursor.fetchall()
        if duplicates:
            logger.warning("Found duplicate matches:")
            for dup in duplicates:
                logger.warning(f"Date: {dup[0]}, Home: {dup[1]}, Away: {dup[2]}, Count: {dup[3]}")
        
        # 2. Check match results distribution
        cursor.execute('''
            SELECT result, COUNT(*) as count
            FROM matches
            GROUP BY result
        ''')
        results = cursor.fetchall()
        logger.info("\nMatch Results Distribution:")
        for result, count in results:
            result_type = "Home Win" if result == -1 else "Draw" if result == 0 else "Away Win"
            logger.info(f"{result_type}: {count} matches")
        
        # 3. Get current ELO ratings
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
        
        # 4. Check for potential ELO calculation issues
        cursor.execute('''
            SELECT m.date, 
                   ht.name as home_team, 
                   at.name as away_team,
                   m.home_goals,
                   m.away_goals,
                   m.result,
                   ht.current_elo_rating as home_elo,
                   at.current_elo_rating as away_elo
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            ORDER BY m.date DESC
            LIMIT 10
        ''')
        recent_matches = cursor.fetchall()
        
        logger.info("\nRecent Matches and ELO Ratings:")
        for match in recent_matches:
            date, home_team, away_team, home_goals, away_goals, result, home_elo, away_elo = match
            result_type = "Home Win" if result == -1 else "Draw" if result == 0 else "Away Win"
            logger.info(f"\n{date}: {home_team} {home_goals}-{away_goals} {away_team}")
            logger.info(f"Result: {result_type}")
            logger.info(f"Home ELO: {home_elo:.2f}, Away ELO: {away_elo:.2f}")
            logger.info(f"ELO Difference: {home_elo - away_elo:.2f}")
        
    except Exception as e:
        logger.error(f"Error checking ELO calculations: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    check_elo_calculations() 