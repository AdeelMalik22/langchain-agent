import redis
import json
import functools
import inspect


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host="localhost",
            port=6379,
            db=0
        )

    def get(self,key):
        value = self.client.get(key)

        if value:
            return value.decode()

        return None


    def set(self,key,value,expire=None):
        self.client.set(
            key,
            value,
            ex=expire
        )


redis_client = RedisClient()



def cache(expire=60):

    def decorator(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):

            # Serialize args: expand Pydantic models to dicts for a stable key
            serialized_args = [
                a.model_dump() if hasattr(a, "model_dump") else repr(a)
                for a in args
            ]
            serialized_kwargs = {
                k: v.model_dump() if hasattr(v, "model_dump") else repr(v)
                for k, v in kwargs.items()
            }
            cache_key = (
                f"{func.__module__}."
                f"{func.__name__}:"
                f"{serialized_args}:"
                f"{serialized_kwargs}"
            )


            cached = redis_client.get(cache_key)

            if cached:
                print("CACHE HIT")
                return json.loads(cached)


            print("CACHE MISS")


            result = await func(
                *args,
                **kwargs
            )


            redis_client.set(
                cache_key,
                json.dumps(
                    result.dict()
                    if hasattr(result, "dict")
                    else result
                ),
                expire
            )


            return result


        return async_wrapper


    return decorator