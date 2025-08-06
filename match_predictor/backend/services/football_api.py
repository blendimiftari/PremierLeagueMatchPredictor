import os
import httpx
import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
import aiohttp
import time

load_dotenv()

logger = logging.getLogger(__name__)

class FootballAPIService:
    """Service for interacting with the football-data.org API v4."""
    
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY environment variable is required")
            
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}
        self.premier_league_id = 'PL'
        self.current_matchday = None
        self.last_matchday_update = None
        self.update_interval = timedelta(hours=6)
        self.max_matchday = 38
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        self.max_retries = 3
        self.initial_retry_delay = 5  # Seconds

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the football-data.org API with retry logic for 429 errors."""
        url = f"{self.base_url}/{endpoint}"
        
        full_url = url
        if params:
            query_params = "&".join(f"{k}={v}" for k, v in params.items())
            full_url = f"{url}?{query_params}"
        
        logger.info(f"Making API request to: {full_url}")
        
        headers = {'X-Auth-Token': self.api_key}
        
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        logger.info(f"API Response Status: {response.status}")
                        logger.info(f"Final URL: {response.url}")
                        
                        if response.status == 200:
                            data = await response.json()
                            if endpoint.startswith("matches/") and not params:
                                 logger.info(f"API Response keys: {', '.join(data.keys())}")
                                 return data  

                            elif 'matches' in data:
                                logger.info(f"API Response: Found {len(data['matches'])} matches")
                                if data['matches']:
                                    first_match = data['matches'][0]
                                    logger.info(f"Example match: {first_match.get('id')} - {first_match.get('homeTeam', {}).get('name')} vs {first_match.get('awayTeam', {}).get('name')}")
                            else:
                                logger.info(f"API Response keys: {', '.join(data.keys())}")
                            return data
                        elif response.status == 429:
                            error_text = await response.text()
                            logger.warning(f"Rate limit hit (429) on attempt {attempt + 1}: {error_text}")
                            try:
                                error_data = json.loads(error_text)
                                wait_time = float(error_data.get('message', '').split('Wait ')[1].split(' seconds')[0])
                            except (json.JSONDecodeError, IndexError, ValueError):
                                wait_time = self.initial_retry_delay * (2 ** attempt)
                            wait_time = min(wait_time, 60)  # Cap at 60 seconds
                            logger.info(f"Retrying after {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            logger.error(f"API Error: {response.status} - {error_text}")
                            return {"error": f"API request failed with status {response.status}: {error_text}"}
            except Exception as e:
                logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = self.initial_retry_delay * (2 ** attempt)
                    logger.info(f"Retrying after {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                return {"error": f"Request error after {self.max_retries + 1} attempts: {str(e)}"}
        
        return {"error": f"Failed to complete request after {self.max_retries + 1} attempts"}

    async def initialize(self):
        """Initialize the service and fetch current matchday."""
        try:
            await self.update_current_matchday()
        except Exception as e:
            logger.error(f"Failed to initialize FootballAPIService: {str(e)}")
            raise

    async def update_current_matchday(self) -> None:
        """Fetch and update the current matchday, capping at 38."""
        try:
            now = datetime.now(timezone.utc)    
            if (self.last_matchday_update and 
                now - self.last_matchday_update < self.update_interval and 
                self.current_matchday is not None):
                logger.info(f"Using cached matchday: {self.current_matchday}")
                return

            data = await self._make_request(f'competitions/{self.premier_league_id}')
            if 'error' in data:
                logger.error(f"Failed to fetch competition data: {data['error']}")
                raise ValueError("Failed to fetch competition data")
            
            logger.debug(f"Season data: {data}")
            end_date = datetime.strptime(data['currentSeason']['endDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if now > end_date:
                logger.info(f"Season ended on {end_date.date()}. Setting matchday to 38.")
                self.current_matchday = 38
                self.last_matchday_update = now
                return

            api_matchday = min(data['currentSeason']['currentMatchday'], self.max_matchday)
            logger.info(f"API reported matchday: {api_matchday}")

            matches_for_current = await self._get_matches_for_matchday(api_matchday)
            if matches_for_current:
                logger.info(f"Found {len(matches_for_current)} matches for matchday {api_matchday}")
                self.current_matchday = api_matchday
            else:
                logger.warning(f"No upcoming matches found for matchday {api_matchday}")
                self.current_matchday = api_matchday

            self.last_matchday_update = now
            logger.info(f"Updated current matchday to: {self.current_matchday}")
        except Exception as e:
            logger.error(f"Error updating current matchday: {str(e)}")
            if self.current_matchday is None:
                raise

    async def _get_matches_for_matchday(self, matchday: int) -> List[Dict]:
        """Helper method to get upcoming matches for a specific matchday."""
        try:
            data = await self._make_request(f'competitions/{self.premier_league_id}/matches', {
                'matchday': matchday,
                'status': 'SCHEDULED,TIMED,POSTPONED'
            })
            
            matches = data.get('matches', [])
            logger.info(f"Found {len(matches)} upcoming matches for matchday {matchday}")
            return matches
        except Exception as e:
            logger.error(f"Error fetching matches for matchday {matchday}: {str(e)}")
            return []

    def get_current_matchday(self) -> int:
        """Get the current matchday with caching."""
        if self.current_matchday is None:
            raise ValueError("FootballAPIService not properly initialized")
        return self.current_matchday

    async def get_upcoming_fixtures(self, matchday: Optional[int] = None) -> List[Dict]:
        """Get upcoming Premier League fixtures for a specific matchday."""
        try:
            if matchday is None:
                await self.update_current_matchday()
                matchday = self.get_current_matchday()
            
            logger.info(f"Getting fixtures for matchday {matchday}")

            data = await self._make_request(f'competitions/{self.premier_league_id}')
            if 'error' in data:
                logger.error(f"Failed to fetch competition data: {data['error']}")
                return []
                
            end_date = datetime.strptime(data['currentSeason']['endDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > end_date:
                logger.info(f"Season ended on {end_date.date()}. No upcoming fixtures available.")
                return []

            params = {
                'matchday': min(matchday, self.max_matchday),
                'status': 'SCHEDULED,TIMED,POSTPONED'
            }
            
            data = await self._make_request(f'competitions/{self.premier_league_id}/matches', params)
            all_matches = data.get('matches', []) if 'matches' in data else []
            logger.debug(f"Full matches: {all_matches}")
            
            logger.info(f"Found {len(all_matches)} total upcoming matches for matchday {matchday}")
            
            if not all_matches:
                logger.warning(f"No upcoming matches found for matchday {matchday}")
                return []
                
            matches = []
            for match in all_matches:
                match_data = {
                    'match_id': match['id'],
                    'date': datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00')),
                    'home_team': {
                        'id': match['homeTeam']['id'],
                        'name': match['homeTeam'].get('name') or match['homeTeam'].get('shortName', 'Unknown Team'),
                        'crest': match['homeTeam'].get('crest')
                    },
                    'away_team': {
                        'id': match['awayTeam']['id'],
                        'name': match['awayTeam'].get('name') or match['awayTeam'].get('shortName', 'Unknown Team'),
                        'crest': match['awayTeam'].get('crest')
                    },
                    'status': match['status'],
                    'venue': match.get('venue', 'TBD'),
                    'matchday': match.get('matchday'),
                    'competition': {
                        'id': match['competition']['id'],
                        'name': match['competition']['name'],
                        'code': match['competition']['code'],
                        'emblem': match['competition'].get('emblem')
                    },
                    'season': {
                        'id': match['season']['id'],
                        'startDate': match['season']['startDate'],
                        'endDate': match['season']['endDate'],
                        'currentMatchday': match['season']['currentMatchday']
                    }
                }
                matches.append(match_data)
            
            matches.sort(key=lambda x: x['date'])
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting upcoming fixtures: {str(e)}")
            return []

    async def get_match_by_id(self, match_id: int) -> Dict:
        """Get match details by match ID."""
        try:
            data = await self._make_request(f'matches/{match_id}')
            return data
        except Exception as e:
            logger.error(f"Error fetching match by ID: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()