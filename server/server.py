import os

from bottle import Bottle, request, response, redirect, abort
from requests_oauthlib import OAuth2Session

app = Bottle()

API_URL = 'https://discordapp.com/api'
TOKEN_URL = 'https://discordapp.com/api/oauth2/token'
AUTHORIZE_URL = 'https://discordapp.com/api/oauth2/authorize'

COOKIE_SECRET = os.environ['COOKIE_SECRET']
OAUTH_CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
OAUTH_CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']
REDIRECT_URI = '{}/auth'.format(os.environ['REDIRECT_URI'])
PORT = int(os.environ.get('PORT', 5000))


def token_updater(token):
    response.set_cookie('oauth2_token', token, secret=COOKIE_SECRET)


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH_CLIENT_ID,
            'client_secret': OAUTH_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route('/')
def root():
    scope = ['identify', 'guilds']
    discord = make_session(scope=scope)
    auth_url, state = discord.authorization_url(AUTHORIZE_URL)
    response.set_cookie('oauth2_state', state, secret=COOKIE_SECRET)
    redirect(auth_url)


@app.route('/auth')
def auth():
    if request.query.error:
        abort(401, request.query.error)
    discord = make_session(
        state=request.get_cookie('oauth2_state', secret=COOKIE_SECRET))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH_CLIENT_SECRET,
        authorization_response=request.url,
    )
    response.set_cookie('oauth2_token', token, secret=COOKIE_SECRET)
    redirect('/app')


@app.route('/app')
def app_page():
    discord = make_session(
        token=request.get_cookie('oauth2_token', secret=COOKIE_SECRET))
    user = discord.get(API_URL + '/guilds/313032054172549120').text
    response.set_header('content-type', 'application/json')
    return user


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ['PORT']))
