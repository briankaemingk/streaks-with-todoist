from todoist.api import TodoistAPI
from flask import Flask, request, jsonify
import os, requests, string, random, hmac, base64, hashlib, logging
import task_complete

app = Flask(__name__)

# Index page initiates a user's token
@app.route('/')
def index():
    # Generate 6 random digits
    os.environ['STATE'] = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    url = 'https://todoist.com/oauth/authorize?state=' + os.getenv('STATE') + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'
    return 'Todoist-Morph: Click <a href=' + url + '>here</a> to connect your account.'


# Callback set on the management console authorizes a user
@app.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Todoist-Morph not authorized, exiting. Go <a href=' + "/" + '>back</a>'
    initialize_token(code)
    return 'Complete'


# Routes webhooks to various actions
@app.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    event_id = request.headers.get('X-Todoist-Delivery-ID')
    if compute_hmac(event_id):
        api = initiate_api()
        if request.json['event_name'] == 'item:completed':
            task_complete.main(api, int(request.json['event_data']['id']))
        api.commit()
        return jsonify({'status': 'accepted', 'request_id': event_id}), 200
    else:
        return jsonify({'status': 'rejected',
                        'reason': 'malformed request'}), 400


# Gets the authorization code from the oauth callback and routes it to get the access token
def initialize_token(code):
    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url='https://todoist.com/oauth/access_token?', data=data)
    # extracting response text
    content = r.json()
    access_token = content['access_token']
    os.environ["TODOIST_APIKEY"] = access_token


# Get user's Todoist API Key
def get_token():
    token = os.getenv('TODOIST_APIKEY')
    return token

# Initiate and sync Todoist API
def initiate_api():
    TODOIST_APIKEY = get_token()
    if not TODOIST_APIKEY:
        logging.warning('Please set the API token in environment variable.')
        exit()
    api = TodoistAPI(TODOIST_APIKEY)
    api.sync()
    return api


# Take payload and compute hmac--check if user-agent matches to todoist webhooks
def compute_hmac(event_id):
    if request.headers.get('USER-AGENT') == 'Todoist-Webhooks':
        request_hmac = request.headers.get('X-Todoist-Hmac-SHA256')
        calculated_hmac = base64.b64encode(hmac.new(bytes(os.getenv('CLIENT_SECRET'), encoding='utf-8'), msg=request.get_data(), digestmod=hashlib.sha256).digest()).decode("utf-8")
        if request_hmac == calculated_hmac: return 1
        else: return 0


if __name__ == '__main__':
    app.run()
