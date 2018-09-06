from flask import Flask, request
import logging, os, requests

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Todoist-Morph not authorized, exiting. Go <a href=' + os.getenv('APP_URL') + '>back</a>'

    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url=os.getenv('API_TOKEN_EX'), data=data)
    print(r)

    # extracting response text
    pastebin_url = r.text
    print("The pastebin URL is:%s" % pastebin_url)

    #content = request.get_json()
    return 'Complete'


if __name__ == '__main__':
    app.run()
