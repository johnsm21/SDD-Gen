import numpy as np
from scipy import stats
from operator import itemgetter


# listODict [{"value": "hasco:originalID", "confidence": 0.9}, {"value": "sio:Number", "confidence": 0.7}, {"value": "chear:Weight", "confidence": 0.25}]
def calcStars(listODict):
    # create confidence array
    confList = []
    for i in listODict:
        confList.append(i["confidence"])
    confArray = np.array(confList)

    # Calculate z-score
    zArray = stats.zscore(confArray)

    # Calculate stars
    confList = []
    for i in zArray.tolist():
        x = int(round(i))
        if x < 0 :
            x = 0
        confList.append(x)

    # Generate new dictionaries
    x = 0
    for i in listODict:
        i["star"] = confList[x]
        x = x + 1

    return listODict

# listOfTuple [('http://semanticscience.org/resource/SIO_000585', 0.9696969696969697),
def calcArrayStars(listOfTuple):
    # create confidence array
    confList = []
    for i in listOfTuple:
        confList.append(i[1])
    confArray = np.array(confList)

    # Calculate z-score
    zArray = stats.zscore(confArray)

    # Calculate stars
    confList = []
    for i in zArray.tolist():
        x = int(round(i))
        if x < 0 :
            x = 0
        confList.append(x)

    # Generate new dictionaries
    x = 0
    listOfTriple = []
    for i in listOfTuple:
        listOfTriple.append((i[0], i[1], confList[x]))
        x = x + 1

    return listOfTriple

def distToConf(distArray):
    maxDist = max(distArray,key=itemgetter(1))[1]
    distArray = list(map(lambda i: (i[0], ((-1*i[1]) + maxDist)/maxDist), distArray))
    return distArray
