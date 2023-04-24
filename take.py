

from db import get_db
from datetime import datetime, timedelta
from replit.database import dumps
import json
from bank import Bank
import random


class Take():

  def __init__(self,
               id_,
               number,
               exam,
               student,
               ends_at,
               score=None,
               progress={}):
    self.id = id_
    self.exam = exam
    self.student = student
    self.over_at = ends_at
    self.score = score
    self.progress = progress


  
  @staticmethod
  def all(user, exam, as_dicts=False):
    db = get_db()
    keys = db.prefix(f'ue_{user.id}_{exam.id}_')
    lst = {k: Take.get(k) for k in keys}
    if not as_dicts:
      return lst

    return {k: v.to_dict() for k, v in lst.items()}

  @staticmethod
  def get(take_id):
    db = get_db()
    take = db.get(take_id)
    _, uid, exid, taken = take_id.split('_')
    
    if not take:
      return None

    take = Take(id_=take_id,
                number=taken,
                exam=exid,
                student=uid,
                over_at=take['over_at'],
                score=take['score'],
                progress=take['progress'])
    return take

  @staticmethod
  def get_id(number, exam, student):
    return f'ue_{student.id}_{exam.id}_{number}'
  
  @staticmethod
  def create(number, exam, student):
    db = get_db()
    id_ = get_id(number, exam, student)
    mins = exam.time_alotted
    over_at = datetime.now() + timedelta(minutes=mins)
    over_at = over_at.timestamp()
    db[id_] = {
      'score': None,
      'over_at': over_at,
      'progress': {}
    }

  def get_question(self, i):
    """i is 1-indexed question number"""
    db = get_db()
    qit = 1
    for qbid, bankf in self.exam.structure.items():
      for qi in range(bankf.amt):
        if qit == i:
          break
        qit += 1
      if qit == i:
        break
      qpfx = f'{qbid}_'
      done_qs = [k[len(qpfx):] for k in self.progress if k.startswith(qpfx)]
      bank = Bank.get(qbid)
      pool = { qid: q for qid, q in bank.questions.items() if qid not in done_qs }
      qid = random.choice(pool)
      return bank.questions[qid]
    
  # do I really need to seed it
  # does it need to be deterministic?
  def get_seed(self, question_n):
    return f'{self.id}_{question_n}'

  def to_dict(self):
    return {
          'id': self.id,
          'exam': self.exam.id,
          'student': self.student.id,
          'over_at': self.over_at,
          'score': self.score,
          'progress': json.loads(dumps(self.progress))
    }
