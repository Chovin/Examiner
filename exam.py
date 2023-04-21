from db import get_db
from user import User
from replit.database import dumps
import json

class Exam():
  def __init__(self,
              id_,
              name,
              author,
              time_alotted,
              is_open = False,
              structure = {}):
    self.id = str(id_)
    self.name = name
    self.author = author
    self.time_alotted = time_alotted
    self.is_open = is_open
    self.structure = structure

  @staticmethod
  def all(as_dicts=False):
    db = get_db()
    lst = {k: Exam.get(k) for k, v in db['exams'].items() if k != 'next_id'}
    if not as_dicts:
      return lst

    return {k: v.to_dict() for k, v in lst.items()}
  
  @staticmethod
  def get(exam_id):
    eid = str(exam_id)
    db = get_db()
    exam = db['exams'].get(eid)

    if not exam:
      return None

    exam = Exam(id_=eid,
               name=exam['name'],
               author=User.get(exam['author_id']),
               time_alotted=exam['time_alotted'],
               is_open=exam['is_open'],
               structure=exam['structure'])
    return exam

  @staticmethod
  def create(name, author, time_alotted, is_open=False, structure={}):
    db = get_db()
    exams = db['exams']
    eid = str(exams['next_id'])
    exams['next_id'] += 1
    exams[eid] = {
      'name': name,
      'author_id': author.id,
      'time_alotted': time_alotted,
      'is_open': is_open,
      'structure': structure
    }
    return Exam.get(str(eid))

  def to_dict(self):
    return {
      'id': self.id,
      'name': self.name,
      'author_id': self.author.id,
      'time_alotted': self.time_alotted,
      'is_open': self.is_open,
      'structure': json.loads(dumps(self.structure))
    }

  def delete(self):
    db = get_db()
    del db['exams'][self.id]
    return self

  def commit(self):
    db = get_db()
    db['exams'][self.id] = self.to_dict()