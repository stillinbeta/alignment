import os
import base64
import uuid
from pathlib import Path

from aiohttp import web
from aioauth_client import OAuth2Client
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

COOKIE_SECRET = base64.urlsafe_b64decode(os.environ['COOKIE_SECRET'])
OAUTH_CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
OAUTH_CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']
REDIRECT_URI = '{}/auth'.format(os.environ['REDIRECT_URI'])
PORT = int(os.environ.get('PORT', 5000))


def discord_client(**kwargs):
    return DiscordClient(
        client_id=OAUTH_CLIENT_ID, client_secret=OAUTH_CLIENT_SECRET, **kwargs)


with open('build/index.html') as idx:
    react_template = idx.read()


class DiscordClient(OAuth2Client):
    access_token_url = 'https://discordapp.com/api/oauth2/token'
    authorize_url = 'https://discordapp.com/api/oauth2/authorize'
    base_url = 'https://discordapp.com/api/v6/'
    name = 'discord'
    user_info_url = 'https://discordapp.com/api/v6/users/@me'

    @staticmethod
    def user_parse(data):
        yield 'id', data.get('id')
        yield 'username', data.get('username')
        yield 'discriminator', data.get('discriminator')
        yield 'picture', "https://cdn.discordapp.com/avatars/{}/{}.png".format(
            data.get('id'), data.get('avatar'))

    def request(self, method, url, headers=None, **aio_kwargs):
        """Request OAuth2 resource."""
        url = self._get_url(url)
        headers = headers or {'Accept': 'application/json'}
        if self.access_token:
            headers['Authorization'] = "Bearer {}".format(self.access_token)

        return self._request(method, url, headers=headers, **aio_kwargs)


async def root(request):
    session = await aiohttp_session.get_session(request)
    state = str(uuid.uuid4())
    session['state'] = state
    discord = discord_client()
    params = {
        'client_id': OAUTH_CLIENT_ID,
        'scope': 'identify email',
        'state': state,
    }
    raise web.HTTPFound(discord.get_authorize_url(**params))


async def auth(request):
    if request.query.get('error'):
        raise web.HTTPUnauthorized(text=request.query.get('error'))
    session = await aiohttp_session.get_session(request)
    if not session['state'] or str(
            session['state']) != request.query.get('state'):
        raise web.HTTPUnauthorized(
            text="state did not match! Try clearing your cookies and try again."
        )
    discord = discord_client()
    token, _resp = await discord.get_access_token(request.query.get('code'))
    session['oauth_access_token'] = token
    raise web.HTTPFound('/app')


async def app_page(request):
    return web.Response(text=react_template, content_type='text/html')


async def user_info(request):
    session = await aiohttp_session.get_session(request)
    token = session['oauth_access_token']
    if not token:
        raise web.HTTPFound('/')
    discord = discord_client(access_token=token)
    _user, userDict = await discord.user_info()
    return web.json_response(userDict)


def make_app():
    app = web.Application()
    aiohttp_session.setup(app, EncryptedCookieStorage(COOKIE_SECRET))
    app.router.add_get('/', root)
    app.router.add_get('/auth', auth)
    app.router.add_get('/app', app_page)
    app.router.add_get('/discord-user', app_page)
    app.router.add_static('/static', 'build/static')

    return app


if __name__ == '__main__':
    app = make_app()
    web.run_app(app, host='0.0.0.0', port=PORT)
