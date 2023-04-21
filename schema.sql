CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL,
  is_teacher INTEGER NOT NULL,
  is_admin INTEGER NOT NULL
);

CREATE TABLE user_class (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  class_id INTEGER NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(id)
  FOREIGN KEY(class_id) REFERENCES class(id)
);

CREATE TABLE class (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  author_id TEXT UNIQUE NOT NULL,
  FOREIGN KEY(author_id) REFERENCES user(id)
);

CREATE TABLE user_exam (
  id INTEGER PRIMARY KEY,  -- use as seed
  user_id TEXT NOT NULL,
  exam_id INTEGER UNIQUE NOT NULL,
  taken INTEGER NOT NULL,
  score INTEGER,
  time_remaining INTEGER,
  progress TEXT, -- ordered dict {<question_id>:[<choice_id>|text,...]}
  FOREIGN KEY(user_id) REFERENCES user(id)
  FOREIGN KEY(exam_id) REFERENCES exam(id)
);

CREATE TABLE exam (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  author_id TEXT UNIQUE NOT NULL,
  class_id INTEGER NOT NULL,
  time_alotted INTEGER,
  is_open INTEGER NOT NULL,
  structure TEXT NOT NULL, -- ordered dict {<bank_id>: {amt:<amt>, points:<points>}, ...}
  FOREIGN KEY(author_id) REFERENCES user(id),
  FOREIGN KEY(class_id) REFERENCES class(id)
);

CREATE TABLE bank {
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  in_exams TEXT -- [<exam_id>, ...] used to keep db updated
}

CREATE TABLE question (
  id INTEGER PRIMARY KEY,
  bank_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  text TEXT NOT NULL,
  FOREIGN KEY(bank_id) REFERENCES bank(id)
  
)

CREATE TABLE question_choice (
  id INTEGER PRIMARY KEY,
  text TEXT NOT NULL,
  question_id INTEGER NOT NULL,
  is_answer INTEGER NOT NULL,
  FOREIGN KEY(question_id) REFERENCES question(id)
)
