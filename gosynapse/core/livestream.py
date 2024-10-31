import os
import asyncio
import configparser
from pathlib import Path
from typing import Optional, Any
from rich.console import Console
import logging
from open_gopro import WirelessGoPro
from open_gopro.api import Params
from open_gopro.constants import ActionId
from open_gopro import proto
from enum import Enum

console = Console()

DEFAULT_CONFIG_PATHS = [
    '/etc/gopro-synapse/config.ini',
    os.path.expanduser('~/.config/gopro-synapse/config.ini'),
    'config.ini'
]

class FOV(Enum):
    WIDE = proto.EnumLens.LENS_WIDE
    LINEAR = proto.EnumLens.LENS_LINEAR
    SUPERVIEW = proto.EnumLens.LENS_SUPERVIEW

class GoProLivestream:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: Optional[str]) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        
        # Try specified config path first
        if config_path and Path(config_path).exists():
            config.read(config_path)
            return config
            
        # Try default locations
        for path in DEFAULT_CONFIG_PATHS:
            if Path(path).exists():
                config.read(path)
                return config
                
        raise FileNotFoundError("No config file found")

    def _get_resolution_value(self, res_string: str) -> proto.EnumWindowSize:
        """Convert resolution string to GoPro API enum"""
        res_map = {
            "1080p": proto.EnumWindowSize.WINDOW_SIZE_1080,
            "720p": proto.EnumWindowSize.WINDOW_SIZE_720,
            "480p": proto.EnumWindowSize.WINDOW_SIZE_480
        }
        try:
            return res_map[res_string.lower()]
        except KeyError:
            self.logger.warning(f"Invalid resolution value: {res_string}, defaulting to 1080p")
            return proto.EnumWindowSize.WINDOW_SIZE_1080

    def _get_fov_value(self, fov_string: str) -> proto.EnumLens:
        """Convert FOV string to GoPro API enum"""
        try:
            return getattr(proto.EnumLens, f"LENS_{fov_string.upper()}")
        except AttributeError:
            self.logger.warning(f"Invalid FOV value: {fov_string}, defaulting to WIDE")
            return proto.EnumLens.LENS_WIDE

    async def start_livestream(self):
        try:
            identifier = self.config['GoPro'].get('gopro_identifier', None)
            async with WirelessGoPro(identifier, enable_wifi=False) as gopro:
                # Configure stream settings
                resolution = self._get_resolution_value(self.config['Stream']['resolution'])
                fov = self._get_fov_value(self.config['Stream']['fov'])
                
                await gopro.ble_command.set_livestream_mode(
                    url=self.config['Stream']['rtmp_url'],
                    window_size=resolution,
                    minimum_bitrate=self.config['Stream'].getint('min_bitrate'),
                    maximum_bitrate=self.config['Stream'].getint('max_bitrate'),
                    starting_bitrate=self.config['Stream'].getint('start_bitrate'),
                    lens=fov,
                )

                await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
                await gopro.ble_command.register_livestream_status(
                    register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
                )

                console.print(f"[yellow]Connecting to {self.config['WiFi']['wifi_ssid']}...")
                await gopro.connect_to_access_point(
                    self.config['WiFi']['wifi_ssid'],
                    self.config['WiFi']['wifi_password']
                )

                # Start livestream
                livestream_is_ready = asyncio.Event()

                async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
                    if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
                        livestream_is_ready.set()

                console.print("[yellow]Configuring livestream...")
                gopro.register_update(wait_for_livestream_start, ActionId.LIVESTREAM_STATUS_NOTIF)

                # Monitor livestream status
                async def monitor_livestream_status(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
                    if update.live_stream_status != proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_STREAMING:
                        if update.live_stream_error == proto.EnumLiveStreamError.LIVE_STREAM_ERROR_OSNETWORK:
                            self.logger.error("Network error detected. Restarting livestream...")
                            raise Exception("Network error, restarting livestream")
                        elif update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_FAILED_STAY_ON:
                            self.logger.error("Livestream failed. Restarting...")
                            raise Exception("Livestream failed, restarting")

                gopro.register_update(monitor_livestream_status, ActionId.LIVESTREAM_STATUS_NOTIF)

                while True:
                    await asyncio.sleep(10)

        except Exception as e:
            self.logger.error(f"An error occurred: {e}. Restarting livestream...")
            
            self.logger.info("Waiting 10 seconds before restarting...")
            await asyncio.sleep(10) 