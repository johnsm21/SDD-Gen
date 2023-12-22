from nltk.tokenize import sent_tokenize, word_tokenize
from textblob import Word
import torch
import numpy as np
from numpy import linalg as LA
from scipy import spatial
import TopMatcher
import time
from string import punctuation

def loadGlove(filepath):
    gloveMap = {}
    word2Id = {}
    weights = []

    with open(filepath) as fp:
        idx = 0
        sum = None
        for line in fp:
            parsedLine = line.split(" ")
            gloveMap[parsedLine[0]] = np.array(parsedLine[1:]).astype(float)

            word2Id[parsedLine[0]] = idx
            weights.append(parsedLine[1:])
            idx = idx + 1

            if sum is None:
                sum = np.array(parsedLine[1:]).astype(float)
            else:
                sum = sum + np.array(parsedLine[1:]).astype(float)

    unknownVector = np.divide(sum, idx)
    weights.append(unknownVector)
    gloveMap['<unknown>'] = unknownVector
    word2Id['<unknown>'] = idx

    return gloveMap, word2Id, torch.from_numpy(np.array(weights).astype(float)).float()

def word2Glove(w2vmap, data, printMiss=True):
    slash = w2vmap['/']
    print('-------------------')
    allData = []
    for dataum in data:
        dataum = dataum.lower()
        row = []
        for token in word_tokenize(dataum):
            if(token in w2vmap):
                row.append(w2vmap[token])
            else:
                if('/' in token):
                    for i in token.split('/'):
                        if(i != ''):
                            if(i in w2vmap):
                                row.append(w2vmap[i])
                                row.append(slash)
                            else:
                                if printMiss:
                                    print('Missing: ' + i)
                    row = row[0:-1]
                else:
                    if printMiss:
                        print('Missing: ' + token)
        allData.append(row)

    print('-------------------')
    return allData


def tokenize(w2vmap, data, printMiss=True):
    allData = []
    for dataum in data:
        dataum = dataum.lower()
        row = []
        for token in word_tokenize(dataum):
            if(token in w2vmap):
                row.append(token)
            else:
                if('/' in token):
                    for i in token.split('/'):
                        if(i != ''):
                            if(i in w2vmap):
                                row.append(i)
                            else:
                                if printMiss:
                                    print('Missing: ' + i)
                                row.append('<unknown>')

                            row.append("/")
                    row = row[0:-1]
                else:
                    # perfrom spell checking
                    result = Word(token).spellcheck()[0]
                    if (result[0] != token) and (result[1] > 0.9) and (result[0] in w2vmap):
                        if printMiss:
                            print('Autocorrect: ' + token + ' ---> ' + result[0])
                        row.append(result[0])
                    else:
                        if printMiss:
                            print('Missing: ' + token)
                        row.append('<unknown>')
        allData.append(row)

    return allData


def token2id(tokenvmap, data):
    allData = []
    for dataum in data:
        row = []
        for d in dataum:
            row.append(tokenvmap[d])
        allData.append(row)

    return allData

def token2idY(tokenvmap, data):
    ignoreList = set(punctuation);
    allData = []
    for dataum in data:
        row = []
        for d in dataum:
            if d not in ignoreList:
                row.append(tokenvmap[d])
        allData.append(row)

    return allData

def idX2Glove(weights, data):
    allData = []
    for dataum in data:
        row = []
        for d in dataum:
            row.append(weights[d])
        allData.append(row)

    return allData

def idY2Glove(weights, data):
    allData = []
    for dataum in data:
        allData.append(weights[dataum])
    return allData

def idY2GloveAverage(weights, data, gloveMap):
    allData = []

    for dataum in data:
        if len(dataum) == 1:
            allData.append(weights[dataum]);
        else:
            arr = np.reshape(weights[dataum[0]], (1, -1));
            for i in range(len(dataum)-1):
                dp1 = np.reshape(weights[dataum[i+1]], (1, -1));
                arr = np.concatenate((arr, dp1), axis=0);

            # print(arr);
            avg = np.average(arr, axis=0);

            # print(getTopXMatches(gloveMap, avg, 5));


            # convert to torch array
            avg = np.reshape(avg, (1, -1)).astype(float);
            avg = torch.from_numpy(avg).float();
            allData.append(avg);

    return allData

