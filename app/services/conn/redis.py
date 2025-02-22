# redis.py
import redis

# Redis 配置
redis_client = redis.StrictRedis(
    host="192.168.10.112",
    port=6379,
    db=0,
    decode_responses=True,
    max_connections=50,  # 最大连接数
    socket_timeout=5,  # 超时设置（秒）
    socket_connect_timeout=5,  # 建立连接的超时设置（秒）
)
