import os
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'


import os
import sys
import asyncio
from open_gopro import WirelessGoPro, Params
from open_gopro.constants import ActionId
from open_gopro.proto import EnumWindowSize, EnumLens
from open_gopro.exceptions import ConnectFailed


WirelessGoPro.CONNECT_TIMEOUT = 30  # Increase connection timeout to 30 seconds

URL = "rtmp://raspberrypi.local:1935/live/gopro"

# Add these constants at the top of your script
WIFI_SSID = "The Matterhorn Bivacco"
WIFI_PASSWORD = "ismoresecure!"

async def main():
    print("Connecting to GoPro...")
    try:
        async with WirelessGoPro() as gopro:
            print("Connected to GoPro via BLE")

            # Connect to the main WiFi network
            print(f"Connecting to WiFi network: {WIFI_SSID}")
            if await gopro.connect_to_access_point(WIFI_SSID, WIFI_PASSWORD):
                print("Successfully connected to WiFi network")
            else:
                print("Failed to connect to WiFi network")
                return

           # Confiuring the 

            # Set up livestream
            print("Setting up livestream...")
            response = await gopro.ble_command.set_livestream_mode(
                url=URL,
                window_size=EnumWindowSize.WINDOW_SIZE_720,
                lens=EnumLens.LENS_WIDE,
                minimum_bitrate=1000000,
                maximum_bitrate=2000000,
                starting_bitrate=1500000
            )
            print(f"Livestream setup response: {response}")

            if not response.ok:
                print("Failed to set up livestream")
                return

            # Start livestream
            print("Starting livestream...")
            shutter_response = await gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
            if not shutter_response.ok:
                print("Failed to start livestream")
                return

            print("Livestream started successfully")

            # Keep the script running and periodically check status
            try:
                while True:
                    stream_status = await gopro.ble_command.get_livestream_status()
                    print(f"Livestream status: {stream_status}")
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("Stopping livestream...")
                await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)

    except ConnectFailed as e:
        print(f"Connection failed: {e}")
        print("Make sure the GoPro is nearby and Bluetooth is enabled.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges.")
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)
    
    asyncio.run(main())
