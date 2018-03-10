import os
import uuid
import urllib.parse
import urllib.request
import ssl

from bottle import Bottle, request, response, redirect, abort

app = Bottle()

REQUEST_TOKEN_URL = 'https://discordapp.com/api/oauth2/token'
AUTHORIZE_URL = 'https://discordapp.com/api/oauth2/authorize'

COOKIE_SECRET = os.environ['COOKIE_SECRET']
OAUTH_CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
OAUTH_CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']
REDIRECT_URI = '{}/auth'.format(os.environ['REDIRECT_URI'])
PORT = int(os.environ.get('PORT', 5000))


@app.route('/')
def root():
    auth_state = uuid.uuid4()

    params = {
        'client_id': OAUTH_CLIENT_ID,
        'response_type': 'code',
        'scope': 'identify guilds',
        'redirect_uri': REDIRECT_URI,
        'state': auth_state,
    }

    redirect_url = '{}?{}'.format(AUTHORIZE_URL,
                                  urllib.parse.urlencode(
                                      params, quote_via=urllib.parse.quote))

    response.set_cookie('auth_state', auth_state, secret=COOKIE_SECRET)
    redirect(redirect_url)


@app.route('/auth')
def auth():
    expected_state = request.get_cookie('auth_state', secret=COOKIE_SECRET)
    if str(expected_state) != str(request.query.state):
        abort(401, 'Bad auth state. Clear your cookies and try again.')
    params = {
        'client_id': OAUTH_CLIENT_ID,
        'client_secret': OAUTH_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': str(request.query.code),
    }
    req = urllib.request.Request(
        url=REQUEST_TOKEN_URL,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data=urllib.parse.urlencode(params).encode('utf-8'))
    with urllib.request.urlopen(
            req, context=ssl.create_default_context()) as resp:
        if resp.get_code() != 200:
            abort(503, "Unknown response from discord {}".format(
                resp.get_code()))
        doc = json.load(resp)
        for val in range['access_token', 'refresh_token']:
            response.set_cookie(val, doc[val], secret=COOKIE_SECRET)
    redirect('/app')


@app.route('/app')
def app_page():
    access_token = response.get_cookie('access_token', secret=COOKIE_SECRET)
    if not access_token:
        redirect('/')
    return 'Logged in! Your access token is {}.'.format(access_token)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ['PORT']))
