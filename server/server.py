import os
import base64
import uuid
from pathlib import Path
import asyncio
from collections import namedtuple, defaultdict
import itertools

import aioredis
from aiohttp import web, WSMsgType, WSCloseCode
from aioauth_client import OAuth2Client
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from structlog import get_logger

COOKIE_SECRET = base64.urlsafe_b64decode(os.environ['COOKIE_SECRET'])
OAUTH_CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
OAUTH_CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']
REDIRECT_URI = '{}/auth'.format(os.environ['REDIRECT_URI'])
REDIS_URL = os.environ['REDIS_URL']
PORT = int(os.environ.get('PORT', 5000))

REDIS_POOL_MIN = int(os.environ.get('REDIS_POOL_MIN', 5))
REDIS_POOL_MAX = int(os.environ.get('REDIS_POOL_MAX', 10))
REDIS_ROOM_KEY = 'alignment-rooms'

log = get_logger()

WebsocketHandle = namedtuple('WebsocketHandle', ['ws', 'sid'])


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


async def avatar_ws(request):
    sid = request.query.get('sid')
    if sid is None:
        raise web.HTTPBadRequest('missing SID')

    room = 'default'

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    handle = WebsocketHandle(ws, sid)

    request.app['websockets'][room].append(handle)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                decoded = json.loads(msg.data)
                decoded.update(sid=sid, room=room)
                await app['redis_pool'].publish_json(rooms, decoded)
            elif msg.type == WSMsgType.ERROR:
                log.error("websocket error", error=msg.exception())
    finally:
        request.app['websockets'][room].remove(handle)

    log.info('websocket connection closed')
    return ws


async def close_open_websockets(app):
    for ws in itertools.chain(app['websockets'].values()):
        await ws.ws.close(
            code=WSCloseCode.GOING_AWAY, message="server-shutdown")


async def create_redis_pool(app):
    redis = await aioredis.create_redis_pool(
        REDIS_URL,
        minsize=REDIS_POOL_MIN,
        maxsize=REDIS_POOL_MAX,
        loop=app.loop)
    app['redis_pool'] = redis


async def send_messages(app):
    redis = await app['redis_pool'].acquire()
    try:
        channel, *_ = await redis.subscribe(REDIS_ROOM_KEY)
        async for msg in ch.iter(encoding='utf-8', decoder=json.loads):
            sid = msg.pop('sid', None)
            room = msg.pop('room', None)
            if sid is None or room is None:
                log.error("message missing sid or room", sid=sid, room=room)
                continue
            for ws in app[REDIS_ROOM_KEY][room]:
                if ws.ws.closed or ws.sid == sid:
                    continue
                await ws.ws.send_json(msg)
    except asyncio.CancelledError:
        pass
    finally:
        await redis.unsubscribe(REDIS_ROOM_KEY)
        app['redis_pool'].release(redis)


async def destroy_redis_pool(app):
    pool = app.get('redis_pool')
    if pool is None:
        return
    pool.close()
    await pool.wait_closed()


def make_app():
    app = web.Application()
    aiohttp_session.setup(app, EncryptedCookieStorage(COOKIE_SECRET))
    app.router.add_get('/', root)
    app.router.add_get('/auth', auth)
    app.router.add_get('/app', app_page)
    app.router.add_get('/discord-user', app_page)
    app.router.add_get('/ws', avatar_ws)
    app.router.add_static('/static', 'build/static')

    app['websockets'] = defaultdict(list)
    app.on_startup.append(create_redis_pool)
    app.on_shutdown.append(destroy_redis_pool)
    app.on_shutdown.append(close_open_websockets)
    return app


if __name__ == '__main__':
    app = make_app()
    log.info('starting app', port=PORT)
    web.run_app(app, host='0.0.0.0', port=PORT)
