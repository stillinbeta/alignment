import unittest

import asyncio
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from alignment.websocket import WebsocketHandler
from alignment.api import APIHandler
from alignment.redis import RedisPool
from redis_util import cleanup_redis_ns


class IntegrationTest(AioHTTPTestCase):
    maxDiff = None
    position_data = [
        {
            'user': {
                "username": "stillinbeta",
                "id": "11358",
                "avatar": "326a8bd3-ba24-4810-8e9a-14f47c7f8234",
            },
            'position': {
                'x': 100,
                'y': 200,
            }
        },
        {
            'user': {
                "username": "liztio",
                "id": "02144",
                "avatar": "326a8bd3-ba24-4810-8e9a-14f47c7f8234",
            },
            'position': {
                'x': 400,
                'y': 300,
            }
        },
        {
            'user': {
                "username": "liztio",
                "id": "021445",
                "avatar": "326a8bd3-ba24-4810-8e9a-14f47c7f8234",
            },
            'position': {
                'x': 400,
                'y': 500,
            }
        },
    ]

    async def get_application(self):
        self.prefix = 'test_room:'

        app = web.Application()
        redis = RedisPool(redis_url='redis://localhost')
        api = APIHandler(room_persist_prefix=self.prefix)
        ws = WebsocketHandler()
        redis.setup(app)
        api.setup(app)
        ws.setup(app)
        return app

    async def tearDownAsync(self):
        await cleanup_redis_ns(self.prefix)

    @unittest_run_loop
    async def test_ws_persist(self):
        resp = await self.client.post(
            '/api/v1/room/', json={'image': 'https://http.cat/201'})
        # TODO(EKF): this should just return 202 with the room parameter
        self.assertEqual(resp.status, 200)
        room = resp.url.path.split('/')[-1]
        url = self.client.make_url(self.app.router['ws'].url_for()).with_query(
            sid=1, room=room)
        async with self.client.session.ws_connect(url) as ws:
            for user in self.position_data:
                await ws.send_json(user)
        resp2 = await self.client.get(resp.url.path)
        self.assertEqual(resp.status, 200)
        decoded = await resp2.json()
        self.assertEqual(
            decoded, {
                'size': 128,
                'image': 'https://http.cat/201',
                'positions': self.position_data,
            })


if __name__ == "__main__":
    unittest.main()
