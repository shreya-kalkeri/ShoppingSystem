import os
import redis


host = os.environ.get("REDIS_HOST")
port = 15697
password = os.environ.get("REDIS_PASSWORD")


def get_redis_database():
    return redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)


if __name__ == "__main__":
    pass
