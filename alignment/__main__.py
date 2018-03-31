import os
import base64

from aiohttp import web
from structlog import get_logger

from alignment.discord_user import DiscordUserHandler
from alignment.websocket import WebsocketHandler
from alignment.webapp import WebappHandler
from alignment.redis import RedisPool

log = get_logger()

COOKIE_SECRET = base64.urlsafe_b64decode(os.environ['COOKIE_SECRET'])
OAUTH_CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
OAUTH_CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']
REDIRECT_URI = '{}/auth'.format(os.environ['REDIRECT_URI'])
REDIS_URL = os.environ['REDIS_URL']
PORT = int(os.environ.get('PORT', 5000))

REDIS_POOL_MIN = int(os.environ.get('REDIS_POOL_MIN', 5))
REDIS_POOL_MAX = int(os.environ.get('REDIS_POOL_MAX', 10))

def run():
    discord_user = DiscordUserHandler(
        cookie_secret=COOKIE_SECRET,
        oauth_client_id=OAUTH_CLIENT_ID,
        oauth_client_secret=OAUTH_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )
    redis_pool = RedisPool(
        redis_url=REDIS_URL,
        redis_pool_min=REDIS_POOL_MIN,
        redis_pool_max=REDIS_POOL_MAX)

    websocket = WebsocketHandler()
    webapp = WebappHandler()

    app = web.Application()
    redis_pool.setup(app)
    discord_user.setup(app)
    websocket.setup(app)
    webapp.setup(app)

    log.info('starting app', port=PORT)
    web.run_app(app, host='0.0.0.0', port=PORT)

run()
