from sqlalchemy import Column, Integer, String, DateTime, Text
from db import Base
from datetime import datetime
import time

class Coord(Base):
    __tablename__ = "coords"
    id = Column(Integer, primary_key=True)
    x = Column(Integer)
    y = Column(Integer)

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __repr__(self):
        return '<Coord (%d, %d)>' % (self.x, self.y)

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    question = Column(Text)
    options = Column(Text)
    password = Column(Text)

    def __init__(self, question="", options=[], password=""):
        self.question = question
        self.options = ("|").join([o.replace("|", ":") for o in options if o != ""])
        self.password = password
        self.pid = int(time.time())

    def __repr__(self):
        return '<Poll (%s, %s)>' % (self.question, self.options)
