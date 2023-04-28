# https://realpython.com/flask-google-login/

# Python standard libraries
import json
import os
# import sqlite3
import traceback

# Third-party libraries
from flask import Flask, redirect, request, url_for, render_template, abort, jsonify
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from replit.database import dumps

# Internal imports
from db import init_db_command, get_db
from user import User
from exam import Exam
from bank import Bank
from take import Take
from utils import teacher_required

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
  init_db_command()
except:
  print(traceback.format_exc())
# except sqlite3.OperationalError:
#     # Assume it's already been created
#     pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
  return User.get(user_id)
  
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
def index():
    if current_user.is_authenticated:
      db = get_db()
      exs = db['exams']
      exams = {e: exs.get(e) for e in current_user.exams}
      return redirect('assigned')
      # return render_template('index.html', user=current_user, exams=exams)
    else:
      return render_template('login_prompt.html')

@app.route('/login')
def _login():
  # Find out what URL to hit for Google login
  google_provider_cfg = get_google_provider_cfg()
  authorization_endpoint = google_provider_cfg["authorization_endpoint"]

  # Use library to construct the request for Google login and provide
  # scopes that let you retrieve user's profile from Google
  request_uri = client.prepare_request_uri(
    authorization_endpoint,
    redirect_uri=request.base_url.replace('http://', 'https://') + "/callback",
    scope=["openid", "email", "profile"],
  )
  return redirect(request_uri)

@app.route('/login/callback')
def _login_callback():
  # Get authorization code Google sent back to you
  code = request.args.get("code")
  # Find out what URL to hit to get tokens that allow you to ask for
  # things on behalf of a user
  google_provider_cfg = get_google_provider_cfg()
  token_endpoint = google_provider_cfg["token_endpoint"]
  
  # Prepare and send a request to get tokens! Yay tokens!
  token_url, headers, body = client.prepare_token_request(
    token_endpoint,
    authorization_response=request.url.replace('http://', 'https://'),
    redirect_url=request.base_url.replace('http://', 'https://'),
    code=code
  )
  token_response = requests.post(
    token_url,
    headers=headers,
    data=body,
    auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
  )

  # Parse the tokens!
  client.parse_request_body_response(json.dumps(token_response.json()))

  # Now that you have tokens (yay) let's find and hit the URL
  # from Google that gives you the user's profile information,
  # including their Google profile image and email
  userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
  uri, headers, body = client.add_token(userinfo_endpoint)
  userinfo_response = requests.get(uri, headers=headers, data=body)

  # You want to make sure their email is verified.
  # The user authenticated with Google, authorized your
  # app, and now you've verified their email through Google!
  # if userinfo_response.json().get("email_verified"):
  unique_id = userinfo_response.json()["sub"]
  users_email = userinfo_response.json()["email"]
  picture = userinfo_response.json()["picture"]
  users_name = userinfo_response.json()["given_name"]
  # else:
  #   return "User email not available or not verified by Google.", 400
  # Create a user in your db with the information provided
  # by Google
  user = User(
    id_=unique_id, name=users_name, email=users_email, profile_pic=picture, is_teacher=False, is_admin=False
)
  
  # TODO: remove this and add a different/better system later
  # all_exams = Exam.all(as_dicts=True)
  # exams = {k: {'can_take': True, 'current_take': 1} for k in all_exams}
  

  # Doesn't exist? Add it to the database.
  if not User.get(unique_id):
    User.create(unique_id, users_name, users_email, picture, False, False, exams={})

  # Begin user session by logging the user in
  login_user(user)
  
  # Send user back to homepage
  return redirect(url_for("index"))


@app.route('/logout')
@login_required
def _logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/privacy')
def privacy():
    return open('privacy.html').read()

@app.route('/tos')
def terms_of_service():
    return open('terms.html').read()


@app.route('/dashboard')
@login_required
# @teacher_required
def dashboard():
  if not current_user.is_teacher:
    abort(403)
  exs = Exam.all(as_dicts=True)
  exams = {eid: exs[eid] for eid in exs.keys() if exs[eid]['author_id'] == current_user.id}
  return render_template('dashboard.html', user=current_user, exams=exams)

@app.route('/new_exam', methods=['GET'])
@login_required
# @teacher_required
def new_exam():
  if not current_user.is_teacher:
    abort(403)
  eid = request.args.get('eid')
  exam = Exam.get(eid)
  # print(eid)
  # print(exam)
  structure = {}
  if exam:
    structure = json.loads(dumps(exam.structure))
  # print(structure)
  banks = Bank.all(as_dicts=False)
  banks = {bid: bank for bid, bank in banks.items() if current_user.id == bank.author.id}
  
  return render_template('new_exam.html', exam=exam, structure=structure, banks=banks)

@app.route('/new_bank', methods=['GET'])
@login_required
def new_bank():
  if not current_user.is_teacher:
    abort(403)
  qb_id = request.args.get('qb_id')
  bank = Bank.get(qb_id)
  if not bank:
    bank = {}
  else:
    bank = bank.to_dict()
  return render_template('new_bank.html', bank=bank)

