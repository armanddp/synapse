import asyncio
import configparser
import argparse
from open_gopro import WirelessGoPro, Params, proto, constants

def load_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

async def main(config_file: str) -> None:
    # Load configuration
    config = load_config(config_file)
    
    # Get configuration values
    gopro_ssid = config['GoPro']['gopro_ssid']
    gopro_password = config['GoPro']['gopro_password']
    rtmp_url = config['Stream']['rtmp_url']
    stream_key = config['Stream']['stream_key']
    log_path = config['System']['log_path']

    # Setup logging
    setup_logging(__name__, log_path)
    logger = logging.getLogger(__name__)

    while True:
        try:
            async with WirelessGoPro(gopro_ssid, enable_wifi=False) as gopro:
                # Your existing livestream code here
                # Use rtmp_url and stream_key as needed
                pass

        except Exception as e:
            logger.error(f"An error occurred: {e}. Restarting livestream...")
        
        logger.info("Waiting 10 seconds before restarting...")
        await asyncio.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='GoPro Livestream Service')
    parser.add_argument('--config', required=True, help='Path to config file')
    args = parser.parse_args()
    
    asyncio.run(main(args.config)) 