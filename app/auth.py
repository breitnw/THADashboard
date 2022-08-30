import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
import time


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        redis_client = current_app.extensions['redis']

        username = request.form['username']
        l_username = username.lower()
        password = request.form['password']

        error = None
        
        if not l_username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if len(password) < 8:
            flash('Password must be eight characters or longer.')
        
        if error is None:
            if redis_client.hget('users:', l_username):
                error = f"User {username} is already registered."
            else:
                # TODO: potentially implement a lock here
                user_id = redis_client.incr('user:id:')
                pipeline = redis_client.pipeline(True)
                pipeline.hset('users:', l_username, user_id)
                pipeline.hmset('user:%s' % user_id, {
                    'username': username,
                    'password': generate_password_hash(password),
                    'id': user_id,
                    'admin': 0,
                    'signup': time.time(),
                })
                pipeline.execute()
                redis_client.hset("user:" + username, "password", generate_password_hash(password))
                return redirect(url_for("auth.login"))
        
        flash(error)
    
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        redis_client = current_app.extensions['redis']

        username = request.form['username']
        l_username = username.lower()
        password = request.form['password']

        error = None
        user = None
        user_id = redis_client.hget('users:', l_username)

        if user_id is None:
            error = 'Incorrect username.'
        else:
            user = redis_client.hgetall('user:%s' % user_id)
            if not check_password_hash(user['password'], password):
                error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)
    
    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        redis_client = current_app.extensions['redis']
        g.user = user = redis_client.hgetall('user:%s' % user_id)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view
