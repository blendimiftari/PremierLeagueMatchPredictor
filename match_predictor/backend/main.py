from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from database import Database
from fastapi import BackgroundTasks
from services.football_api import FootballAPIService
from services.model_service import ModelService
from scheduler import MatchUpdater

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Premier League Match Predictor")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
football_api = FootballAPIService()
model_service = ModelService()
match_updater = MatchUpdater()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(match_updater.schedule_updates())
    try:
        await football_api.initialize()
        logger.info("FootballAPIService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await football_api.close()
    logger.info("FootballAPIService client closed")

class MatchData(BaseModel):
    home_team_id: int
    away_team_id: int
    date: datetime
    home_goals: int
    away_goals: int
    result: int

class PredictionRequest(BaseModel):
    home_team_id: int
    away_team_id: int

class PredictionResponse(BaseModel):
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    features: Dict

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Premier League Match Predictor",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/predict/", response_model=PredictionResponse)
async def predict_match_new(request: PredictionRequest):
    """Get match prediction and features."""
    try:
        features = db.get_match_features(request.home_team_id, request.away_team_id)
        if features is None:
            raise HTTPException(
                status_code=404,
                detail="One or both teams not found in database. Make sure teams exist and try again."
            )
        preparedFeatures = model_service.prepare_features(features)
        probabilities = model_service.predict(preparedFeatures)

       
        with db.connect() as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            cursor.execute('''
                SELECT match_id FROM matches
                WHERE home_team_id = (SELECT team_id FROM teams WHERE api_team_id = ?)
                  AND away_team_id = (SELECT team_id FROM teams WHERE api_team_id = ?)
                  AND date >= ?
                ORDER BY date ASC LIMIT 1
            ''', (request.home_team_id, request.away_team_id, today))
            row = cursor.fetchone()
            if row:
                match_id = row[0]
                db.insert_match_prediction(
                    match_id,
                    probabilities['home_win'],
                    probabilities['draw'],
                    probabilities['away_win']
                )

        return PredictionResponse(
            home_win_probability=probabilities['home_win'],
            draw_probability=probabilities['draw'],
            away_win_probability=probabilities['away_win'],
            features=features
        )
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
async def get_results(offset: int = 0, limit: int = 20):
    """Get past matches for the current season, including stored model predictions, paginated."""
    try:
        # Get the current season start date (assume August 1st of this year)
        now = datetime.now()
        season_start = datetime(now.year, 8, 1)
        if now.month < 8:
            season_start = datetime(now.year - 1, 8, 1)
        
        with db.connect() as conn:
            cursor = conn.cursor()
            # Get total count for pagination
            cursor.execute('''
                SELECT COUNT(*) FROM matches
                WHERE date >= ? AND date < ? AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            ''', (season_start, now))
            total = cursor.fetchone()[0]
            # Get paginated results
            cursor.execute('''
                SELECT m.match_id, m.date, ht.name, at.name, m.home_goals, m.away_goals
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.team_id
                JOIN teams at ON m.away_team_id = at.team_id
                WHERE m.date >= ? AND m.date < ? AND m.home_goals IS NOT NULL AND m.away_goals IS NOT NULL
                ORDER BY m.date DESC
                LIMIT ? OFFSET ?
            ''', (season_start, now, limit, offset))
            matches = cursor.fetchall()
        
        results = []
        for match in matches:
            match_id, date, home_team, away_team, home_goals, away_goals = match
            prediction = db.get_prediction_for_match(match_id)
            results.append({
                'match_id': match_id,
                'date': date,
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'prediction': prediction
            })
        return {
            'total': total,
            'results': results
        }
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# def _get_date_chunks(start_date: datetime, end_date: datetime, chunk_size: int = 10) -> List[tuple[datetime, datetime]]:
#     """Split a date range into chunks of specified size."""
#     chunks = []
#     current_date = start_date
#     while current_date < end_date:
#         chunk_end = min(current_date + timedelta(days=chunk_size-1), end_date)
#         chunks.append((current_date, chunk_end))
#         current_date = chunk_end + timedelta(days=1)
#     return chunks

# async def update_matches():
#     """Background task to update matches from API-Football."""
#     try:
#         current_date = datetime.now()
#         from_date = current_date - timedelta(days=7)
#         logger.info(f"Fetching matches from {from_date.strftime('%Y-%m-%d')}")
        
#         all_matches = []
#         date_chunks = _get_date_chunks(from_date, current_date)
        
#         for chunk_start, chunk_end in date_chunks:
#             logger.info(f"Fetching chunk from {chunk_start.date()} to {chunk_end.date()}")
#             params = {
#                 'dateFrom': chunk_start.strftime('%Y-%m-%d'),
#                 'dateTo': chunk_end.strftime('%Y-%m-%d'),
#                 'competitions': 'PL',
#                 'status': 'FINISHED'
#             }
#             try:
#                 data = await football_api._make_request('matches', params)
#                 for match in data.get('matches', []):
#                     match_data = {
#                         'match_id': match['id'],
#                         'home_team': {
#                             'id': match['homeTeam']['id'],
#                             'name': match['homeTeam'].get('shortName') 
#                         },
#                         'away_team': {
#                             'id': match['awayTeam']['id'],
#                             'name': match['awayTeam'].get('shortName') 
#                         },
#                         'date': datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00')),
#                         'home_goals': match['score']['fullTime']['home'],
#                         'away_goals': match['score']['fullTime']['away'],
#                         'status': match['status']
#                     }
#                     all_matches.append(match_data)
#             except Exception as e:
#                 logger.error(f"Error fetching chunk {chunk_start.date()} to {chunk_end.date()}: {str(e)}")
#                 continue
#             await asyncio.sleep(1)
            
