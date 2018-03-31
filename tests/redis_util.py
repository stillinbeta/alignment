import aioredis

async def cleanup_redis_ns(prefix, url='redis://localhost'):
    redis = await aioredis.create_redis(url)
    try:
        async for key in redis.iscan(match=prefix + '*'):
            await redis.delete(key)
    finally:
        redis.close()
        await redis.wait_closed()
