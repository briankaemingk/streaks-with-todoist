from flask import Blueprint, render_template, request, jsonify
from app.todoist_webhook import initiate_api, compute_hmac, create_url, initialize_token, initialize_cron_job
from app.extensions import db
from worker import conn

blueprint = Blueprint('public', __name__, static_folder='../static')


# Index page initiates a user's token
@blueprint.route('/')
def index():
    url = create_url()
    return render_template('index.html', url=url)


from app.user.models import User


@blueprint.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state and code:
        if state != state:
            return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'
        access_token = initialize_token(code)
        api = initiate_api(access_token)
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
            initialize_cron_job(api)
            settings_list = [['Streaks', u.streaks_feature], ['Just In Time tasks', u.jit_feature], ['Recurrence reschedule', u.recurrence_resch_feature], ['In-line comment', u.in_line_comment_feature]]
            return render_template('settings.html', settings_list=settings_list)
        else:
            u = User.query.filter_by(id=user_id).first()
            u.access_token = access_token
            db.session.commit()
            settings_list = [['Streaks', u.streaks_feature], ['Just In Time tasks', u.jit_feature], ['Recurrence reschedule', u.recurrence_resch_feature], ['In-line comment', u.in_line_comment_feature]]
            return render_template('settings.html', settings_list=settings_list)
    else: return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'

# Routes webhooks to various actions
@blueprint.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    event_id = request.headers.get('X-Todoist-Delivery-ID')
    req = request.json
    if event_id is not None and compute_hmac():
        user_id = req['user_id']
        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar() is not None
        if(user_exists):
            current_user = User.query.get(user_id)
            current_user.launch_task('process_webhooks', 'Processing webhook', req)
        return jsonify({'status': 'accepted', 'request_id': event_id}), 200
    else:
        return jsonify({'status': 'rejected',
                            'reason': 'malformed request'}), 400
