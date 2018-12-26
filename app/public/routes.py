from flask import Blueprint, render_template
from app.webhooks.todoist_webhook import create_url

blueprint = Blueprint('public', __name__, static_folder='../static')

@blueprint.route('/')
def index():
    url = create_url()
    return render_template('public/index.html', url=url)


