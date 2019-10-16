import numpy as np
import threading
import queue

def loadGlove(filepath):
    gloveMap = {}

    with open(filepath) as fp:
        for line in fp:
            parsedLine = line.split(" ")
            gloveMap[parsedLine[0]] = np.array(parsedLine[1:]).astype(np.float)
    return gloveMap

## often much slower because of join
def threadedLoadGlove(filepath):
    numThreads = 8

    def worker():
        gloveMap = {}
        while True:
            line = q.get()
            if line is None:
                retQ.put(gloveMap)
                break
            parsedLine = line.split(" ")
            gloveMap[parsedLine[0]] = np.array(parsedLine[1:]).astype(np.float)
            q.task_done()

    q = queue.Queue()
    retQ = queue.Queue()

    threads = []
    for i in range(numThreads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    with open(filepath) as fp:
        for line in fp:
            q.put(line)

    # block until all tasks are done
    q.join()

    # stop workers
    for i in range(numThreads):
        q.put(None)

    for t in threads:
        t.join()

    gloveMap = {}
    while not retQ.empty():
        gloveMap.update(retQ.get())

    print(gloveMap)
    return gloveMap
