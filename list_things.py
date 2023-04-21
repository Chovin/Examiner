# import dependencies
from replit import db

# init the overall users db array
users = db['users']

def list_teachers():
  print('TEACHERS!')
  
  # iterate through users
  for id, user in users.items():
    name = user['name']
    email = user['email']
    is_teacher = user['is_teacher']

    # print the user if he/she is a teacher
    if is_teacher:
      print(f'User\'s name: {name}')
      print(f'User\'s email: {email}')
      print(f'A teacher?: {is_teacher}\n') # line break important!

def list_students():
  print('STUDENTS!')
  
  # iterate through users
  for id, user in users.items():
    name = user['name']
    email = user['email']
    is_teacher = user['is_teacher']
    students_tests = user['exams']

    # print the user if he/she is NOT a teacher
    if not is_teacher:
      print(f'User\'s name: {name}')
      print(f'User\'s email: {email}')
      print(f'A teacher?: {is_teacher}\n')

      print(f'{name}\'s tests!:')

      for id, item in students_tests.items():
        can_take = item['can_take']
        print(f'Test ID: {id}, Takeable?: {can_take}')

      # line break
      print('\n')

def list_tests():
  print('TESTS!')
  
  exams = db['exams']
  tests = exams.items()
  for id, test in tests:
    if id != 'next_id': # quick workaround for db mess...

      # print name, time alloted, is_open
      
      name = test['name']
      time_allotted = test['time_alotted']
      is_open = test['is_open']
      
      print(f'Test name: {name}')
      print(f'Time allotted: {time_allotted}')
      print(f'Available?: {is_open}\n')

# invoke all functions
list_teachers()
list_students()
list_tests()