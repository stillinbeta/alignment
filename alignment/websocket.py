import json
import itertools
from collections import namedtuple, defaultdict
import logging

import asyncio
from aiohttp import web, WSMsgType, WSCloseCode
from structlog import get_logger

from alignment.redis import REDIS_POOL_KEY

log = get_logger()

WebsocketHandle = namedtuple('WebsocketHandle', ['ws', 'sid'])


class WebsocketHandler:
    WEBSOCKET_KEY = 'websockets'
    LISTENER_KEY = 'redis-listener'

    def __init__(self, pubsub_key='alignment_rooms'):
        self.pubsub_key = pubsub_key

    def setup(self, app):
        app[self.WEBSOCKET_KEY] = defaultdict(list)
        app.router.add_get('/ws', self.handle_ws, name='ws')

        app.on_startup.append(self.start_send_messages)
        app.on_shutdown.append(self.close_open_websockets)
        app.on_shutdown.append(self.shutdown_send_messages)


    async def start_send_messages(self, app):
        app[self.LISTENER_KEY] = app.loop.create_task(self.send_messages(app))

    async def shutdown_send_messages(self, app):
        app[self.LISTENER_KEY].cancel()
        await app[self.LISTENER_KEY]

    async def send_messages(self, app):
        """
        Listen on the Redis channel specified in :pubsub_key: for messages.
        When they're received, fan them out to all websockets in that room except the websocket that
        the message originated from (identified by SID)
        """
        redis = await app[REDIS_POOL_KEY]
        try:
            channel, *_ = await redis.subscribe(self.pubsub_key)
            async for msg in channel.iter(
                    encoding='utf-8', decoder=json.loads):
                sid = msg.pop('sid', None)
                room = msg.pop('room', None)
                if sid is None or room is None:
                    log.error(
                        "message missing sid or room", sid=sid, room=room)
                    continue
                for ws in app[self.WEBSOCKET_KEY][room]:
                    if ws.ws.closed or ws.sid == sid:
                        continue
                    await ws.ws.send_json(msg)
        except asyncio.CancelledError:
            pass
        finally:
            await redis.unsubscribe(self.pubsub_key)

    async def close_open_websockets(self, app):
        """
        Iterate over all registered websockts and close them all.
        """
        for ws in itertools.chain(*app[self.WEBSOCKET_KEY].values()):
            await ws.ws.close(
                code=WSCloseCode.GOING_AWAY, message="server-shutdown")

    async def handle_ws(self, request):
        """
        Listen for room activity on a websocket. Every message that is
        recieved is annotated with the sid and the room then put onto the redis
        pubsub channel.
        """
        sid = request.query.get('sid')
        if sid is None:
            raise web.HTTPBadRequest(text='missing sid parameter')

        room = request.query.get('room', 'default')

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        handle = WebsocketHandle(ws, sid)

        request.app[self.WEBSOCKET_KEY][room].append(handle)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    decoded = json.loads(msg.data)
                    decoded.update(sid=sid, room=room)
                    await request.app[REDIS_POOL_KEY].publish_json(
                        self.pubsub_key, decoded)
                elif msg.type == WSMsgType.ERROR:
                    log.error("websocket error", error=msg.exception())
        finally:
            request.app[self.WEBSOCKET_KEY][room].remove(handle)

        return ws
