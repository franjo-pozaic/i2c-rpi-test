# I2C player

A Python script that reads a file with a time series and sends it via I2C messages to an Arduino.


## Options
```
-f, --file-name: Path to the choreography file. Default is test.
-isa, --i2c-slave-addresses: List of I2C addresses to which the choreography is directed. Default is [1..24].
-v, --value: Set a single value to send to the I2C bus.
-d, --dry-run: Simulate sending I2C messages, only prints to the console. Default is False.
-l, --log: Enable or disable logging to the console. Default is True.
```

Install required dependencies using pip:

```bash
pip install smbus2 gpiozero
```


### Single values
Sends the value 0 to the I2C addresses 1, 2, and 3.

```bash
python player.py -v 0 -isa 1 2 3
```

### Execute a time series
To execute a time series file on all I2C slaves:

```bash
python player.py -f test_file
```

Example
### Dry run

```bash
python player.py -f choreography_file -d
```

### Panic Mode
The panic mode is activated when the button connected to GPIO 4 is released. This will reset all connected devices by sending a 0 value to each I2C address and pausing for 15 seconds.
