from todoist.api import TodoistAPI
from flask import Flask, request
import logging, os, requests

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@app.route('/')
def index():
    url = 'https://todoist.com/oauth/authorize?state=' + os.getenv('STATE') + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'
    print(url)
    return 'Todoist-Morph: Click <a href=' + url + '>here</a> to connect your account.'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Todoist-Morph not authorized, exiting. Go <a href=' + os.getenv('APP_URL') + '>back</a>'

    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url=os.getenv('API_TOKEN_EX'), data=data)

    # extracting response text
    content = r.json()
    access_token = content['access_token']
    print(access_token)
    api = TodoistAPI(access_token)
    api.sync()
    print(api.state['items'])

    return 'Complete'


if __name__ == '__main__':
    app.run()
