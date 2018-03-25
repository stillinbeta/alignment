import aioredis

REDIS_POOL_KEY = 'redis_pool'

class RedisPool:
    def __init__(self,
                 redis_url,
                 redis_pool_min=5,
                 redis_pool_max=10):
        self.redis_url = redis_url
        self.redis_pool_min = redis_pool_min
        self.redis_pool_max = redis_pool_max

    def setup(self, app):
        app.on_startup.append(self.create_redis_pool)
        app.on_cleanup.append(self.destroy_redis_pool)

    async def create_redis_pool(self, app):
        """Initialise a new redis pool using the parameters passed to the class"""
        redis = await aioredis.create_redis_pool(
            self.redis_url,
            minsize=self.redis_pool_min,
            maxsize=self.redis_pool_max,
            loop=app.loop)
        app[REDIS_POOL_KEY] = redis

    async def destroy_redis_pool(self, app):
        """Destroy this class's redis pool"""
        pool = app.get(REDIS_POOL_KEY)
        if pool is None:
            return
        pool.close()
        await pool.wait_closed()
