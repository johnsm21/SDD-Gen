import copy

class TopMatcher:
    def __init__(self, x):
        self.x = x
        self.resultList = []
        self.max = float('inf')

    def add(self, item):
        # check to see if we have enough items, if not add them
        if len(self.resultList) < self.x:
            self.resultList.append(item)
            self.resultList = sorted(self.resultList, key=lambda x: x[1], reverse=True)
            self.max = self.resultList[0][1]
            return True

        else:
            # check to see if this word matters
            if item[1] < self.max:
                self.resultList.pop(0)

                # self.resultList.append(item)
                # self.resultList = sorted(self.resultList, key=lambda x: x[1], reverse=True)

                for i in range(self.x - 1):
                    if item[1] > self.resultList[i][1]:
                        self.resultList.insert(i, item)
                        break

                if len(self.resultList) < self.x:
                    self.resultList.append(item)

                self.max = self.resultList[0][1]

                return True

        return False

    def getSortedList(self):
        # resultList_copy = copy.deepcopy(self.resultList)
        # resultList_copy.reverse()
        # return resultList_copy
        
        self.resultList.reverse()
        return self.resultList
