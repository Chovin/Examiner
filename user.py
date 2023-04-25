from flask_login import UserMixin

from db import get_db
from replit.database import dumps
import json


class User(UserMixin):

  def __init__(self,
               id_,
               name,
               email,
               profile_pic,
               is_teacher=False,
               is_admin=False,
               exams={}):
    self.id = id_
    self.name = name
    self.email = email
    self.profile_pic = profile_pic
    self.is_teacher = bool(is_teacher)
    self.is_admin = bool(is_admin)
    self.exams = exams

  @staticmethod
  def all(as_dicts=False):
    db = get_db()
    lst = {k: User.get(k) for k, v in db['users'].items()}
    if not as_dicts:
      return lst

    return {k: v.to_dict() for k, v in lst.items()}
  
  @staticmethod
  def get(user_id):
    db = get_db()
    user = db['users'].get(user_id)
    
    if not user:
      return None

    user = User(id_=user_id,
                name=user['name'],
                email=user['email'],
                profile_pic=user['profile_pic'],
                is_teacher=user['is_teacher'],
                is_admin=user['is_admin'],
                exams=user['exams'])
    return user

  @staticmethod
  def create(id_, name, email, profile_pic, is_teacher=False, is_admin=False, exams={}):
    db = get_db()
    db['users'][id_] = {
      'name': name,
      'email': email,
      'profile_pic': profile_pic,
      'is_teacher': is_teacher,
      'is_admin': is_admin,
      'exams': exams
    }

  def is_assigned(self, eid):
    eid = str(eid)
    return bool(self.exams.get(eid))

  def can_take(self, eid):
    eid = str(eid)
    return self.exams.get(eid, {'can_take': False})['can_take']

  def assign_exam(self, eid):
    eid = str(eid)
    if eid in self.exams:
      self.exams[eid]['can_take'] = True
    else:
      self.exams[eid] = {'can_take': True, 'current_take': 1}

  def unassign_exam(self, eid):
    eid = str(eid)
    if eid in self.exams:
      self.exams[eid]['can_take'] = False

  def to_dict(self):
    return {
      'id': self.id,
      'name': self.name,
      'email': self.email,
      'profile_pic': self.profile_pic,
      'is_teacher': self.is_teacher,
      'is_admin': self.is_admin,
      'exams': json.loads(dumps(self.exams)),
    }
