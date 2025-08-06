import os
import sys
from datetime import datetime
from database import Database
from services.model_service import ModelService

# --- CONFIGURATION ---
SEASON_START_MONTH = 8  # August
LIMIT = None  # Set to an integer to limit how many matches to backfill

def main():
    db = Database()
    model_service = ModelService()

    now = datetime.now()
    season_start = datetime(now.year, SEASON_START_MONTH, 1)
    if now.month < SEASON_START_MONTH:
        season_start = datetime(now.year - 1, SEASON_START_MONTH, 1)

    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.match_id, ht.api_team_id, at.api_team_id
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            WHERE m.date >= ? AND m.date < ? AND m.home_goals IS NOT NULL AND m.away_goals IS NOT NULL
            ORDER BY m.date ASC
        ''', (season_start, now))
        matches = cursor.fetchall()

    print(f"Found {len(matches)} matches in current season.")

    count = 0
    for match in matches:
        match_id, home_api_id, away_api_id = match
        # Check if prediction already exists
        if db.get_prediction_for_match(match_id):
            continue

        features = db.get_match_features(home_api_id, away_api_id)
        if not features:
            print(f"Skipping match {match_id}: could not get features.")
            continue

        prepared = model_service.prepare_features(features)
        probs = model_service.predict(prepared)
        db.insert_match_prediction(
            match_id,
            probs['home_win'],
            probs['draw'],
            probs['away_win']
        )
        count += 1
        print(f"Backfilled prediction for match {match_id}")

        if LIMIT and count >= LIMIT:
            breakc

    print(f"Backfilled predictions for {count} matches.")

if __name__ == '__main__':
    main()