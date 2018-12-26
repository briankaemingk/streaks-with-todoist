from flask import Blueprint, render_template, session

blueprint = Blueprint('user', __name__, static_folder='../static')

@blueprint.route('/settings')
def settings():
    settings_list = session['settings_list']
    return render_template('user/settings.html', settings_list=settings_list)