def idY2_L1NormSum(weights, data):
    allData = []

    for dataum in data:
        if len(dataum) == 1:
            allData.append(weights[dataum]);

        else:
            arr = np.reshape(weights[dataum[0]], (1, -1));
            for i in range(len(dataum)-1):
                dp1 = np.reshape(weights[dataum[i+1]], (1, -1));
                arr = np.concatenate((arr, dp1), axis=0);

            arrSum = np.sum(arr, axis=0);
            l1Nrom = LA.norm(arrSum, ord=1);
            l1NormSum = np.divide(arrSum, l1Nrom);

            # print(getTopXMatches(gloveMap, l1NormSum, 5));
            # print(LA.norm(l1NormSum,ord=1));

            # convert to torch array
            l1NormSum = np.reshape(l1NormSum, (1, -1)).astype(float);
            l1NormSum = torch.from_numpy(l1NormSum).float();
            allData.append(l1NormSum);

    # print(allData);
    return allData

def idY2_L1NormSumPrinter(weights, data, gloveMap):
    allData = []
    print(weights)
    print(data)
    for dataum in data:
        if len(dataum) == 1:
            allData.append(weights[dataum]);

        else:
            arr = np.reshape(weights[dataum[0]], (1, -1));
            for i in range(len(dataum)-1):
                dp1 = np.reshape(weights[dataum[i+1]], (1, -1));
                arr = np.concatenate((arr, dp1), axis=0);

            arrSum = np.sum(arr, axis=0);
            l1Nrom = LA.norm(arrSum, ord=1);
            l1NormSum = np.divide(arrSum, l1Nrom);

            print(getTopXMatches(gloveMap, l1NormSum, 5));
            # print(LA.norm(l1NormSum,ord=1));

            # convert to torch array
            l1NormSum = np.reshape(l1NormSum, (1, -1)).astype(float);
            l1NormSum = torch.from_numpy(l1NormSum).float();
            allData.append(l1NormSum);

    # print(allData);
    return allData

def pad_id(length, data):
    allData = []
    mask = []
    largestLength = length
    for l in data:
        if len(l) > largestLength:
            largestLength = len(l)

        row = []
        mask_row = []
        for i in range(length):
            if i < len(l):
                row.append(l[i])
                mask_row.append(1)
            else:
                row.append(0)
                mask_row.append(0)

        allData.append(row)
        mask.append(mask_row)

    if largestLength > length:
        print("Warning: 1 or more sentences are larger than max_sent_length = " + str(length) + ' and the largest sentence was ' + str(largestLength))

    return (np.array(allData), np.array(mask))


def getTopXMatches(gloveMap, vector, x):
    distArray = []

    for word, gloveVect in gloveMap.items():
        d = spatial.distance.cosine(gloveVect, vector)
        distArray.append((word, d))

    distArray = sorted(distArray, key=lambda x: x[1], reverse=False)
    distArray = distArray[0:x]

    return distArray

def getQuickTopXMatches(gloveMap, vector, x):
    distArray = []
    tm = TopMatcher.TopMatcher(x)

    for word, gloveVect in gloveMap.items():
        d = spatial.distance.cosine(gloveVect, vector)
        tm.add((word, d))

    return tm.getSortedList()

def calculateError(gloveMap, predict, dataY, x, printOn=False):
    predict = predict.detach().numpy()
    data_size = np.shape(predict)[0]
    # data_size = predict.size()[0]
    num_correct = 0

    for i in range(data_size):
        # start = time.time()
        # distArray = getTopXMatches(gloveMap, predict[i], x)
        # stop = time.time()
        # print("getTopXMatches time = %dm" % (stop - start))
        # print(distArray)
        #
        # start = time.time()
        # distQuickArray = getQuickTopXMatches(gloveMap, predict[i], x)
        # stop = time.time()
        # print("getTopXMatches time = %dm" % (stop - start))
        # print(distQuickArray)
        #
        # return True

        distArray = getTopXMatches(gloveMap, predict[i], x)

        if printOn:
            print('---------------')
            print('Actual: ' + dataY[i])
            print('Perdicted: ')
            print(distArray)

        for result in distArray:
            if result[0] == dataY[i]:
                num_correct = num_correct + 1
                break

    accuracy = 100*(num_correct/data_size)

    if printOn:
        print('---------------')
        print('Total accuracy: ' + str(accuracy))

    return accuracy
