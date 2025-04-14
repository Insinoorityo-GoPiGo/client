from easygopigo3 import EasyGoPiGo3
import time
from picamera import PiCamera

gpg = EasyGoPiGo3()
distance_sensor = gpg.init_distance_sensor()
camera = PiCamera()

def take_picture():
    camera.start_preview()
    time.sleep(2)
    camera.capture('/home/pi/Desktop/captured_image.jpg')
    camera.stop_preview()
    print("Picture saved as /home/pi/Desktop/captured_image.jpg")

try:
    while True:
        distance = distance_sensor.read_mm() / 10.0
        #print(f"Distance: {distance} cm")

        if distance <= 15:
            gpg.stop()
            time.sleep(1)
            take_picture()
            break
        else:
            gpg.forward()

        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
    gpg.stop()