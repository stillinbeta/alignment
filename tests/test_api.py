import unittest
import uuid

import aioredis
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from alignment.api import APIHandler
from alignment.redis import RedisPool
from redis_util import cleanup_redis_ns


class APITest(AioHTTPTestCase):
    async def get_application(self):
        self.prefix = 'test_room:'

        app = web.Application()
        redis = RedisPool(redis_url='redis://localhost')
        api = APIHandler(room_persist_prefix=self.prefix)
        redis.setup(app)
        api.setup(app)
        return app

    async def tearDownAsync(self):
        await cleanup_redis_ns(self.prefix)

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
        self.assertEqual(resp.status, 200)
        redirect = await resp.json()
        self.assertIn('room', redirect)
        self.assertIn('api_url', redirect)

        resp2 = await self.client.get(redirect['api_url'])
        self.assertEqual(resp2.status, 200)
        body = await resp2.json()
        self.assertEqual(body, {
            'image': 'https://http.cat/201',
            'size': 128,
            'positions': []
        })

if __name__ == '__main__':
    unittest.main()
