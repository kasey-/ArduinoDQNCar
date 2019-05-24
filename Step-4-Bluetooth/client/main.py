import serial

ser = serial.Serial('/dev/tty.HC-06-DevB', 115200, timeout=1)
ser.write(b'This is sent from python')
ser.close()