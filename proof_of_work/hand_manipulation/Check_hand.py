import serial
import time

ser = serial.Serial(
    port="COM3",
    baudrate=9600,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=1,
)

print("Connected to COM3")

# Read HAND_ID register (address 1000)
request = bytes([
    0xEB,
    0x90,
    0x01,       # Hand ID
    0x04,       # Frame data length
    0x11,       # Read register
    0xE8,       # Address low byte
    0x03,       # Address high byte
    0x01,       # Read 1 byte
    0x16,       # Checksum
])

print("TX:", request.hex(" "))

ser.write(request)
ser.flush()

time.sleep(0.05)

response = ser.read(100)

print("RX:", response.hex(" "))

ser.close()
