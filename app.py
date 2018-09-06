from flask import Flask, request

app = Flask(__name__)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    print(code)
    #content = request.get_json()
    #print(content)
    return 'Complete'


if __name__ == '__main__':
    app.run()
