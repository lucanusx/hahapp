from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, DateTimeField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional
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


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    post_text = TextAreaField(
        'Açıklama',
        validators=[
            DataRequired(message='Post metni zorunludur.'),
            Length(min=1, max=300, message='Post metni 1 ile 300 karakter arasında olmalıdır.')
        ]
    )
    image = FileField(
        'Resim Ekle',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], message='Yalnızca jpg, jpeg, png, gif formatında resimler yükleyebilirsiniz.')
        ]
    )
    submit = SubmitField('Gönder')

class CommentForm(FlaskForm):
    comment_text = TextAreaField('Yorum yaz.', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Gönder')

class EditUserForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    email = StringField('E-Posta', validators=[DataRequired(), Email()])
    about_me = StringField('Hakkında', validators=[Optional()])
    password = PasswordField('Yeni Şifre', validators=[Optional()])
    score = IntegerField('Puan', validators=[Optional()])
    is_admin = BooleanField('Admin')
    delete_profile_picture = BooleanField('Profil resmini sil')
    submit = SubmitField('Kaydet')

class AdminConfigForm(FlaskForm):
    score_per_like = IntegerField('Beğeni Puan Değeri', validators=[DataRequired()])
    score_per_comment = IntegerField('Yorum Puan Değeri', validators=[DataRequired()])
    score_per_post = IntegerField('Postların Puan Değeri', validators=[DataRequired()])
    maintenance_mode = BooleanField('Bakım Modu')
    submit = SubmitField('Güncelle')