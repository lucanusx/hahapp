import os
basedir = os.path.abspath(os.path.dirname(__file__))
# Config class for the Flask app

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    POSTS_PER_PAGE = 6
    SCORE_PER_LIKE = 1
    SCORE_PER_COMMENT = 2
    SCORE_PER_POST = 5
    MAINTENANCE_MODE = 0
