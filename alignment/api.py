import json
import uuid
import time

from aiohttp import web
import asyncio
from structlog import get_logger

from alignment.redis import REDIS_POOL_KEY
from alignment.room import RoomStore

log = get_logger()


class APIHandler:
    PERSIST_KEY = 'persist_task'

    def __init__(self,
                 pubsub_key='alignment_rooms',
                 room_persist_prefix='alignment:room'):
        self.pubsub_key = pubsub_key
        self.room_persist_prefix = room_persist_prefix

    def setup(self, app):
        app.on_startup.append(self.start_persist_position)
        # app.on_startup.append(self.setup_default_room)
        app.on_shutdown.append(self.end_persist_position)

        self.room_store = RoomStore(app, self.room_persist_prefix)

        app.router.add_get('/api/v1/room/{room}', self.get, name='room_api')
        app.router.add_post('/api/v1/room/', self.create)

    async def start_persist_position(self, app):
        app[self.PERSIST_KEY] = app.loop.create_task(self.persist(app))

    async def end_persist_position(self, app):
        app[self.PERSIST_KEY].cancel()
        await app[self.PERSIST_KEY]

    async def persist(self, app):
        """
        Listen on the Redis channel specified in :pubsub_key: for messages.
        When they're received, fan them out to all websockets in that room except the websocket that
        the message originated from (identified by SID)
        """
        redis = app[REDIS_POOL_KEY]
        try:
            channel, *_ = await redis.subscribe(self.pubsub_key)
            async for msg in channel.iter(
                    encoding='utf-8', decoder=json.loads):
                room = msg.pop('room', None)
                if room is None:
                    log.error("message missing userid or room",)
                    continue

                user = msg.get('user')
                position = msg.get('position')
                msg.pop('sid') # not needed for persistence
                if user is not None and room is not None:
                    await self.room_store.set_position(room, user, position)

        except asyncio.CancelledError:
            pass
        finally:
            await redis.unsubscribe(self.pubsub_key)


    async def get(self, request):
        name = request.match_info['room']
        room = await self.room_store.get_room(name)
        if room is None:
            raise web.HTTPNotFound

        return web.json_response(room)

    async def create(self, request):
        body = await request.json()
        image = body.get('image')
        if image is None:
            raise web.HTTPBadRequest(text='missing image parameter')
        room = str(uuid.uuid4())
        await self.room_store.create_room(room, image)

        resp = {
            'room': room,
            'api_url': str(request.app.router['room_api'].url_for(room=room))
        }

        room_app = request.app.router.get('app')
        if room_app is not None:
            resp['app_url'] = str(room_app.url_for(room=room).with_fragment(room))

        return web.json_response(resp)
