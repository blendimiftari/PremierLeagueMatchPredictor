import asyncio
import logging
from services.football_api import FootballAPIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_matchday_logic():
    """Test the matchday progression logic."""
    try:
        # Initialize API service
        api = FootballAPIService()
        await api.initialize()
        
        # Get current matchday
        current_matchday = api.get_current_matchday()
        logger.info(f"Initial current matchday: {current_matchday}")
        
        # Get matches for current matchday
        matches = await api._make_request(f'competitions/PL/matches', {
            'matchday': current_matchday
        })
        
        if 'matches' in matches:
            logger.info(f"Found {len(matches['matches'])} matches for matchday {current_matchday}")
            
            # Display match statuses
            for match in matches['matches']:
                home_team = match['homeTeam'].get('name', match['homeTeam'].get('shortName', 'Unknown'))
                away_team = match['awayTeam'].get('name', match['awayTeam'].get('shortName', 'Unknown'))
                status = match['status']
                logger.info(f"{home_team} vs {away_team} - Status: {status}")
            
            # Check if all matches are finished
            all_finished = all(match['status'] == 'FINISHED' for match in matches['matches'])
            logger.info(f"All matches finished: {all_finished}")
            
            if all_finished:
                # Get next scheduled match
                next_matches = await api._make_request('matches', {
                    'competitions': 'PL',
                    'status': 'SCHEDULED',
                    'limit': 1
                })
                
                if 'matches' in next_matches and next_matches['matches']:
                    next_match = next_matches['matches'][0]
                    next_matchday = next_match['matchday']
                    home_team = next_match['homeTeam'].get('name', next_match['homeTeam'].get('shortName', 'Unknown'))
                    away_team = next_match['awayTeam'].get('name', next_match['awayTeam'].get('shortName', 'Unknown'))
                    match_date = next_match['utcDate']
                    
                    logger.info(f"\nNext scheduled match:")
                    logger.info(f"Matchday: {next_matchday}")
                    logger.info(f"Match: {home_team} vs {away_team}")
                    logger.info(f"Date: {match_date}")
                else:
                    logger.info("No scheduled matches found")
        else:
            logger.error("No matches found in API response")
        
        # Force update matchday
        await api.update_current_matchday()
        updated_matchday = api.get_current_matchday()
        logger.info(f"\nFinal current matchday after update: {updated_matchday}")
        
    except Exception as e:
        logger.error(f"Error testing matchday logic: {str(e)}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(test_matchday_logic()) 