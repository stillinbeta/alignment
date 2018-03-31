import json
import uuid
import time

from aiohttp import web
import asyncio
from structlog import get_logger

from alignment.redis import REDIS_POOL_KEY

log = get_logger()


class APIHandler:
    DEFAULT_SIZE = 128
    PERSIST_KEY = 'persist_task'

    def __init__(self,
                 pubsub_key='alignment_rooms',
                 room_persist_prefix='alignment:room'):
        self.pubsub_key = pubsub_key
        self.room_persist_prefix = room_persist_prefix

    def setup(self, app):
        app.on_startup.append(self.start_persist_position)
        app.on_shutdown.append(self.end_persist_position)

        app.router.add_get('/api/v1/room/{room}', self.get, name='room')
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
        redis = await app[REDIS_POOL_KEY]
        try:
            channel, *_ = await redis.subscribe(self.pubsub_key)
            async for msg in channel.iter(
                    encoding='utf-8', decoder=json.loads):
                userid = msg.get('user', {}).get('id')
                room = msg.pop('room', None)
                msg.pop('sid') # not needed for persistence
                if userid is None or room is None:
                    log.error(
                        "message missing userid or room",
                        user_id=user_id,
                        room=room)
                    continue

                await self._set_position(app, room, userid, msg)

        except asyncio.CancelledError:
            pass
        finally:
            await redis.unsubscribe(self.pubsub_key)

    def _get_room_meta_key(self, room):
        return self.room_persist_prefix + ':meta:' + room

    def _get_position_key(self, room):
        return self.room_persist_prefix + ':position:' + room

    def _get_position_sort_key(self, room):
        return self.room_persist_prefix + ':position:sort:' + room

    async def _set_position(self, app, room, userid, msg):
        encoded = json.dumps(msg)
        await app[REDIS_POOL_KEY].hset(
            self._get_position_key(room), userid, encoded)
        await app[REDIS_POOL_KEY].zadd(
            self._get_position_sort_key(room),
            time.clock_gettime(time.CLOCK_MONOTONIC_RAW), userid)

    async def _get_positions(self, redis, room):
        users = await redis.hgetall(self._get_position_key(room), encoding='utf-8')
        positions = await redis.zrangebyscore(self._get_position_sort_key(room), encoding='utf-8')
        for position in positions:
            if position in users:
                yield json.loads(users[position])

    async def get(self, request):
        room = request.match_info['room']
        meta_key = self._get_room_meta_key(room)
        exists = await request.app[REDIS_POOL_KEY].exists(meta_key)
        if not exists:
            raise web.HTTPNotFound

        image, size = await request.app[REDIS_POOL_KEY].hmget(
            meta_key,
            'image',
            'size',
            encoding='utf-8',
        )

        positions = [pos async for pos in self._get_positions(request.app[REDIS_POOL_KEY], room)]

        return web.json_response({
            'image': image,
            'size': int(size),
            'positions': list(positions),
        })

    async def create(self, request):
        body = await request.json()
        image = body.get('image')
        if image is None:
            raise web.HTTPBadRequest(text='missing image parameter')
        room = str(uuid.uuid4())
        key = self._get_room_meta_key(room)
        await request.app[REDIS_POOL_KEY].hmset_dict(
            key, image=image, size=self.DEFAULT_SIZE)
        raise web.HTTPSeeOther(request.app.router['room'].url_for(room=room))
