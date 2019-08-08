from Tello import Tello
import time

tello = Tello()

tello.connect()

tello.land()
tello.land()
tello.land()
tello.land()
tello.land()

print("Done - disconnecting")
tello.disconnect()
