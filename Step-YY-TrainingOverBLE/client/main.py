import serial

arduino = serial.Serial('/dev/tty.usbmodemFA141', 115200)
print(arduino.readline())
arduino.write(b'500')
result = arduino.readline()
obs, score, done = result.decode('ascii').rstrip().split(',')
pobs  = 500
obs   = int(obs)
score = int(score)
done  = bool(done)
print(str(pobs+obs), obs, score, done)
arduino.write(str(pobs+obs).encode('ascii'))
print(arduino.readline())