import redis
import json
import functools
import uuid
import asyncio


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host="localhost",
            port=6379,
            db=0
        )

    def get(self, key):
        value = self.client.get(key)

        if value:
            return value.decode()

        return None


    def set(self, key, value, expire=None):
        self.client.set(
            key,
            value,
            ex=expire
        )


    def acquire_lock(self, key, expire=30):
        """
        Try to create lock.
        Returns lock token if successful.
        """

        token = str(uuid.uuid4())

        acquired = self.client.set(
            key,
            token,
            nx=True,
            ex=expire
        )

        if acquired:
            return token

        return None


    def release_lock(self, key, token):
        """
        Delete lock only if we own it.
        """

        current = self.client.get(key)

        if current and current.decode() == token:
            self.client.delete(key)



redis_client = RedisClient()



def cache(expire=60):

    def decorator(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):

            serialized_args = [
                a.model_dump()
                if hasattr(a, "model_dump")
                else repr(a)
                for a in args
            ]

            serialized_kwargs = {
                k: (
                    v.model_dump()
                    if hasattr(v, "model_dump")
                    else repr(v)
                )
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


            lock_key = f"lock:{cache_key}"

            lock_token = redis_client.acquire_lock(
                lock_key,
                expire=30
            )


            # I am the worker
            if lock_token:

                try:

                    print("LOCK ACQUIRED")


                    # Double check cache
                    # maybe another worker filled it
                    cached = redis_client.get(cache_key)

                    if cached:
                        return json.loads(cached)


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


                finally:

                    print("LOCK RELEASE")

                    redis_client.release_lock(
                        lock_key,
                        lock_token
                    )


            else:

                # Another request is generating the cache
                print("WAITING FOR LOCK")


                for _ in range(50):

                    await asyncio.sleep(0.1)


                    cached = redis_client.get(
                        cache_key
                    )

                    if cached:
                        print("CACHE READY")
                        return json.loads(cached)


                raise Exception(
                    "Cache generation timeout"
                )


        return async_wrapper


    return decorator