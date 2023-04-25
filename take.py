

from db import get_db
from datetime import datetime, timedelta
from replit.database import dumps
import json
from bank import Bank
from user import User
from exam import Exam
import random


class Take():

  def __init__(self,
               id_,
               number,
               exam,
               student,
               over_at,
               score=None,
               status="not started",
               progress=[]):
    self.id = id_
    self.number = number
    self.exam = Exam.get(exam)
    self.student = User.get(student)
    if isinstance(over_at, float):
      self.over_at = over_at
    else:
      self.over_at = over_at.timestamp()
    self.score = score
    self.status = status
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
                status=take['status'],
                progress=take['progress'])
    return take

  @staticmethod
  def last_take(user, exam):
    all_takes = Take.all(user, exam)
    if not all_takes:
      return None
    take = None
    for take_id, take in all_takes.items():
      take.number
    take_id, take = max(all_takes.items(), key=lambda k: k[1].number)
    return take

  @staticmethod
  def get_id(number, exam, student):
    return f'ue_{student.id}_{exam.id}_{number}'
  
  @staticmethod
  def create(number, exam, student):
    db = get_db()
    id_ = Take.get_id(number, exam, student)
    mins = exam.time_alotted
    over_at = datetime.now() + timedelta(minutes=mins)
    over_at = over_at.timestamp()
    db[id_] = {
      'score': None,
      'over_at': over_at,
      'status': 'not started',
      'progress': []
    }
    return Take.get(id_)

  def start(self):
    if self.exam.is_open and self.student.exams[self.exam.id]['can_take'] and self.status == "not started" and not self.is_ended():
      self.status = "started"
      self.over_at = (datetime.now() + timedelta(minutes=self.exam.time_alotted)).timestamp()
      self.commit()

  def can_get_question(self):
    return self.status == "started" and not self.is_ended()
    
  def finish(self):
    self.status = "finished"
    self.commit()

  def is_started(self):
    """questions can be answered"""
    if self.status != "started" or self.is_ended():
      return False
    return True

  def is_ended(self):
    return datetime.now().timestamp() > self.over_at

  def get_seed(self, qbid, qid, qn):
    return f'{self.id}_{qbid}_{qid}_{qn}'
  
  def get_question(self, i):
    """i is 1-indexed question number"""
    db = get_db()
    qit = 1
    for qp in self.progress:
      if qit == i:
        return Bank.get(qp['qbid']).get_question(qp['qid'], answers_hidden=True, seed=self.get_seed(qp['qbid'], qp['qid'], qit))
      qit += 1

    q = None
    # generate new progress
    for qbid, amt_pnts in self.exam.structure.items():
      bank = Bank.get(qbid)
      for qi in range(amt_pnts['amt']):
        print(self.progress)
        done_qs = [p['qid'] for p in self.progress if p['qbid'] == qbid]
        print('-'*20 + 'pool')
        pool = [ qid for qid in bank.questions.keys() if qid not in done_qs and qid != 'next_id' ]
        qid = random.choice(pool)
        self.progress.append({'qbid': qbid, 'qid': qid, 'answer': []})
        seed = self.get_seed(qbid, qid, qit)
        if qit == i:
          break
        qit += 1
      if qit == i:
        break
        
    self.commit()
    return bank.get_question(qid, answers_hidden=True, seed=seed)
    
  # do I really need to seed it
  # does it need to be deterministic?
  # def get_seed(self, question_n):
  #   return f'{self.id}_{question_n}'

  def to_dict(self):
    return {
          'id': self.id,
          'exam': self.exam.id,
          'student': self.student.id,
          'over_at': self.over_at,
          'status': self.status,
          'score': self.score,
          'progress': json.loads(dumps(self.progress))
    }
    
  def commit(self):
    db = get_db()
    print(self.to_dict())
    db[self.id] = self.to_dict()
    print('here')