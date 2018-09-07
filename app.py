from todoist.api import TodoistAPI
from flask import Flask, request, jsonify
import os, requests, string, random, hmac, base64, hashlib

app = Flask(__name__)

@app.route('/')
def index():
    # Generate 6 random digits
    os.environ['STATE'] = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    url = 'https://todoist.com/oauth/authorize?state=' + os.getenv('STATE') + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'
    return 'Todoist-Morph: Click <a href=' + url + '>here</a> to connect your account.'

@app.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Todoist-Morph not authorized, exiting. Go <a href=' + "/" + '>back</a>'
    initialize_token(code)
    return 'Complete'


@app.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    event_id = request.headers.get('X-Todoist-Delivery-ID')

    # Check if user-agent matches to todoist webhooks
    if request.headers.get('USER-AGENT') == 'Todoist-Webhooks':

        if not request.json:
            return jsonify({'status': 'rejected',
                            'reason': 'malformed request'}), 400

        # Take payload and compute hmac
        request_hmac = request.headers.get('X-Todoist-Hmac-SHA256')
        calculated_hmac = base64.b64encode(
            hmac.new(bytes(os.getenv('CLIENT_SECRET'), encoding='utf-8'), msg=request.get_data(), digestmod=hashlib.sha256).digest()).decode("utf-8")

        if request_hmac == calculated_hmac:
            if request.json['event_data']['content'] == "Test":
                return jsonify({'status': 'accepted', 'request_id': event_id}), 200
        else:
            return jsonify({'status': 'rejected',
                            'reason': 'invalid request'}), 400
    else:
        return jsonify({'status': 'rejected'}), 400
    return jsonify({'status': 'accepted', 'request_id': event_id}), 200


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


if __name__ == '__main__':
    app.run()
