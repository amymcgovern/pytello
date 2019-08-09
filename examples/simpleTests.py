from pytello.Tello import Tello

tello = Tello()

success = tello.connect()

if (success):
    # tello.takeoff()
    #
    # print("Sleeping")
    # tello.sleep(3)
    #
    # print("Trying to land")
    # tello.land()

    print("Success")
    tello.sleep(5)

tello.disconnect()