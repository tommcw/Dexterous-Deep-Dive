import serial

PORT = "COM3"

ser = serial.Serial(
    port=PORT,
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1,
)

print("Connected to", ser.port)
print("Is open:", ser.is_open)

ser.close()
