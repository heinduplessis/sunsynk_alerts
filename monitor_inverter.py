# Pulls realtime feed from inverter cloud and sends out sms alerts if critcal
# Based on https://github.com/jamesridgway/sunsynk-api-client
# June 2023, Hein du Plessis

import asyncio
import os
import requests
import json
import os.path
import time
import logging
import urllib.request

from sunsynk.client import SunsynkClient

APP_VERSION='Sunsynk Monitor V0.04'
DEVICE_ID=2 #2 is sunsyk inverter for espresso data

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

#Init enviroment variable holders
SUNSYNK_USER=os.getenv('SUNSYNK_USER')
SUNSYNK_PASS=os.getenv('SUNSYNK_PASS')
BULKSMS_USER=os.getenv('BULKSMS_USER')
BULKSMS_PASS=os.getenv('BULKSMS_PASS')

#Make this True if you need it to run forever
RUN_FOREVER = True

def send_sms(sms_message):
    # HTTP Basic Authentication credentials
    # username = "aerobots"
    # https://api.bulksms.com/v1/messages/send?to=%2b27824616593&body=Hello%20World

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

    response = requests.post(url, data=json_params, headers=headers, auth=(BULKSMS_USER, BULKSMS_PASS))
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
    # sunsynk_username = "hein@aerobots.co.za"
    abort_run=False

    print(APP_VERSION)
    logging.info(APP_VERSION)

    async with SunsynkClient(SUNSYNK_USER, SUNSYNK_PASS) as client:
        inverters = await client.get_inverters()
        for inverter in inverters:
            while not abort_run:
                # logging.info(f"checking... ")
                abort_run = not RUN_FOREVER
                try:
                    grid = await client.get_inverter_realtime_grid(inverter.sn)
                    battery = await client.get_inverter_realtime_battery(inverter.sn)
                    solar_pv = await client.get_inverter_realtime_input(inverter.sn)
                    output_values = await client.get_inverter_realtime_output(inverter.sn)
                    soc=float(battery.soc)
                    pwr=battery.power

                    inverter_status_str=f"Inverter (sn: {inverter.sn}) is drawing {grid.get_power()} W from the grid, {pwr} W from battery and {solar_pv.get_power()} W solar and {output_values.vip} W demand. Battery is at {soc}%"
                    print(f"battery={battery}\n")
                    print(f"solar_pv={solar_pv}\n")
                    print(f"output_values={output_values}\n")
                    url = f"http://wingops.aerobots.co.za:1880/store_Data?device_id={DEVICE_ID}&inverter_sn={inverter.sn}"\
                        f"&grid_power={grid.get_power()}"\
                        f"&battery_power={battery.power}"\
                        f"&solar_pv={pwr}"\
                        f"&battery_soc={soc}"
                    print (f"url={url}")
                    try:
                        contents = urllib.request.urlopen(url).read()
                        print("Response=",contents)
                    except:
                        logging.exception('')
                        print("Critical error with espresso, check log")

                    check_alarm(soc < BATT_SOC_LOW_THRESHOLD,soc >= BATT_SOC_LOW_RESET,BATT_SOC_ALARM_FN,f"INVERTER ALERT! Battery SOC Low: {soc}%. Battery Power: {battery.power} W")
                    check_alarm(soc < BATT_SOC_LOW_CRIT_THRESHOLD,soc >= BATT_SOC_LOW_RESET,BATT_SOC_ALARM_CRITICAL_FN,f"**INVERTER ALERT! Battery SOC CRITICALLY Low: {soc}%. Battery Power: {battery.power} W")
                    check_alarm(pwr > BATT_PWR_HIGH_THRESHOLD,pwr <= BATT_PWR_HIGH_RESET,BATT_PWR_ALARM_FN,f"INVERTER ALERT! Battery Power High: {battery.power} W. SOC: {soc}%")
                    check_alarm(pwr > BATT_PWR_HIGH_CRIT_THRESHOLD,pwr <= BATT_PWR_HIGH_RESET,BATT_PWR_ALARM_CRITICAL_FN,f"**INVERTER ALERT! Battery Power CRITICALLY High: {battery.power} W. SOC: {soc}%")
                except:
                    logging.exception('')
                    print("Critical error, check log")
                if RUN_FOREVER:
                    time.sleep(5*60)
    # send_sms()

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='monitor_inverter.log'
)

#Confirm variables are set
ok_to_go=True
if (SUNSYNK_USER == None) or (SUNSYNK_PASS == None) or (BULKSMS_USER == None) or (BULKSMS_PASS == None):
    print("Please set enviroment variables first (see readme)")
    ok_to_go=False

if ok_to_go:
    print(f"using SUNSYNK_USER={SUNSYNK_USER} and BULKSMS_USER={BULKSMS_USER}")

# ok_to_go=False

if ok_to_go:
    asyncio.run(main())