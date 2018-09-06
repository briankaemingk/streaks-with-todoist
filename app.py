import logging
from flask import Flask, request

app = Flask(__name__)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    print(code + ' ' + state)
    print(error)
    #content = request.get_json()
    #print(content)
    return 'Complete'


if __name__ == '__main__':
    app.run()
