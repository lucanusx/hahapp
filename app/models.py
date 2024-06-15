from datetime import datetime, timezone
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.user_id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('users.user_id'), primary_key=True)
)

class User(UserMixin, db.Model):
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
    
    following = so.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == user_id),
        secondaryjoin=(followers.c.followed_id == user_id),
        back_populates='followers'
    )
    followers = so.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.followed_id == user_id),
        secondaryjoin=(followers.c.follower_id == user_id),
        back_populates='following'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        return user in self.following

    def followers_count(self):
        return len(self.followers)

    def following_count(self):
        return len(self.following)
    
    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.user.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.user_id == self.user_id,
                Author.user_id == self.user_id,
            ))
            .group_by(Post.post_id)
            .order_by(Post.upload_date.desc())
        )

class Post(db.Model):
    __tablename__ = 'posts'

    post_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.user_id'))
    post_text = sa.Column(sa.String)
    image_location = sa.Column(sa.String)
    upload_date = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))
    like_count = sa.Column(sa.Integer, default=0)
    comment_count = sa.Column(sa.Integer, default=0)
    user = so.relationship("User", back_populates="posts")

    def __repr__(self):
        return '<Post {}>'.format(self.post_text)

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class PostLike(db.Model):
    __tablename__ = 'post_likes'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.user_id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('posts.post_id'))
    liked = sa.Column(sa.Boolean, default=True)  # True if liked, False if disliked
    timestamp = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))

    user = so.relationship("User", back_populates="post_likes")
    post = so.relationship("Post", back_populates="post_likes")

User.post_likes = so.relationship("PostLike", back_populates="user")
Post.post_likes = so.relationship("PostLike", back_populates="post")
