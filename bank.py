from db import get_db
from user import User
from replit.database import dumps
import json

class Bank():
  def __init__(self,
              id_,
              name,
              author,
              questions = {'next_id':0}):
    self.id = str(id_)
    self.name = name
    self.author = author
    questions.setdefault('next_id', 0)
    self.questions = questions

  @staticmethod
  def all(as_dicts=False):
    db = get_db()
    keys = db.prefix('qb_')
    lst = {k[len('qb_'):]: Bank.get(k[len('qb_'):]) for k in keys if 'next_id' not in k}
    if not as_dicts:
      return lst

    return {k: v.to_dict() for k, v in lst.items()}
  
  @staticmethod
  def get(qb_id):
    qb_id = str(qb_id)
    db = get_db()
    key = 'qb_' + qb_id
    bank = db.get(key)

    if not bank:
      return None

    bank = Bank(id_=qb_id,
               name=bank['name'],
               author=User.get(bank['author_id']),
               questions=bank['questions'])
    return bank

  @staticmethod
  def create(name, author, questions={}):
    db = get_db()

    questions['next_id'] = 0
    qbid = str(db['qb_next_id'])
    db['qb_next_id'] += 1
    db['qb_' + qbid] = {
      'name': name,
      'author_id': author.id,
      'questions': questions
    }
    return Bank.get(str(qbid))

  def to_dict(self):
    return {
      'id': self.id,
      'name': self.name,
      'author_id': self.author.id,
      'questions': json.loads(dumps(self.questions))
    }

  def delete(self):
    db = get_db()
    del db['qb_'+str(self.id)]
    return self

  def commit(self):
    db = get_db()
    db['qb_'+str(self.id)] = self.to_dict()

  def get_question(self, qid):
    q = self.questions.get(str(qid))
    return json.loads(dumps(q))
    
  def add_question(self, text, type_, choices):
    key = str(self.questions['next_id'])
    self.questions['next_id'] += 1
    self.questions[key] = {
      'id': key,
      'text': text,
      'type': type_,
      'choices': choices
    }
    return json.loads(dumps(self.questions[key]))

  def update_question(self, id_, text, type_, choices):
    id_ = str(id_)
    self.questions[id_]['text'] = text
    self.questions[id_]['type'] = type_
    self.questions[id_]['choices'] = choices
    return json.loads(dumps(self.questions[id_]))
  
  def delete_question(self, qid):
    qid = str(qid)
    q = self.questions[qid]
    del self.questions[qid]
    return json.loads(dumps(q))
  
    