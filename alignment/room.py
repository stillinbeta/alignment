import json
import time

from alignment.redis import REDIS_POOL_KEY


class RoomStore:
    DEFAULT_SIZE = 128

    def __init__(self, app, room_prefix):
        self.app = app
        self.room_prefix = room_prefix

    @property
    def redis(self):
        return self.app[REDIS_POOL_KEY]

    def _get_room_meta_key(self, room):
        return self.room_prefix + ':meta:' + room

    def _get_position_key(self, room):
        return self.room_prefix + ':position:' + room

    def _get_position_sort_key(self, room):
        return self.room_prefix + ':position:sort:' + room

    async def create_room(self, name, image, size=None):
        if size is None:
            size = self.DEFAULT_SIZE
        await self.redis.hmset_dict(
            self._get_room_meta_key(name), image=image, size=size)

    @staticmethod
    def time():
        return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)

    async def set_position(self, name, user, position):
        id_ = user['id']
        encoded = json.dumps({'user': user, 'position': position})
        await self.redis.hset(self._get_position_key(name), id_, encoded)
        await self.redis.zadd(
            self._get_position_sort_key(name), self.time(), id_)

    async def get_room(self, name):
        meta_key = self._get_room_meta_key(name)
        exists = await self.redis.exists(meta_key)
        if not exists:
            return None

        image, size = await self.redis.hmget(
            meta_key,
            'image',
            'size',
            encoding='utf-8',
        )

        return {
            'image': image,
            'size': int(size),
            'positions': list([p async for p in self.get_positions(name)]),
        }

    async def get_positions(self, name):
        users = await self.redis.hgetall(self._get_position_key(name), encoding='utf-8')
        keys = await self.redis.zrangebyscore(self._get_position_sort_key(name), encoding='utf-8')
        for key in keys:
            if key in users:
                yield json.loads(users[key])
