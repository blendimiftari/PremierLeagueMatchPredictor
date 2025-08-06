import asyncio
import logging
from scheduler import MatchUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Force an immediate update of matches."""
    try:
        updater = MatchUpdater()
        await updater.force_update()
        logger.info("Match update completed successfully")
    except Exception as e:
        logger.error(f"Error during forced update: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 