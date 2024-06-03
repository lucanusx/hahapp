from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from flask_wtf.file import FileAllowed


class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Kayıt Ol')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Bu kullanıcı adı zaten alınmış.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Bu email adresi zaten alınmış.')


class EditProfileForm(FlaskForm):
    username = StringField(
        'Kullanıcı Adı',
        validators=[
            Length(min=2, message='Kullanıcı adı kısmı 2 karakterden kısa olamaz.'),
            Length(max=25, message='Kullanıcı adı kısmı 25 karakterden uzun olamaz.'),
            DataRequired(message='Kullanıcı adı zorunludur.')
        ]
    )
    about_me = TextAreaField(
        'Hakkında',
        validators=[
            Length(min=0, max=500, message='Hakkında kısmı 500 karakterden uzun olamaz.')
        ]
    )
    profile_picture = FileField(
        'Profil Resmi Güncelle',
        validators=[
            FileAllowed(['jpg', 'png','jpeg','gif'], message='Profil resmi yalnızca jpg, jpeg, png, gif formatında olmalıdır.')
        ]
    )
    submit = SubmitField('Güncelle')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == self.username.data))
            if user is not None:
                raise ValidationError('Bu kullanıcı adı kullanılmaktadır.')
