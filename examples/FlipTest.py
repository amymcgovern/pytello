from pytello.Tello import Tello

tello = Tello()

tello.connect()

tello.takeoff()
tello.sleep(8)
print("flipping")
tello.flip("left", 3)
tello.flip("right", 3)
tello.flip("forward", 3)
tello.flip("backward", 3)


tello.land()

tello.disconnect()