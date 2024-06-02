from datetime import datetime, timezone
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login


class User(UserMixin,db.Model):
    __tablename__ = 'users'

    user_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String)
    email = sa.Column(sa.String)
    about_me = sa.Column(sa.String)
    password_hash = sa.Column(sa.String)
    profile_picture = sa.Column(sa.String, default='default.png')
    registration_date = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))
    last_login_date = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))
    posts = so.relationship("Post", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
class Post(db.Model):
    __tablename__ = 'posts'

    post_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.user_id'))
    post_text = sa.Column(sa.String)
    image_location = sa.Column(sa.String)
    upload_date = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))
    like_count = sa.Column(sa.Integer)
    comment_count = sa.Column(sa.Integer)
    user = so.relationship("User", back_populates="posts")

    def __repr__(self):
        return '<Post {}>'.format(self.post_text)
    
@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
