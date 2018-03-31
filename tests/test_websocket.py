import unittest
import uuid

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web


from alignment.redis import RedisPool
from alignment.websocket import WebsocketHandler


class WebsocketTest(AioHTTPTestCase):
    example_data = {
        "user": {
            "username": "stillinbeta",
            "discriminator": "1123",
            "mfa_enabled": True,
            "id": "11358",
            "avatar": "326a8bd3-ba24-4810-8e9a-14f47c7f8234",
        },
        "position": {
            "x": 100,
            "y": 205
        }
    }

    async def get_application(self):
        app = web.Application()
        redis = RedisPool(redis_url='redis://localhost')
        websocket = WebsocketHandler()
        redis.setup(app)
        websocket.setup(app)
        return app

    def ws(self, id_=1):
        return self.client.make_url('/ws?sid={}'.format(id_))

    @unittest_run_loop
    async def test_websocket_without_sid(self):
        resp = await self.client.request('GET', '/ws')
        self.assertEqual(resp.status, 400)

    @unittest_run_loop
    async def test_websocket_connect(self):
        async with self.client.session.ws_connect(self.ws()) as ws:
            await ws.close()

    @unittest_run_loop
    async def test_send_websocket_send_recieves(self):
        async with self.client.session.ws_connect(self.ws()) as ws1:
            async with self.client.session.ws_connect(self.ws(2)) as ws2:
                await ws1.send_json(self.example_data)
                recieved = await ws2.receive_json(timeout=5)
                self.assertEqual(recieved, self.example_data)


if __name__ == "__main__":
    unittest.main()
