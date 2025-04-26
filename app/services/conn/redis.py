from redis.asyncio import StrictRedis

from app.config import settings

redis_client = StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    max_connections=50,  # 最大连接数
    socket_timeout=5,  # 超时设置（秒）
    socket_connect_timeout=5,  # 建立连接的超时设置（秒）
)
