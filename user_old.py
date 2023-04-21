from flask_login import UserMixin

from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, is_teacher=False, is_admin=False):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.is_teacher = bool(is_teacher)
        self.is_admin = bool(is_admin)

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            id_=user[0], name=user[1], email=user[2], profile_pic=user[3], is_teacher=user[4], is_admin=user[5]
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic, is_teacher=False, is_admin=False):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic, is_teacher, is_admin) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_, name, email, profile_pic, is_teacher, is_admin),
        )
        db.commit()