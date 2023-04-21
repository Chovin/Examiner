# http://flask.pocoo.org/docs/1.0/tutorial/database/
# import sqlite3

import click
from replit import db as repl_db
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
  if "db" not in g:
    g.db = repl_db

  return g.db


def close_db(e=None):
  db = g.pop("db", None)

  if db is not None:
    db.close()


def init_db():
  db = get_db()

  schema = {
    'users': {},
    'exams': {'next_id': 0},
    'qb_next_id': 0
    # 'ue_<uid>_<exid>_<take>': {}
    # 'qb_<id>': {},
  }
  with current_app.open_resource("schema.py") as f:
    f.read()
    for k, v in schema.items():
      if k not in db:
        db[k] = v


@click.command("init-db")
@with_appcontext
def init_db_command():
  """Clear the existing data and create new tables."""
  init_db()
  click.echo("Initialized the database.")


def init_app(app):
  app.teardown_appcontext(close_db)
  app.cli.add_command(init_db_command)
