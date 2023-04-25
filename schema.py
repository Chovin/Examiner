{
  'users': {
    id: {
      'name': name,
      'email': email,
      'profile_pic': profile_pic,
      'is_teacher': is_teacher,
      'is_admin': is_admin,
      'exams': {id: {can_take: true}}
    }
  },
  'exams': {
    id: {
      'name': name,
      'author_id': author_id,
      'time_alotted': time_alotted,
      'is_open': is_open,
      'structure': {
        '<qb_id>': {
          'amt': amt,
          'points': points
        },
        ...,
      }
    }
  },
  'ue_<uid>_<exid>_<take#>': {
    'score': score,  # None if not started
    'over_at': over_at,
    'status': "not started" | "started" | "finished",
    'progress': [
      {'qbid': qbid, 'qid': qid, 'answer': [choice_id|text,...]},
    ]
  },
  'qb_<id>': {
    'name': name,
    'author_id': author_id
    'questions': {
      'qid': {
        'id': qid,
        'text': text,
        'type': type,
        'choices': {
          'choice_id': {
            'text': text,
            'is_answer': is_answer # None if example essay answer
          }
        }
      }
    }
  },
}