from multiprocessing import Process, Lock


def func1(lock):

    print('func1: starting')
    for i in range(10000):
        if i % 1000 == 0:
            lock.acquire()
            print("STUFF")
            lock.release()
    print('func1: finishing')


def func2():
    print('func2: starting')
    for i in range(10000000):
        pass #print('F2')
    print('func2: finishing')

def func3(lock):

    print('func3: starting')
    for i in range(10000):
        if i % 1000 == 0:
            lock.acquire()
            print("3STUFF")
            lock.release()
    print('func3: finishing')

if __name__ == '__main__':
    lock = Lock()
    p1 = Process(target=func1, args=(lock,))
    p1.start()
    p2 = Process(target=func3, args=(lock,))
    p2.start()
    p1.join()
    p2.join()
