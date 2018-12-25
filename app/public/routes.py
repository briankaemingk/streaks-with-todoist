from flask import Blueprint, render_template, request, jsonify
from app.todoist_webhook import initiate_api, compute_hmac, create_url
from app.registration.routes import initialize_token, initialize_cron_job
from app.extensions import db

blueprint = Blueprint('public', __name__, static_folder='../static')


# Index page initiates a user's token
@blueprint.route('/')
def index():
    url = create_url()
    return render_template('index.html', url=url)


from app.user.models import User



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
