from flask import Blueprint, current_app, request, redirect, url_for, flash, render_template

from app.auth import admin_required
from app.utils import safe_incr

bp = Blueprint('admin', __name__, url_prefix='/admin')


# Page only accessible to admins, where permissions settings can be updated
@bp.route('/controls', methods=['GET'])
@admin_required
def controls():
    redis_client = current_app.extensions['redis']

    users = redis_client.keys(pattern="user:by_id:*")
    user_data = []
    for u in users:
        user_data.append((redis_client.hget(u, 'username'), redis_client.hget(u, 'permissions')))

    hubs = redis_client.keys(pattern="hub:by_id:*")
    hub_info = []
    for h in hubs:
        hub_idx = h[10:]
        (name, lat, long) = list(redis_client.hgetall(h).values())
        (lat, long) = (float(lat), float(long))
        lat_formatted = "{lat:.2f}°{dir}".format(lat=abs(lat), dir='N' if lat > 0 else 'S')
        long_formatted = "{long:.2f}°{dir}".format(long=abs(long), dir='E' if lat > 0 else 'W')
        coords_formatted = "{}, {}".format(lat_formatted, long_formatted)
        hub_info.append((hub_idx, name, coords_formatted))

    print(hub_info)

    return render_template('auth/admin_controls.html', user_data=user_data, hub_info=hub_info)


@bp.route('/update_users', methods=['POST'])
@admin_required
def update_users():
    redis_client = current_app.extensions['redis']
    for (user, value) in request.form.items():
        user_id = redis_client.hget("users", user)
        user_key = "user:by_id:%s" % user_id
        redis_client.hset(user_key, 'permissions', value)
    return redirect(url_for("admin.controls"))


@bp.route('/delete_user/<user>', methods=['GET'])
@admin_required
def delete_user(user):
    redis_client = current_app.extensions['redis']
    user_id = redis_client.hget("users", user)
    user_key = "user:by_id:%s" % user_id
    redis_client.delete(user_key)
    redis_client.hdel("users", user)
    return redirect(url_for("admin.controls"))


@bp.route('/add_hub', methods=['POST'])
@admin_required
def add_hub():
    redis_client = current_app.extensions['redis']
    try:
        new_hub_lat = float(request.form.get('new-hub-lat'))
        new_hub_long = float(request.form.get('new-hub-long'))
        if not ((-90 <= new_hub_lat <= 90) and (-180 <= new_hub_long <= 180)):
            raise ValueError
    except ValueError:
        flash("Latitude and longitude must be valid decimal numbers")
        return redirect(url_for("admin.controls"))

    hub_id = safe_incr(redis_client, 'hub:id')
    hub_key = "hub:by_id:%s" % hub_id
    redis_client.hset(hub_key, 'name', request.form.get('new-hub-name'))

    redis_client.hset(hub_key, 'lat', new_hub_lat)
    redis_client.hset(hub_key, 'long', new_hub_long)

    return redirect(url_for("admin.controls"))


@bp.route('/update_hub', methods=['POST'])
@admin_required
def update_hub():
    redis_client = current_app.extensions['redis']
    hub_key = "hub:by_id:%s" % request.form.get('save')
    redis_client.hset(hub_key, 'name', request.form.get('hub-input'))
    return redirect(url_for("admin.controls"))


@bp.route('/delete_hub/<idx>', methods=['GET'])
@admin_required
def delete_hub(idx):
    redis_client = current_app.extensions['redis']
    hub_key = "hub:by_id:%s" % idx
    redis_client.delete(hub_key)
    return redirect(url_for("admin.controls"))
