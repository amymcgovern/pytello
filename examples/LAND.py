# Emergency landing - sends the land command a bunch of times just to ensure it lands

from pytello.Tello import Tello

tello = Tello()

tello.connect()

tello.land()
tello.land()
tello.land()
tello.land()
tello.land()

print("Done - disconnecting")
tello.disconnect()
