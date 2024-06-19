from flask import render_template, flash, redirect, url_for, request, get_flashed_messages, jsonify
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, EmptyForm, EditProfileForm, PostForm, CommentForm
from app.models import User, Post, PostLike, Comment
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import os


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_login_date = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('homepage')
        return redirect(next_page)
    return render_template('login.html', form=form)

@login_required
@app.route('/home')
@app.route('/homepage')
def homepage():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['POSTS_PER_PAGE']
    query = current_user.following_posts()
    posts = db.paginate(query, page=page, per_page=per_page, error_out=False)
    next_url = url_for('homepage', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('homepage', page=posts.prev_num) if posts.has_prev else None
    return render_template('home.html', posts=posts.items, next_url=next_url, prev_url=prev_url, title='Anasayfa')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    
    page = request.args.get('page', 1, type=int)
    per_page = app.config['POSTS_PER_PAGE']
    query = sa.select(Post).where(Post.user_id == user.user_id).order_by(Post.upload_date.desc())
    posts = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    
    return render_template('user.html', user=user, form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        
        # Handle profile picture upload if provided
        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file
        db.session.commit()
        flash('Değişiklikler kaydedildi.', 'success')
        return redirect(url_for('edit_profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    
    return render_template('edit_profile.html', form=form, flash_success=get_flashed_messages(category_filter=['success']))

def save_picture(form_picture):
    import secrets
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route('/500')
def error_500():
    return render_template('500.html')

@login_required
@app.route('/share_post', methods=['GET', 'POST'])
def share_post():
    form = PostForm()
    if form.validate_on_submit():
        post_text = form.post_text.data
        image_file = None
        if form.image.data:
            image_file = save_picture(form.image.data)
        
        post = Post(user=current_user, post_text=post_text, image_location=image_file)
        db.session.add(post)
        current_user.score += app.config['SCORE_PER_POST']
        db.session.commit()
        flash('Gönderiniz paylaşıldı!', 'success')
        return jsonify(success=True)
    
    return render_template('share_post.html', title='Post Paylaş', form=form, flash_success=get_flashed_messages(category_filter=['success']))

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@login_required
@app.route('/recent_posts')
def recent_posts():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['POSTS_PER_PAGE']
    query = sa.select(Post).order_by(Post.upload_date.desc())
    posts = db.paginate(query, page=page, per_page=per_page, error_out=False)
    next_url = url_for('recent_posts', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('recent_posts', page=posts.prev_num) if posts.has_prev else None
    return render_template('recent_post.html', posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            post_id=post_id,
            user_id=current_user.user_id,
            comment_text=form.comment_text.data, 
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(comment)

        post = db.session.get(Post, post_id)
        if post:
            post.user.score += app.config['SCORE_PER_COMMENT']
            current_user.score += app.config['SCORE_PER_COMMENT'] 

        db.session.commit()
        flash('Your comment has been added.', 'success')
    else:
        flash('Error: Your comment could not be added.', 'danger')
    return redirect(url_for('show_post', post_id=post_id))

@app.route('/p/<int:post_id>', methods=['GET', 'POST'])
@login_required
def show_post(post_id):
    post = db.first_or_404(sa.select(Post).where(Post.post_id == post_id))
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            post_id=post_id,
            user_id=current_user.user_id,
            text=form.comment_text.data,
        )
        db.session.add(comment)
        db.session.commit()
        flash('Yorumunuz eklendi.', 'success')
        return redirect(url_for('show_post', post_id=post_id))
    
    comments = db.session.scalars(
        sa.select(Comment).where(Comment.post_id == post_id).order_by(Comment.timestamp.asc())
    ).all()
    
    post_like = db.session.scalar(
        sa.select(PostLike).where(PostLike.user_id == current_user.user_id, PostLike.post_id == post_id)
    )
    liked = post_like.liked if post_like else None
    
    return render_template('show_post.html', post=post, liked=liked, comments=comments, form=form)

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        post_like = db.session.query(PostLike).filter_by(user_id=current_user.user_id, post_id=post_id).first()
        if post_like:
            if post_like.liked:
                return jsonify(success=False, message="Zaten beğendiniz."), 400
            else:
                post_like.liked = True
                post.user.score += app.config['SCORE_PER_LIKE'] * 2
                post.like_count += 2  
        else:
            new_like = PostLike(user_id=current_user.user_id, post_id=post_id, liked=True)
            db.session.add(new_like)
            post.user.score += app.config['SCORE_PER_LIKE']
            post.like_count += 1
        db.session.commit()
        return jsonify(success=True, like_count=post.like_count)
    return jsonify(success=False, message="Post not found"), 404

@app.route('/dislike/<int:post_id>', methods=['POST'])
@login_required
def dislike_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        post_like = db.session.query(PostLike).filter_by(user_id=current_user.user_id, post_id=post_id).first()
        if post_like:
            if not post_like.liked:
                return jsonify(success=False, message="Zaten beğenmediniz"), 400
            else:
                post_like.liked = False
                post.like_count -= 2  
                post.user.score -= app.config['SCORE_PER_LIKE'] * 2

        else:
            new_like = PostLike(user_id=current_user.user_id, post_id=post_id, liked=False)
            db.session.add(new_like)
            post.user.score -= app.config['SCORE_PER_LIKE']
            post.like_count -= 1
        db.session.commit()
        return jsonify(success=True, like_count=post.like_count)
    return jsonify(success=False, message="Post not found"), 404

@login_required
@app.route('/top_liked_posts')
def top_liked_posts():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['POSTS_PER_PAGE']
    query = sa.select(Post).order_by(Post.like_count.desc())
    posts = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    next_url = url_for('top_liked_posts', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('top_liked_posts', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('top_liked.html', posts=posts.items, next_url=next_url, prev_url=prev_url)

@login_required
@app.route('/top_users')
def top_users():
    top_users = db.session.query(User).order_by(User.score.desc()).limit(25).all()
    return render_template('top_users.html', top_users=top_users)
