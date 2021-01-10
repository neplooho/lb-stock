from flask import Flask, Response, redirect, request

app = Flask(__name__)


@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.route('/', methods=['POST'])
def main():
    return Response('Duck says meow')


if __name__ == '__main__':
    app.run(ssl_context=('secrets/public.pem', 'secrets/private.key'), host='0.0.0.0', port=8443)
