from flask import abort
from flask_login import current_user

def teacher_required(func):
  def wrapper():
    if not current_user.is_teacher:
      abort(403)
    else:
      func()
  return wrapper