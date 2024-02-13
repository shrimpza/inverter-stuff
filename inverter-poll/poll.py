from pysolarmanv5 import PySolarmanV5
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import schedule
import time

import urllib.request
from urllib.parse import urlencode
import base64

influx_url = 'https://your.influxdb.host/'
influx_database = 'power'
influx_retention_policy = 'autogen'
influx_bucket = f'{influx_database}/{influx_retention_policy}'

influx = InfluxDBClient(url=influx_url, token='username:password', org='-')
write_api = influx.write_api(write_options=SYNCHRONOUS)

polling_interval = 40 # in seconds

def main():
    inverters = [
        {
            'name': "home",        # friendly name
            'host': "192.168.0.2", # IP/hostname of logger device
            'port': 8899,          # query port of logger device
            'serial': 000000000    # serial number of inverter
        }
    ]

    for i in inverters:
        query_inverter(i['host'], i['port'], i['serial'], i['name'])

def query_inverter(host, port, serial, name):
    print(f'Query inverter {name} serial {serial} at {host}:{port}', flush=True)
    try:
        modbus = PySolarmanV5(host, serial, port=port, mb_slave_id=0x01, socket_timeout=10, verbose=False)

        ###### Usage
        Batt_Temp = get_sensor_temp(modbus.read_holding_registers(0xB6, 0x01))
        Batt_Power = get_sensor_signed(modbus.read_holding_registers(0xBE, 0x01), 1)
        Batt_SOC = get_sensor(modbus.read_holding_registers(0xB8, 0x01), 1)
        Load = get_sensor_signed(modbus.read_holding_registers(0xB2, 0x01), 1)
        Inverter = get_sensor_signed(modbus.read_holding_registers(0xAF, 0x01), 1)
        Grid_In = get_sensor_signed(modbus.read_holding_registers(0xA9, 0x01), 1)
        Grid_Status = get_sensor(modbus.read_holding_registers(0xC2, 0x01), 1)
        Solar1_In = get_sensor_signed(modbus.read_holding_registers(0xBA, 0x01), 1)
        Solar2_In = get_sensor_signed(modbus.read_holding_registers(0xBB, 0x01), 1)

        ###### Day totals
        Day_Grid_In = get_sensor(modbus.read_holding_registers(0x4C, 0x01), 1)
        Day_Solar_In = get_sensor(modbus.read_holding_registers(0x6C, 0x01), 1)
        Day_Load = get_sensor(modbus.read_holding_registers(0x54, 0x01), 1)

        ###### Temperatures
        Transformer_Temp = get_sensor_temp(modbus.read_holding_registers(0x5A, 0x01))
        Radiator_Temp = get_sensor_temp(modbus.read_holding_registers(0x5B, 0x01))

        modbus.disconnect()

        # gather values as influxdb points
        points = [
            Point("inverter").tag("name", name).field("State", "Online"),
            Point("inverter").tag("name", name).field("Error", "-"),
            Point("inverter").tag("name", name).field("Batt_Temp", Batt_Temp),
            Point("inverter").tag("name", name).field("Batt_Power", Batt_Power),
            Point("inverter").tag("name", name).field("Batt_SOC", Batt_SOC),
            Point("inverter").tag("name", name).field("Load", Load),
            Point("inverter").tag("name", name).field("Inverter", Inverter),
            Point("inverter").tag("name", name).field("Grid_In", Grid_In),
            Point("inverter").tag("name", name).field("Grid_Status", Grid_Status),
            Point("inverter").tag("name", name).field("Day_Grid_In", Day_Grid_In),
            Point("inverter").tag("name", name).field("Solar1_In", Solar1_In),
            Point("inverter").tag("name", name).field("Solar2_In", Solar2_In),
            Point("inverter").tag("name", name).field("Day_Solar_In", Day_Solar_In),
            Point("inverter").tag("name", name).field("Day_Load", Day_Load),
            Point("inverter").tag("name", name).field("Transformer_Temp", Transformer_Temp),
            Point("inverter").tag("name", name).field("Radiator_Temp", Radiator_Temp)
        ]

        # useful for debugging
        for i in points:
            print(i.to_line_protocol())

        # write influxdb values
        write_api.write(bucket=influx_bucket, record=points)

        print("Query and submit success", flush=True)

    except Exception as e:
        print("Data collection or submission failed")
        print(e, flush=True)

def get_sensor(value, scale = 0.1):
    return int(value[0]) * scale

def get_sensor_signed(value, scale = 0.1):
    val = get_sensor(value, scale)
    return val if val <= 0x7FFF else val - 0xFFFF

def get_sensor_temp(value):
    return round(int(value[0]) * 0.1 - 100, 2)

if __name__ == "__main__":
    schedule.every(polling_interval).seconds.do(main)
    main()
    while True:
        schedule.run_pending()
        time.sleep(1)
