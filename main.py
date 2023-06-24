import asyncio
import os

from sunsynk.client import SunsynkClient


async def main():
    sunsynk_username = "hein@aerobots.co.za"
    sunsynk_password = "wwwSunsynk"

    async with SunsynkClient(sunsynk_username, sunsynk_password) as client:
        inverters = await client.get_inverters()
        for inverter in inverters:
            grid = await client.get_inverter_realtime_grid(inverter.sn)
            battery = await client.get_inverter_realtime_battery(inverter.sn)
            solar_pv = await client.get_inverter_realtime_input(inverter.sn)
            demand = await client.get_inverter_realtime_output(inverter.sn)

            await client.get_inverter_realtime_output(inverter.sn)

            print(f"Inverter (sn: {inverter.sn}) is drawing {grid.get_power()} W from the grid, {battery.power} W from battery and {solar_pv.get_power()} W solar and {demand.pac} W demand. Battery is at {battery.soc}%")

    print('Done!')

asyncio.run(main())