#         logger.info(f"Retrieved {len(all_matches)} matches from API")
        
#         match_count = 0
#         prediction_count = 0
#         for match in all_matches:
#             try:
#                 with db.connect() as conn:
#                     cursor = conn.cursor()
#                     cursor.execute('SELECT match_id FROM matches WHERE match_id = ?', (match['match_id'],))
#                     if cursor.fetchone():
#                         logger.info(f"Match {match['match_id']} already exists, skipping")
#                         continue


                
#                  # Generate features using data up to match date
#                 match_date = match['date'].strftime('%Y-%m-%d')
#                 features = db.get_match_features(
#                     match['home_team']['id'],
#                     match['away_team']['id'],
#                     match_date=match_date
#                 )
#                 if not features:
#                     logger.warning(f"Could not generate features for match {match['match_id']}, skipping prediction")
#                 else:
#                     # Generate prediction
#                     prepared = model_service.prepare_features(features)
#                     probs = model_service.predict(prepared)


#                 match_data = {
#                     'match_id': match['match_id'],
#                     'home_team_id': match['home_team']['id'],
#                     'home_team_name': match['home_team']['shortName'],
#                     'away_team_id': match['away_team']['id'],
#                     'away_team_name': match['away_team']['shortName'],
#                     'date': match['date'],
#                     'home_goals': match['home_goals'],
#                     'away_goals': match['away_goals'],
#                     'result': -1 if match['home_goals'] > match['away_goals'] else 0 if match['home_goals'] == match['away_goals'] else 1
#                 }

#                 db_match_id = db.add_new_match(match_data)
#                 if db_match_id:
#                     match_count += 1
#                     logger.info(f"Added match {match['match_id']}: {match_data['home_team_name']} vs {match_data['away_team_name']}")
                    
#                     # Store prediction if generated
#                     if features:
#                         db.insert_match_prediction(
#                             db_match_id,
#                             probs['home_win'],
#                             probs['draw'],
#                             probs['away_win']
#                         )
#                         prediction_count += 1
#                         logger.info(f"Stored prediction for match {db_match_id}")
                    
#                     # Update Elo ratings
#                     db.update_elo_ratings(db_match_id)


#             except Exception as e:
#                 logger.error(f"Error processing match {match['match_id']}: {str(e)}")
#                 continue
        
#         logger.info(f"Successfully added {match_count} new matches and {prediction_count} predictions to the database")
        
#     except Exception as e:
#         logger.error(f"Error updating matches: {str(e)}")
#         raise

@app.get("/fixtures/upcoming")
async def get_upcoming_fixtures(matchday: Optional[int] = None):
    """
    Get upcoming fixtures for the current or specified matchday.
    If matchday is not provided, uses the current matchday from the cached value.
    """
    try:
        # If matchday not specified, ensure current_matchday is up-to-date
        if matchday is None:
            await football_api.update_current_matchday()
            current_matchday = football_api.get_current_matchday()
            logger.info(f"Using current matchday: {current_matchday}")
        else:
            current_matchday = matchday
            logger.info(f"Using specified matchday: {current_matchday}")
        
        # Fetch fixtures using the pre-fetched or specified matchday
        fixtures = await football_api.get_upcoming_fixtures(matchday)
        
        if not fixtures:
            logger.warning(f"No fixtures found for matchday {current_matchday}")
            return {
                "status": "success",
                "data": {
                    "fixtures": [],
                    "matchday": current_matchday
                }
            }

        # Transform to a format matching the expected frontend format
        formatted_fixtures = []
        for match in fixtures:
            try:
                formatted_match = {
                    'match_id': match['match_id'],
                    'home_team_id': match['home_team']['id'],
                    'home_team_name': match['home_team']['name'],
                    'home_team_crest': match['home_team'].get('crest', ''),
                    'away_team_id': match['away_team']['id'],
                    'away_team_name': match['away_team']['name'],
                    'away_team_crest': match['away_team'].get('crest', ''),
                    'date': match['date'].isoformat() if isinstance(match['date'], datetime) else match['date'],
                    'status': match['status'],
                    'venue': match.get('venue', 'TBD'),
                    'matchday': match.get('matchday')
                }
                
                # Add competition details if available
                if 'competition' in match:
                    formatted_match['competition'] = match['competition']
                
                formatted_fixtures.append(formatted_match)
            except Exception as e:
                logger.error(f"Error formatting match: {match}. Error: {str(e)}")
                continue
        
        # Sort by date
        formatted_fixtures.sort(key=lambda x: x['date'])
        
        logger.info(f"Returning {len(formatted_fixtures)} formatted fixtures for matchday {current_matchday}")
        
        return {
            "status": "success",
            "data": {
                "fixtures": formatted_fixtures,
                "matchday": current_matchday
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming fixtures: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch upcoming fixtures"
        )
    

@app.get("/match/{match_id}")
async def get_match_by_id(match_id: int):
    """Get match details by match ID."""
    try:
        match = await football_api.get_match_by_id(match_id)
        return match
    except Exception as e:
        logger.error(f"Error fetching match by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
