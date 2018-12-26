from flask import Blueprint, request, jsonify
from app.extensions import db
from app.user.models import User
from app.webhooks.todoist_webhook import compute_hmac

blueprint = Blueprint('webhooks', __name__, static_folder='../static')

@blueprint.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    """Routes webhooks to various actions"""
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