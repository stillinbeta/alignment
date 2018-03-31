import unittest
import uuid

import aioredis
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from alignment.api import APIHandler
from alignment.redis import RedisPool


class APITest(AioHTTPTestCase):
    async def get_application(self):
        self.prefix = 'test_room_'

        app = web.Application()
        redis = RedisPool(redis_url='redis://localhost')
        api = APIHandler(room_persist_prefix=self.prefix)
        redis.setup(app)
        api.setup(app)
        return app

    async def tearDownAsync(self):
        redis = await aioredis.create_redis('redis://localhost')
        try:
            async for key in redis.iscan(match=self.prefix + '*'):
                await redis.delete(key)
        finally:
            redis.close()
            await redis.wait_closed()

    @unittest_run_loop
    async def test_nonexistent_room(self):
        resp = await self.client.request('GET', '/api/v1/room/someroomid')
        self.assertEqual(resp.status, 404)

    @unittest_run_loop
    async def test_create_no_image(self):
        resp = await self.client.post('/api/v1/room/', json={})
        self.assertEqual(resp.status, 400)

    @unittest_run_loop
    async def test_create_get_room(self):
        resp = await self.client.post(
            '/api/v1/room/', json={'image': 'https://http.cat/201'})
        self.assertEqual(len(resp.history), 1)
        self.assertEqual(resp.history[0].status, 303)

        self.assertEqual(resp.status, 200)
        body = await resp.json()
        self.assertEqual(body, {
            'image': 'https://http.cat/201',
            'size': 128,
            'positions': []
        })


if __name__ == '__main__':
    unittest.main()
