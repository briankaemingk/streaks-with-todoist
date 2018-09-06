from flask import Flask, request
import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    logging.warning(code + ' ' + state)
    logging.warning(error)
    #content = request.get_json()
    #print(content)
    return 'Complete'


if __name__ == '__main__':
    app.run()
