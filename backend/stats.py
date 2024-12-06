import json
from abc import ABC, abstractmethod
import random

class Stat:
    @abstractmethod
    def construct(self):
        pass

class LineGraph(Stat):
    def __init__(self, title):
       self.title = title
       self.points = []
       self.labels = [] 
    
    def add_point(self, label, point):
        self.points.append(point)
        self.labels.append(label)

    def construct(self):
        line = {"title": self.title, "type" : "line"}
        data = {"labels" : self.labels, "datasets": [{
            "label" : self.title,
            "data" : self.points,
            "tension": 0.1,
            "fill": False,
            "borderColor": "rgb(75, 192, 192)",
        }]}
        line['data'] = data
        return line

class PieChart(Stat):
    def __init__(self, title):
        self.title = title
        self.pie_size = 0
        self.labels = []
        self.proportions = []
        self.colors = []
    def add_slice(self, label, proportion):
        if proportion > 1 or proportion < 0:
            raise Exception("Invalid proportion size")
        pie_size = self.pie_size + proportion
        if pie_size > 1:
            raise Exception("Not enough space in pie")
        self.pie_size = pie_size
        self.labels.append(label)
        self.proportions.append(proportion)
        self.colors.append("#"+str(hex(random.randrange(0, 2**24)).lstrip("0x")))

    def construct(self):
        if sum(self.proportions) != 1:
            raise Exception("Invalid proportion size")
        pie = {"title": self.title, "type" : "pie"}
        data = {"labels" : self.labels, "datasets": [{
            "label" : self.title,
            "data" : self.proportions,
            "hoverOffset": 5,
            "backgroundColor" : self.colors
        }]}
        pie['data'] = data
        return pie


class NumericalStat(Stat):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def construct(self):
        return {"title": self.name, "data":self.value}
        

class StatView():
    def __init__(self):
        self.graphs = []
        self.numeric_stats = []

    def add_graph(self, graph):
        self.graphs.append(graph)

    def add_number(self, number):
        self.numeric_stats.append(number)

    def json(self):
        return json.dumps({"graphs" : self.graphs, "numbers" : self.numeric_stats})