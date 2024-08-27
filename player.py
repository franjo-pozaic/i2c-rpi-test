from smbus2 import SMBus, i2c_msg
import contextlib
import time
import argparse
from gpiozero import Button

button = Button(4) # 

I2C_ADDRESSES = list(range(1,25))
RESET_WAIT_TIME = 15
CLOCK_PERIOD = 0.06
MIDDLE_POSITION = 4000

parser = argparse.ArgumentParser(prog = 'Choreograph', \
    description = 'Reads a chorepgraphy file and sends I2C messages to Arduino', \
    formatter_class=argparse.RawDescriptionHelpFormatter, \
    epilog='''
Example usage
*************

Send value 0 to addresses 1 2 3: python player.py -v 0 -isa 1 2 3

Read chorepgraphy file test_file and send to all slaves: python player.py -f test_file''')
parser.add_argument('-f', '--file-name', default='test', help='Path to the choregraphy file')
parser.add_argument('-isa', '--i2c-slave-addresses', nargs="+", type=int, default=I2C_ADDRESSES, help='List I2C addesses to which a choreography is directed (default=[1..24])')
parser.add_argument('-v', '--value', default=None, type=int, help='Set to send a single value to the I2C bus')
parser.add_argument('-d', '--dry-run', default=False, action=argparse.BooleanOptionalAction, help='Avoids sending I2C messages, only prints to console (default=False)')
parser.add_argument('-l', '--log', default=True, action=argparse.BooleanOptionalAction, help='Allow logging to console (default=True)')

args = parser.parse_args()

def is_panic_activated():
    return not button.is_pressed

def generate_positions_with_value(value):
    return list(map(lambda _: bytewise(value), args.i2c_slave_addresses))

def log(string):
    if args.log:
        print(string)

def bytewise(num):
    l = []
    while num:
        l.append(num & 0xFF)
        num = num >> 8
    if (len(l) == 1):
        l.insert(0, 0)
    elif len(l) == 0:
        l.insert(0, 0)
        l.insert(0, 0)
    l.reverse()
    return l

def start(sm_bus, send_positions):
    time_series = []
    # opens the choreography file and creates a time series array
    # the array consists of 2 byte tuples
    with open(args.file_name) as file:
        for line in file:
            numbers_strings = line.split(';')[0:len(args.i2c_slave_addresses)]
            numbers = list(map(int, numbers_strings))
            byte_tuples = list(map(bytewise, numbers))
            time_series.append(byte_tuples)

    with sm_bus(1) as bus:
        while 1:
            for positions in time_series:
                time.sleep(CLOCK_PERIOD)
                if is_panic_activated():
                    log('Reset (panic)')
                    reset_positions = generate_positions_with_value(0)
                    send_positions(bus, reset_positions)
                    time.sleep(RESET_WAIT_TIME)
                    break
                    
                send_positions(bus, positions)
                if is_reset_stage(positions):
                    log('Reset (regular)')
                    time.sleep(RESET_WAIT_TIME)
       
def is_reset_stage(positions):
    return positions[0][0] == 0 and positions[0][1] == 0
    
@contextlib.contextmanager
def SMBusStub(x):
    yield 0

def send_bytes_impl(bus, addr, value):
    log(f'{value} > {addr}')
    high = value[0]
    low = value[1]
    try:
        bus.write_byte_data(addr, high, low)
    except Exception as e:
        print(f'Failed to write to address {addr}: {e}')

def send_positions_stub(bus, positions):
    out = ''
    for idx, addr in enumerate(args.i2c_slave_addresses):
        out = out + str(positions[idx]).rjust(5)
    log(out)
    
MIDDLE_POSITION_BYTES = bytewise(MIDDLE_POSITION)

def send_positions_impl(bus, positions):
    for idx, addr in enumerate(args.i2c_slave_addresses):
        if positions[idx] != MIDDLE_POSITION_BYTES:
            send_bytes_impl(bus, addr, positions[idx])

send_positions = send_positions_stub if args.dry_run else send_positions_impl
sm_bus = SMBusStub if args.dry_run else SMBus
         
if args.value != None:
    with SMBus(1) as bus:
        positions = generate_positions_with_value(args.value)
        log(f'Sending position {args.value} to I2C addresses {args.i2c_slave_addresses}')
        send_positions_impl(bus, positions)
else:     
    start(sm_bus, send_positions)