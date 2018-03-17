import itertools
from collections import namedtuple, defaultdict

import aioredis
from aiohttp import web, WSMsgType, WSCloseCode
from structlog import get_logger

log = get_logger()

WebsocketHandle = namedtuple('WebsocketHandle', ['ws', 'sid'])

class WebsocketHandler:
    REDIS_POOL_KEY = 'redis_pool'
    WEBSOCKET_KEY = 'websockets'

    def __init__(self,
                 redis_url,
                 redis_pool_min=5,
                 redis_pool_max=10,
                 redis_room_key='alignment_rooms'):
        self.redis_url = redis_url
        self.redis_pool_min = redis_pool_min
        self.redis_pool_max = redis_pool_max
        self.redis_room_key = redis_room_key

    def setup(self, app):
        app[self.WEBSOCKET_KEY] = defaultdict(list)
        app.router.add_get('/ws', self.handle_ws)
        app.on_startup.append(self.create_redis_pool)
        app.on_shutdown.append(self.destroy_redis_pool)
        app.on_shutdown.append(self.close_open_websockets)

    async def create_redis_pool(self, app):
        """Initialise a new redis pool using the parameters passed to the class"""
        redis = await aioredis.create_redis_pool(
            self.redis_url,
            minsize=self.redis_pool_min,
            maxsize=self.redis_pool_max,
            loop=app.loop)
        app[self.REDIS_POOL_KEY] = redis

    async def destroy_redis_pool(self, app):
        """Destroy this class's redis pool"""
        pool = app.get(self.REDIS_POOL_KEY)
        if pool is None:
            return
        pool.close()
        await pool.wait_closed()

    async def send_messages(self, app):
        """Listen on the Redis channel specified in :redis_room_key: for messages.
        When they're received, fan them out to all websockets in that room except the websocket that
        the message originated from (identified by SID)
        """
        redis = await app['redis_pool'].acquire()
        try:
            channel, *_ = await redis.subscribe(REDIS_ROOM_KEY)
            async for msg in ch.iter(encoding='utf-8', decoder=json.loads):
                sid = msg.pop('sid', None)
                room = msg.pop('room', None)
                if sid is None or room is None:
                    log.error(
                        "message missing sid or room", sid=sid, room=room)
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

    async def close_open_websockets(self, app):
        for ws in itertools.chain(app[self.WEBSOCKET_KEY].values()):
            await ws.ws.close(
                code=WSCloseCode.GOING_AWAY, message="server-shutdown")

    async def handle_ws(self, request):
        sid = request.query.get('sid')
        if sid is None:
            raise web.HTTPBadRequest('missing SID')

        room = 'default'

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        handle = WebsocketHandle(ws, sid)

        request.app[self.WEBSOCKET_KEY][room].append(handle)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    decoded = json.loads(msg.data)
                    decoded.update(sid=sid, room=room)
                    await app[self.REDIS_POOL_KEY].publish_json(rooms, decoded)
                elif msg.type == WSMsgType.ERROR:
                    log.error("websocket error", error=msg.exception())
        finally:
            request.app[self.WEBSOCKETS_KEY][room].remove(handle)

        log.info('websocket connection closed')
        return ws
