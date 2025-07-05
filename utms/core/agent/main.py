import signal
import sys
from utms import UTMSConfig
from utms.core.agent.agent import SchedulerAgent
from utms.core.logger import get_logger

# Initialize components
logger = get_logger()
config = UTMSConfig()
agent = SchedulerAgent(config)

def signal_handler(sig, frame):
    """Gracefully handles shutdown signals like CTRL+C."""
    logger.info(f"Signal {sig} received, shutting down agent...")
    agent.stop()
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
signal.signal(signal.SIGTERM, signal_handler) # Kill command

if __name__ == "__main__":
    logger.info("Starting UTMS Scheduler Agent process...")
    logger.info("Initializing configuration...")
    config = UTMSConfig()

    logger.info("Loading all system components...")
    config.load_all_components() # This is the new, crucial step.
    
    logger.info("Initializing the agent...")
    agent = SchedulerAgent(config)

    try:
        agent.run_blocking()
    except Exception as e:
        logger.critical(f"Scheduler Agent process failed with a critical error: {e}", exc_info=True)
        sys.exit(1)
