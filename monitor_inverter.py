import asyncio
import os
import requests
import json
import os.path
import time

from sunsynk.client import SunsynkClient

#https://api.bulksms.com/v1/messages/send?to=%2b27824616593&body=Hello%20World
#aerobots / wwwBulksms1

BATT_SOC_LOW_THRESHOLD=50
BATT_SOC_LOW_CRIT_THRESHOLD=20
BATT_SOC_LOW_RESET=60

BATT_PWR_HIGH_THRESHOLD=5000
BATT_PWR_HIGH_CRIT_THRESHOLD=9000
BATT_PWR_HIGH_RESET=3000

BATT_SOC_ALARM_FN="battery_soc_alarm.sig"
BATT_SOC_ALARM_CRITICAL_FN="battery_soc_alarm_critical.sig"
BATT_PWR_ALARM_FN="battery_pwr_alarm.sig"
BATT_PWR_ALARM_CRITICAL_FN="battery_pwr_alarm_critical.sig"

infinite_loop = False

def send_sms(sms_message):
    # HTTP Basic Authentication credentials
    username = "aerobots"
    password = "wwwBulksms1"

    # API endpoint URL
    url = "https://api.bulksms.com/v1/messages"

    # Set the headers to specify the content type as JSON
    headers = {
        "Content-Type": "application/json"
    }
    # JSON parameters
    params = {
        "to": "+27824616593",
        "body": sms_message
    }
    # Convert the parameters to JSON format
    json_params = json.dumps(params)

    response = requests.post(url, data=json_params, headers=headers, auth=(username, password))
    # Check the response status code
    if response.status_code in (200,201):
        # Request was successful
        result = response.json()
        print(result)
    else:
        # Request failed
        print("Error:", response.status_code)

def check_alarm(condition_alarm, condition_reset, sig_file, msg):
    if condition_alarm:
        if not (os.path.isfile(sig_file)):
            print(msg)
            send_sms(msg)
            open(sig_file, 'a').close()
        else: #Create signal file
            print("Not alerting - file exists")

    if condition_reset and os.path.isfile(sig_file):
        os.remove(sig_file)
        print(f"Alarm reset ({sig_file})")

async def main():
    sunsynk_username = "hein@aerobots.co.za"
    sunsynk_password = "wwwSunsynk"
    check_count=0

    async with SunsynkClient(sunsynk_username, sunsynk_password) as client:
        inverters = await client.get_inverters()
        for inverter in inverters:
            while infinite_loop:
                check_count=check_count+1
                print(f"{check_count} checking... ",end="\r")
                grid = await client.get_inverter_realtime_grid(inverter.sn)
                battery = await client.get_inverter_realtime_battery(inverter.sn)
                solar_pv = await client.get_inverter_realtime_input(inverter.sn)
                output_values = await client.get_inverter_realtime_output(inverter.sn)

                inverter_status_str=f"Inverter (sn: {inverter.sn}) is drawing {grid.get_power()} W from the grid, {battery.power} W from battery and {solar_pv.get_power()} W solar and {output_values.vip} W demand. Battery is at {battery.soc}%"
                # print(f"battery={battery}\n")
                # print(f"solar_pv={solar_pv}\n")
                # print(f"output_values={output_values}\n")

                soc=float(battery.soc)
                pwr=battery.power
                #Check for low battery
                print(f"{check_count} check done",end="\r")

                check_alarm(soc < BATT_SOC_LOW_THRESHOLD,soc >= BATT_SOC_LOW_RESET,BATT_SOC_ALARM_FN,f"INVERTER ALERT! Battery SOC Low: {soc}%. Battery Power: {battery.power} W")
                check_alarm(soc < BATT_SOC_LOW_CRIT_THRESHOLD,soc >= BATT_SOC_LOW_RESET,BATT_SOC_ALARM_CRITICAL_FN,f"**INVERTER ALERT! Battery SOC CRITICALLY Low: {soc}%. Battery Power: {battery.power} W")
                check_alarm(pwr > BATT_PWR_HIGH_THRESHOLD,pwr <= BATT_PWR_HIGH_RESET,BATT_PWR_ALARM_FN,f"INVERTER ALERT! Battery Power High: {battery.power} W. SOC: {soc}%")
                check_alarm(pwr > BATT_PWR_HIGH_CRIT_THRESHOLD,pwr <= BATT_PWR_HIGH_RESET,BATT_PWR_ALARM_CRITICAL_FN,f"**INVERTER ALERT! Battery Power CRITICALLY High: {battery.power} W. SOC: {soc}%")

                print(f"{check_count} check done",end="\r")

                time.sleep(5*60)
    # send_sms()

asyncio.run(main())