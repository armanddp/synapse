import asyncio
import argparse
import logging
from gosynapse.core.livestream import GoProLivestream

def setup_logging(log_path: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='GoPro Livestream Service')
    parser.add_argument('--config', help='Path to config file')
    args = parser.parse_args()

    try:
        livestream = GoProLivestream(args.config)
        setup_logging(livestream.config['System']['log_path'])
        asyncio.run(livestream.start_livestream())
    except Exception as e:
        print(f"Failed to start livestream: {e}")
        exit(1)

if __name__ == "__main__":
    main()
