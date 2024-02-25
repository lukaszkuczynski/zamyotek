import subprocess
from collections import Counter
from datetime import datetime
from itertools import filterfalse
from statistics import mean


class DistanceStack:
    def __init__(self, ms_ttl, max_val):
        self.ms_ttl = ms_ttl
        self.__elements = []
        # values greater than this will be ignored (sometimes distance sensor reports 1205 mm)
        self.max_val = max_val

    def push(self, el):
        if el < self.max_val:
            self.__elements.append((datetime.now(), el))
        self.__invalidate()

    def __invalidate(self):
        def determine(el):
            return (datetime.now() - el[0]).total_seconds() * 1000 > self.ms_ttl

        self.__elements[:] = filterfalse(determine, self.__elements)

    def avg_distance(self):
        self.__invalidate()
        if len(self.__elements) > 0:
            return mean(el[1] for el in self.__elements)
        else:
            return None


class AnyObjectStack:
    def __init__(self, ms_ttl):
        self.ms_ttl = ms_ttl
        self.__elements = []

    def push(self, el):
        self.__elements.append((datetime.now(), el))
        self.__invalidate()

    def __invalidate(self):
        def determine(el):
            return (datetime.now() - el[0]).total_seconds() * 1000 > self.ms_ttl

        self.__elements[:] = filterfalse(determine, self.__elements)

    def most_common(self):
        self.__invalidate()
        if len(self.__elements) < 1:
            return None
        most_common = Counter(self.__elements)
        return most_common.most_common()[0][0][1]


