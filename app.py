from flask import Flask, request
import logging, os

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Todoist-Morph not authorized, exiting. Go <a href=' + os.getenv('APP_URL') + '>back</a>'
    #content = request.get_json()
    print(state)
    return 'Complete'


if __name__ == '__main__':
    app.run()
