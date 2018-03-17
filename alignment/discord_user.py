import uuid

from aiohttp import web
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_session

from alignment.discordclient import DiscordClient


class DiscordUserHandler:
    STATE_KEY = 'state'
    ACCESS_TOKEN_KEY = 'discord-access-token'

    def __init__(self,
                 cookie_secret,
                 oauth_client_id,
                 oauth_client_secret,
                 redirect_uri,
                 landing='/app'):
        self.cookie_secret = cookie_secret
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        self.redirect_uri = redirect_uri
        self.landing = landing

    def setup(self, app):
        aiohttp_session.setup(app, EncryptedCookieStorage(self.cookie_secret))
        app.router.add_get('/', self.root)
        app.router.add_get('/auth', self.auth)
        app.router.add_get('/me', self.user_info)

    def discord_client(self, **kwargs):
        return DiscordClient(
            client_id=self.oauth_client_id,
            client_secret=self.oauth_client_secret,
            **kwargs)

    async def root(self, request):
        session = await aiohttp_session.get_session(request)
        state = str(uuid.uuid4())
        session[self.STATE_KEY] = state
        discord = self.discord_client()
        params = {
            'client_id': self.oauth_client_id,
            'scope': 'identify email',
            'state': state,
        }
        raise web.HTTPFound(discord.get_authorize_url(**params))

    async def auth(self, request):
        if request.query.get('error'):
            raise web.HTTPUnauthorized(text=request.query.get('error'))
        session = await aiohttp_session.get_session(request)
        if not session[self.STATE_KEY] or str(
                session[self.STATE_KEY]) != request.query.get('state'):
            raise web.HTTPUnauthorized(
                text=
                "state did not match! Try clearing your cookies and try again."
            )
        discord = self.discord_client()
        token, _resp = await discord.get_access_token(
            request.query.get('code'))
        session[self.ACCESS_TOKEN_KEY] = token
        raise web.HTTPFound('/app')

    async def user_info(self, request):
        session = await aiohttp_session.get_session(request)
        token = session[self.ACCESS_TOKEN_KEY]
        if not token:
            raise web.HTTPFound('/')
        discord = self.discord_client(access_token=token)
        _user, userDict = await discord.user_info()
        return web.json_response(userDict)
