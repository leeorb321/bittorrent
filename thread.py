from threading import Thread
import time

def temp():
    time.sleep(1)
    print("I'm alive")


if __name__ == '__main__':

    t1 = Thread(target=temp)
    t1.start()
