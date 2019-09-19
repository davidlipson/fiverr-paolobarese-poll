from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime
import time

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    question = Column(Text)
    options = Column(Text)
    password = Column(Text)
    x = Column(Integer)
    y = Column(Integer)
    started = Column(Boolean)
    completed = Column(Boolean)
    viewers = Column(Integer)
    winners = Column(Text)
    voters = relationship("Voter")

    def __init__(self, question="", options=[], password="", x=300, y=300, viewers=0, winners=""):
        self.question = question
        self.options = ("|").join([o.replace("|", ":") for o in options if o != ""])
        self.password = password
        self.pid = int(time.time())
        self.x = x
        self.y = y
        self.started = False
        self.completed = False
        self.viewers = viewers
        self.winners = winners

    def __repr__(self):
        return '<Poll (%s, %s, %d, %d)>' % (self.question, self.options, self.x, self.y)

class Voter(Base):
    __tablename__ = "voters"
    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    x = Column(Integer)
    y = Column(Integer)

    def __init__(self, poll_id, x=300, y=300):
        self.poll_id = poll_id
        self.x = x
        self.y = y

    def __repr__(self):
        return '<Voter (%d, %d)>' % (self.x, self.y)
