import numpy as np
from scipy import stats

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
