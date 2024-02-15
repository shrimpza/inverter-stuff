# Inverter Poll

Queries a number of values from a Deye inverter with a Solarman 
"stick logger" device attached, and posts them to an InfluxDB 1.x 
timeseries database.

These values can then be graphed using Grafana, Chronograf, or other
dashboarding software.

Tested with the wifi stick logger protocol only, though should work with
ethernet variation too.

## Usage

Update `poll.py` with your own logger's IP and port, as well as inverter
serial number.

Configure the InfluxDB endpoints and credentials, or remove and replace
with your own data recording implementation.

To run, create a Python virtual environment, activate it, and install 
dependencies:

```
$ python3 -m venv ./poll

$ source ./poll/bin/activate

$ pip install -r requirements.txt
```

Run the poller client:

```
python3 poll.py
```

## References:

Uses Pysolarmanv5: https://github.com/jmccrohan/pysolarmanv5

Registers reference: 
- https://github.com/kellerza/sunsynk/blob/main/src/sunsynk/definitions.py
  - (convert decimal registers to hex for modbus read)
- https://github.com/schwatter/solarman_mqtt/blob/main/Deye_SUN600G3-230-EU_Register.xlsx

Protocol reference:
- https://github.com/jmccrohan/pysolarmanv5/blob/main/pysolarmanv5/pysolarmanv5.py
