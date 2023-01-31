import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
import time

from app.utils import safe_incr

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Users without roles (0) will be brought to the landing page
# Editors (1) will be able to do everything except assign roles
# Admins (2) will be able to assign roles, but cannot modify the roles of other admins
# The owner (3) can modify all roles

# TODO: allow owner to transfer ownership to other users


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
            if redis_client.hget('users', l_username):
                error = f"User {username} is already registered."
            else:
                user_id = safe_incr(redis_client, 'user:id')
                pipeline = redis_client.pipeline(True)
                pipeline.hset('users', l_username, user_id)
                pipeline.hmset('user:by_id:%s' % user_id, {
                    'username': username,
                    'password': generate_password_hash(password),
                    'id': user_id,
                    'permissions': 3 if user_id == 1 else 0,  # 0 is none, 1 is editor, 2 is admin, 3 is owner
                    'signup': time.time(),
                })
                pipeline.execute()
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
        user_id = redis_client.hget('users', l_username)

        if user_id is None:
            error = 'Incorrect username.'
        else:
            user = redis_client.hgetall('user:by_id:%s' % user_id)
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
        g.user = redis_client.hgetall('user:by_id:%s' % user_id)


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


# Landing page for newly signed-up users while they wait to be given editor permissions
@bp.route('/editor')
@login_required
def editor():
    return render_template('auth/no_permissions.html', message="Thanks for registering! In order to access the dashboard, your account must first be approved by an admin.")


def editor_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user['permissions'] == '0':
            return redirect(url_for('auth.editor'))

        return view(**kwargs)

    return wrapped_view


# Landing page for editors if they don't have admin permissions
@bp.route('/admin')
@editor_required
def admin():
    return render_template('auth/no_permissions.html', message="Admin permissions are required to view this page.")


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user['permissions'] == '0':
            return redirect(url_for('auth.editor'))
        elif g.user['permissions'] == '1':
            return redirect(url_for('auth.admin'))

        return view(**kwargs)

    return wrapped_view
