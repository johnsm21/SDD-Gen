import numpy as np
import torch

def loadGlove(filepath):
    gloveMap = {}
    word2Id = {}
    weights = []

    with open(filepath) as fp:
        idx = 0
        sum = None
        for line in fp:
            parsedLine = line.split(" ")
            gloveMap[parsedLine[0]] = np.array(parsedLine[1:]).astype(np.float)

            word2Id[parsedLine[0]] = idx
            weights.append(parsedLine[1:])
            idx = idx + 1

            if sum is None:
                sum = np.array(parsedLine[1:]).astype(np.float)
            else:
                sum = sum + np.array(parsedLine[1:]).astype(np.float)

    unknownVector = np.divide(sum, idx)
    weights.append(unknownVector)
    gloveMap['<unknown>'] = unknownVector
    word2Id['<unknown>'] = idx

    return gloveMap, word2Id, torch.from_numpy(np.array(weights).astype(np.float)).float()