@app.route('/student_watchtower', methods=['GET'])
@login_required
def student_watchtower():
  # lists students and their assigned test and scores. let teacher allow retake
  if not current_user.is_teacher:
    abort(403)

  ex = Exam.all(as_dicts=True)
  exams = {eid: ex[eid] for eid in ex.keys() if ex[eid]['author_id'] == current_user.id}
  users = User.all(as_dicts=True)
  # print(users)
  return render_template('student_watchtower.html', exams=exams, users=users)

@app.route('/assigned', methods=['GET'])
@login_required
def assigned():
  ex = Exam.all(as_dicts=True)
  exams = {i:e for i, e in ex.items() if i in current_user.exams}

  return render_template('assigned.html', exams=exams, user=current_user.to_dict())

@app.route('/prep_area/<int:eid>')
@login_required
def prep_exam(eid):
  # allow them to see this page so they can see the last test
  # if not current_user.can_take(eid):
  #   abort(403)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if str(eid) not in current_user.exams:
    abort(403)

  take = Take.last_take(current_user, exam)
  return render_template('prep_area.html', exam=exam.to_dict(), user=current_user.to_dict(), take=take)

@app.route('/take_exam/<int:eid>')
@login_required
def take_exam(eid):
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if not current_user.can_take(eid):
    abort(403)

  take = Take.last_take(current_user, exam)

  return render_template('take_exam.html', exam=exam.to_dict(), user=current_user.to_dict(), take=take.to_dict() if take and take.status != 'finished' else None)

@app.route('/prev_exam/<int:eid>')
@login_required
def prev_exam(eid):
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if current_user.can_take(eid):
    abort(403)
  take = Take.last_take(current_user, exam)
  if not take.is_finished():
    abort(403)

  qs = []
  for i, p in enumerate(take.progress):
    qs.append(take.get_question(i, answers_hidden=False))

  return render_template('prev_exam.html', exam=exam.to_dict(), user=current_user.to_dict(), take=take.to_dict(), questions=qs)

@app.route('/user/<uid>/<int:eid>/<action>', methods=['POST'])
@login_required
def assign_exam(uid, eid, action):
  if not current_user.is_teacher:
    abort(403)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if current_user.id != exam.author.id:
    abort(403)
  student = User.get(uid)
  if student is None:
    abort(404)
  actions = {
    'assign': student.assign_exam,
    'unassign': student.unassign_exam,
  }
  if action not in actions:
    abort(404)
  actions[action](eid)
  return jsonify(student.to_dict()['exams'][str(eid)])

# @app.route('/exam/<int:eid>/start', methods=['POST'])
# @login_required
# def start_exam(eid):
#   exam = Exam.get(eid)
#   if exam is None:
#     abort(404)
#   if not current_user.can_take(eid):
#     abort(403)
    
#   take = get_or_create_next_unfinished_take()

def get_or_create_next_unfinished_take(user, exam):
  last_take = Take.last_take(user, exam)
  if last_take is None or last_take.status == "finished":
    n = (int(last_take.number) + 1) if last_take else 1
    last_take = Take.create(n, exam, user)
  return last_take

@app.route('/question/<int:eid>/<int:i>', methods=['GET'])
@login_required
def get_question(eid, i):
  # print('get_question', eid, i)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if not current_user.can_take(eid):
    abort(403)
  if i < 0:
    return jsonify(None)

  take = get_or_create_next_unfinished_take(current_user, exam)
  if take.status == "not started":
    take.start()
  if take.can_get_question():
    return jsonify(take.get_question(i))
  else:
    # current_user.finish_take(exam.id)
    take.finish()
    return jsonify(False)

@app.route('/take/<int:eid>/progress', methods=['PUT'])
@login_required
def update_take_progress(eid):
  if not request.json:
    abort(400)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if not current_user.can_take(eid):
    abort(403)
  take = Take.last_take(current_user, exam)
  if take.is_ended():
    abort(403)

  qi = int(request.json['i'])
  answers = request.json['answers']
  take.update_progress(qi, answers)
  return jsonify(True)

@app.route('/take/<int:eid>/progress', methods=['POST'])
@login_required
def post_take_progress(eid):
  if not request.json or not request.json['answers']:
    abort(400)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if not current_user.can_take(eid):
    abort(403)
  take = Take.last_take(current_user, exam)
  if take.is_ended():
    abort(403)
  answers = request.json['answers']

  for i, ans in enumerate(answers):
    take.update_progress(i, ans)

@app.route('/take/<int:eid>/finish', methods=['POST'])
@login_required
def finish_take(eid):
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if not current_user.can_take(eid):
    abort(403)
  take = Take.last_take(current_user, exam)
  take.finish()

  return take.to_dict()
  

