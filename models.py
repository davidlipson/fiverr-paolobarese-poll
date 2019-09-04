from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from datetime import datetime

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
