import atexit
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, render_template, request, session, redirect, url_for
from app.webhooks.todoist_webhook import initiate_api, get_user_timezone, daily
from app.extensions import db
from app.user.models import User

blueprint = Blueprint('auth', __name__, static_folder='../static')

@blueprint.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state and code:
        if state != state:
            return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'
        access_token = initialize_token(code)
        api = initiate_api(access_token)
        if api is None:
            return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'
        user_id = api.state['user']['id']
        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar() is not None
        if not user_exists:
            if api.state['user']['is_premium']:
                u = User(user_id, access_token, jit_feature=True, recurrence_resch_feature=True, streaks_feature=True, in_line_comment_feature=True)
            else:
                u = User(user_id, access_token, jit_feature=False, recurrence_resch_feature=False, streaks_feature=True,
                         in_line_comment_feature=False)
            db.session.add(u)
            db.session.commit()
            settings_list = create_settings_list(u)
            session['settings_list'] = settings_list
            return redirect(url_for('user.settings'))
        else:
            u = User.query.filter_by(id=user_id).first()
            u.access_token = access_token
            db.session.commit()
            settings_list = create_settings_list(u)
            session['settings_list'] = settings_list
            session.close()
            return redirect(url_for('user.settings'))
    else: return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'


def initialize_token(code):
    """Gets the authorization code from the oauth callback and routes it to get the access token"""
    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url='https://todoist.com/oauth/access_token?', data=data)
    # extracting response text
    content = r.json()
    access_token = content['access_token']
    return access_token


def initialize_cron_job():
    """Create scheduled job to run after app token is initialized"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily, 'cron', minute=33)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


def create_settings_list(user):
    settings_list = [['Streaks', user.streaks_feature], ['Just In Time tasks', user.jit_feature],
                     ['Recurrence reschedule', user.recurrence_resch_feature],
                     ['In-line comment', user.in_line_comment_feature]]
    return settings_list