@app.route('/exam/list', methods=['GET'])
@login_required
def exam_list():
  # returns authored exams if teachern and authored param
  ex = Exam.all(as_dicts=True)
  if current_user.is_teacher and request.args.get('authored'):
    exams = {i:e for i, e in ex.items() if current_user.id == e['author_id']}
  else:
    exams = {i: ex[i] for i in current_user['exams']}
  return jsonify(exams)

@app.route('/exam/<int:eid>', methods=['GET'])
@login_required
def get_exam(eid):
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if str(eid) not in current_user.exams:
    if current_user.is_teacher and request.args.get('authored') and exam.author.id == current_user.id:
      pass
    else:
      abort(403)
  return jsonify(exam.to_dict())

@app.route('/exam/<int:eid>', methods=['PUT'])
@login_required
def update_exam(eid):
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  if current_user.id != exam.author.id:
    abort(403)
  exam.name = request.json['name']
  exam.time_alotted = int(request.json['time'])
  exam.is_open = request.json['is_open']
  exam.structure = request.json['structure']
  # print(exam.structure)
  exam.commit()
  return jsonify(exam.to_dict())

@app.route('/exam/<int:eid>', methods=['DELETE'])
@login_required
def delete_exam(eid):
  exam = Exam.get(eid)
  if exam is None:
    abort(404)
  
  if (not current_user.is_teacher) or (not exam.author.id == current_user.id):
    abort(403)

  exam.delete()
  return jsonify(exam.to_dict())

@app.route('/exam', methods=['POST'])
@login_required
def create_exam():
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  name = request.json['name']
  time_alotted = int(request.json['time'])
  is_open = bool(request.json['is_open'])
  structure = request.json.get('structure', {})

  exam = Exam.create(name, current_user, time_alotted, is_open=is_open, structure=structure)
  return jsonify(exam.to_dict())


@app.route('/bank/list', methods=['GET'])
@login_required
def bank_list():
  if not current_user.is_teacher:
    abort(403)
  banks = Bank.all(as_dicts=True)
  banks = {bid: b for bid, b in banks.items() if current_user.id == b['author_id']}
  return jsonify(banks)

@app.route('/bank/<int:qbid>', methods=['GET'])
@login_required
def get_bank(qbid):
  if not current_user.is_teacher:
    abort(403)
  bank = Bank.get(qbid)
  if bank is None:
    abort(404)
  if current_user.id != bank.author.id:
    abort(403)
  return jsonify(bank.to_dict())

@app.route('/bank', methods=['POST'])
@login_required
def create_bank():
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  name = request.json['name']
  if not name:
    abort(400)

  bank = Bank.create(name, current_user, questions={})
  return jsonify(bank.to_dict())

@app.route('/bank/<int:eid>', methods=['DELETE'])
@login_required
def delete_bank(eid):
  bank = Bank.get(eid)
  if bank is None:
    abort(404)
  
  if (not current_user.is_teacher) or (not bank.author.id == current_user.id):
    abort(403)

  bank.delete()
  return jsonify(bank.to_dict())

@app.route('/bank/<int:qbid>', methods=['PUT'])
@login_required
def update_bank(qbid):
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  bank = Bank.get(qbid)
  if bank is None:
    abort(404)
  if current_user.id != bank.author.id:
    abort(403)
  bank.name = request.json['name']
  bank.questions = request.json['questions']
  bank.commit()
  return jsonify(bank.to_dict())

@app.route('/bank/<int:qbid>', methods=['POST'])
@login_required
def add_question(qbid):
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  bank = Bank.get(qbid)
  if bank is None:
    abort(404)
  if current_user.id != bank.author.id:
    abort(403)

  text = request.json['text']
  type_ = request.json['type']
  choices = request.json['choices']
  q = bank.add_question(text, type_, choices)
  return jsonify(q)

@app.route('/bank/<int:qbid>/<int:qid>', methods=['PUT'])
@login_required
def update_question(qbid, qid):
  if not current_user.is_teacher:
    abort(403)
  if not request.json:
    abort(400)
  bank = Bank.get(qbid)
  if bank is None:
    abort(404)
  if current_user.id != bank.author.id:
    abort(403)

  q = bank.get_question(qid)
  if q is None:
    abort(404)

  bank.update_question(
    qid, 
    request.json['text'], 
    request.json['type'],
    request.json['choices']
  )
  # print(request.json['choices'])
  q = bank.get_question(qid)
  return jsonify(q)

@app.route('/bank/<int:qbid>/<int:qid>', methods=['DELETE'])
@login_required
def delete_question(qbid, qid):
  if not current_user.is_teacher:
    abort(403)
  bank = Bank.get(qbid)
  if bank is None:
    abort(404)
  if current_user.id != bank.author.id:
    abort(403)

  q = bank.get_question(qid)
  if q is None:
    abort(404)
  
  q = bank.delete_question(qid)
  return jsonify(q)

app.run(host='0.0.0.0', port=443)
