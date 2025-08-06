import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from services.football_api import FootballAPIService
from services.model_service import ModelService
from database import Database
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchUpdater:
    def __init__(self, team_mapping_csv: str | Path = "team_mappings.csv"):
        self.db = Database()
        self.football_api = FootballAPIService()
        self.team_mapping = self._load_team_mapping(team_mapping_csv) if team_mapping_csv else {}
        self.max_matchday = 38
        self.chunk_size = 5  # Smaller chunks for rate limits

    def _load_team_mapping(self, csv_path: str | Path) -> Dict[str, str]:
        """Load team name mappings from CSV into a dictionary."""
        try:
            df = pd.read_csv(csv_path)
            mapping = dict(zip(df['api_shortName'], df['database_team_name']))
            logger.info(f"Loaded team name mapping with {len(mapping)} entries")
            return mapping
        except Exception as e:
            logger.error(f"Error loading team name mapping from {csv_path}: {str(e)}")
            return {}

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure datetime is UTC and timezone-aware."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def get_last_match_date(self) -> Optional[datetime]:
        """Get the date of the most recent match in the database."""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(date) FROM matches')
                result = cursor.fetchone()
                if result[0]:
                    try:
                        dt = datetime.strptime(result[0], '%Y-%m-%d')
                    except ValueError:
                        logger.error(f"Invalid date format in matches table: {result[0]}")
                        return None
                    return self._ensure_utc(dt)
                return None
        except Exception as e:
            logger.error(f"Error getting last match date: {str(e)}")
            return None

    async def _get_season_end_date(self) -> datetime:
        """Get the current season's end date from the API."""
        try:
            season_data = await self.football_api._make_request()
            if 'error' in season_data:
                logger.error(f"Failed to fetch season data: {season_data['error']}")
                return datetime.now(timezone.utc)
            logger.debug(f"Season data: {season_data}")
            end_date_str = season_data.get('currentSeason', {}).get('endDate')
            if end_date_str:
                return datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Error getting season end date: {str(e)}")
            return datetime.now(timezone.utc)

    def process_new_matches(self, matches: List[Dict]) -> int:
        """Process new matches and add them to the database."""
        model_service = ModelService()
        added_count = 0
        prediction_count = 0
        for match in matches:
            try:
                if match['status'] != 'FINISHED':
                    logger.info(f"Skipping non-finished match: {match.get('match_id', 'Unknown')} - status: {match['status']}")
                    continue
                
                api_match_id = match['match_id']
                with self.db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'SELECT match_id FROM matches WHERE api_match_id = ?',
                        (api_match_id,)
                    )
                    if cursor.fetchone():
                        logger.debug(f"Match {api_match_id} already exists in database, skipping")
                        continue

                match_date = match['date']
                features = self.db.get_match_features(
                    match['home_team']['id'],
                    match['away_team']['id'],
                    match_date=match_date
                )
                probs = None
                if not features:
                    logger.warning(f"Could not generate features for match {api_match_id}, skipping prediction")
                else:
                    # Generate prediction
                    prepared = model_service.prepare_features(features)
                    probs = model_service.predict(prepared)
                
                if isinstance(match_date, str):
                    try:
                        match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                    except ValueError as e:
                        logger.error(f"Invalid date format for match {api_match_id}: {match_date} - {str(e)}")
                        continue
                match_date = self._ensure_utc(match_date)
                logger.debug(f"Processing match {api_match_id} on {match_date.strftime('%Y-%m-%d')}")

                match_data = {
                    'match_id': api_match_id,  # API match ID
                    'home_team_id': match['home_team']['id'],
                    'away_team_id': match['away_team']['id'],
                    'home_team_name': match['home_team']['name'],
                    'away_team_name': match['away_team']['name'],
                    'date': match_date.strftime('%Y-%m-%d'),  # YYYY-MM-DD for database
                    'home_goals': match['home_goals'] if match['home_goals'] is not None else 0,
                    'away_goals': match['away_goals'] if match['away_goals'] is not None else 0,
                    'result': -1 if match['home_goals'] > match['away_goals']
                             else 0 if match['home_goals'] == match['away_goals']
                             else 1
                }

                match_id = self.db.add_new_match(match_data)
                if match_id:
                    added_count += 1
                    logger.info(f"Added match: {match_data['home_team_name']} vs {match_data['away_team_name']} on {match_data['date']}")

                    if probs:
                        self.db.insert_match_prediction(
                            match_id,
                            probs['home_win'],
                            probs['draw'],
                            probs['away_win'],
                        )
                        prediction_count += 1
                        logger.info(f"Stored prediction for match {match_id}")

                    self.db.update_elo_ratings(match_id)
                    
                else:
                    logger.warning(f"Failed to add match: {match_data['home_team_name']} vs {match_data['away_team_name']}")

            except Exception as e:
                logger.error(f"Error processing match {match.get('match_id', 'Unknown')}: {str(e)}")
                continue

        logger.info(f"Successfully added {added_count} matches and {prediction_count} predictions to the database")
        return added_count

    def _get_date_chunks(self, start_date: datetime, end_date: datetime, chunk_size: int) -> List[tuple[datetime, datetime]]:
        """Split a date range into chunks of specified size."""
        chunks = []
        current_start = start_date
        while current_start < end_date:
            chunk_end = min(current_start + timedelta(days=chunk_size), end_date)
            chunks.append((current_start, chunk_end))
            current_start = chunk_end + timedelta(days=1)
        return chunks

    async def update_matches(self):
        """Update matches from the API, starting from 10 days before the last match in the database."""
        try:
            season_end_date = await self._get_season_end_date()
            now = datetime.now(timezone.utc)  # 2025-06-17 15:02 UTC
            last_match_date = self.get_last_match_date()
            last_fetched_date = self.db.get_last_fetched_date()

            # Force fetch if last_match_date is before season end
            if last_match_date and last_match_date.date() >= season_end_date.date():
                logger.info(f"Last match date {last_match_date.date()} is at or after season end {season_end_date.date()}. No new matches to fetch.")
                self.db.set_last_fetched_date(now.date())
                return
            elif last_match_date:
                logger.info(f"Last match date: {last_match_date.date()}. Checking for missing matches up to {season_end_date.date()}.")
            else:
                logger.info("No matches in database. Fetching from season start.")

            to_date = season_end_date + timedelta(days=1)  
            logger.info(f"Season end date: {season_end_date.date()}. Fetching matches up to {to_date.date()}.")

            if last_match_date:
                from_date = last_match_date - timedelta(days=10)  
                from_date = datetime.combine(from_date.date(), datetime.min.time(), tzinfo=timezone.utc)
            else:
                from_date = datetime(2024, 8, 1, tzinfo=timezone.utc)  # Start of 2024-25 season
                logger.info("Fetching from season start (2024-08-01).")

            if from_date > to_date:
                logger.info(f"From date {from_date.date()} is after to date {to_date.date()}. No matches to fetch.")
                self.db.set_last_fetched_date(now.date())
                return

            logger.info(f"Fetching matches from {from_date.date()} to {to_date.date()}")

            date_chunks = self._get_date_chunks(from_date, to_date, self.chunk_size)
            logger.info(f"Date range split into {len(date_chunks)} chunks")

            all_matches = []
            for chunk_start, chunk_end in date_chunks:
                params = {
                    'dateFrom': chunk_start.strftime('%Y-%m-%d'),
                    'dateTo': chunk_end.strftime('%Y-%m-%d'),
                    'competitions': 'PL',
                    'season': '2024'  # 2024-25 season
                }
                logger.info(f"Fetching matches from {chunk_start.date()} to {chunk_end.date()}")
                try:
                    data = await self.football_api._make_request('matches', params)
                    if 'error' in data:
                        logger.error(f"Failed to fetch matches for {chunk_start.date()} to {chunk_end.date()}: {data['error']}")
                        continue
                    if data and 'matches' in data:
                        matches = data['matches']
                        logger.info(f"Found {len(matches)} matches in range {chunk_start.date()} to {chunk_end.date()}")
                        for match in matches:
                            logger.debug(f"Match: {match['id']} - {match['homeTeam']['name']} vs {match['awayTeam']['name']} - Status: {match['status']} - Date: {match['utcDate']}")
                            home_team_name = self.team_mapping.get(
                                match['homeTeam'].get('shortName', match['homeTeam'].get('name', f"Team {match['homeTeam']['id']}")),
                                match['homeTeam'].get('shortName', f"Team {match['homeTeam']['id']}")
                            )
                            away_team_name = self.team_mapping.get(
                                match['awayTeam'].get('shortName', match['awayTeam'].get('name', f"Team {match['awayTeam']['id']}")),
                                match['awayTeam'].get('shortName', f"Team {match['awayTeam']['id']}")
                            )

                            match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                            match_date = self._ensure_utc(match_date)

                            match_data = {
                                'match_id': match['id'],
                                'date': match_date.strftime('%Y-%m-%d'),  # YYYY-MM-DD
                                'home_team': {
                                    'id': match['homeTeam']['id'],
                                    'name': home_team_name
                                },
                                'away_team': {
                                    'id': match['awayTeam']['id'],
                                    'name': away_team_name
                                },
                                'status': match['status'],
                                'home_goals': match['score']['fullTime']['home'],
                                'away_goals': match['score']['fullTime']['away']
                            }
                            all_matches.append(match_data)
                    else:
                        logger.info(f"No matches returned for range {chunk_start.date()} to {chunk_end.date()}")
                except Exception as e:
                    logger.error(f"Error fetching matches: {str(e)}")
                await asyncio.sleep(6)  # 10 requests/minute = 1 every 6 seconds

            if all_matches:
                added_count = self.process_new_matches(all_matches)
                logger.info(f"Added {added_count} matches to the database")
            else:
                logger.info("No matches found")

            self.db.set_last_fetched_date(now.date())
            logger.info(f"Updated last_fetched_date to {now.date()}")

        except Exception as e:
            logger.error(f"Error updating matches: {str(e)}")
            logger.exception("Full traceback:")

    async def schedule_updates(self, update_interval: int = 1440):
        
        while True:
            try:
               
                await self.update_matches()
                
           
                await asyncio.sleep(60 * 60 * 24)
                
            except Exception as e:
                logger.error(f"Error in update schedule: {str(e)}")
            
                await asyncio.sleep(86400)

if __name__ == "__main__":
    csv_path = "team_mappings.csv" 
    updater = MatchUpdater()
    asyncio.run(updater.schedule_updates()) 