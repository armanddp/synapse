import argparse
import asyncio
import logging
from typing import Any

from rich.console import Console

from open_gopro import Params, WirelessGoPro, constants, proto
from open_gopro.logger import setup_logging
from open_gopro.util import add_cli_args_and_parse, ainput

console = Console()

async def main(args: argparse.Namespace) -> None:
    setup_logging(__name__, args.log)
    logger = logging.getLogger(__name__)

    while True:  # Outer loop for restarting
        try:
            async with WirelessGoPro(args.identifier, enable_wifi=False) as gopro:
                await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
                await gopro.ble_command.register_livestream_status(
                    register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
                )

                console.print(f"[yellow]Connecting to {args.ssid}...")
                await gopro.connect_to_access_point(args.ssid, args.password)

                # Start livestream
                livestream_is_ready = asyncio.Event()

                async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
                    if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
                        livestream_is_ready.set()

                console.print("[yellow]Configuring livestream...")
                gopro.register_update(wait_for_livestream_start, constants.ActionId.LIVESTREAM_STATUS_NOTIF)
                await gopro.ble_command.set_livestream_mode(
                    url=args.url,
                    window_size=args.resolution,
                    minimum_bitrate=args.min_bit,
                    maximum_bitrate=args.max_bit,
                    starting_bitrate=args.start_bit,
                    lens=args.fov,
                )

                # Wait to receive livestream started status
                console.print("[yellow]Waiting for livestream to be ready...\n")
                await asyncio.wait_for(livestream_is_ready.wait(), timeout=30)  # Add a timeout

                console.print("[yellow]Starting livestream")
                await gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)

                console.print("[yellow]Livestream is now streaming and should be available for viewing.")
                
                # Monitor livestream status
                async def monitor_livestream_status(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
                    if update.live_stream_status != proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_STREAMING:
                        logger.warning(f"Livestream status changed: {update.live_stream_status}")
                        if update.live_stream_error == proto.EnumLiveStreamError.LIVE_STREAM_ERROR_OSNETWORK:
                            logger.error("Network error detected. Restarting livestream...")
                            raise Exception("Network error, restarting livestream")
                        elif update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_FAILED_STAY_ON:
                            logger.error("Livestream failed. Restarting...")
                            raise Exception("Livestream failed, restarting")

                gopro.register_update(monitor_livestream_status, constants.ActionId.LIVESTREAM_STATUS_NOTIF)

                # Keep the main coroutine running
                while True:
                    await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"An error occurred: {e}. Restarting livestream...")
        finally:
            if 'gopro' in locals():
                try:
                    await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
                    await gopro.ble_command.release_network()
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")
            
        logger.info("Waiting 10 seconds before restarting...")
        await asyncio.sleep(10)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a GoPro livestream with auto-restart capability.")
    parser.add_argument("--ssid", type=str, help="WiFi SSID to connect to.", default="gopro2")
    parser.add_argument("--password", type=str, help="Password of WiFi SSID.", default="gopro123")
    parser.add_argument("--url", type=str, help="RTMP server URL to stream to.", default="rtmp://192.168.8.17/live/gopro2")
    parser.add_argument("--min_bit", type=int, help="Minimum bitrate.", default=1000)
    parser.add_argument("--max_bit", type=int, help="Maximum bitrate.", default=5500)
    parser.add_argument("--start_bit", type=int, help="Starting bitrate.", default=5000)
    parser.add_argument(
        "--resolution", help="Resolution.", choices=list(proto.EnumWindowSize.values()), default=proto.EnumWindowSize.WINDOW_SIZE_1080, type=int
    )
    parser.add_argument(
        "--fov", help="Field of View.", choices=list(proto.EnumLens.values()), default=proto.EnumLens.LENS_SUPERVIEW, type=int
    )
    return add_cli_args_and_parse(parser, wifi=False)

def entrypoint() -> None:
    asyncio.run(main(parse_arguments()))

if __name__ == "__main__":
    entrypoint()
