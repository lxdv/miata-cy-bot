import json
import os

import redis


class RedisClient:
    def __init__(self, password, host="localhost", port=6379, db=0):
        self.client = redis.Redis(
            host=host, port=port, password=password, decode_responses=True, db=db
        )

    def get_subscribers(self, subscribers_key="subscribers"):
        if self.client.exists(subscribers_key):
            return set(json.loads(self.client.get(subscribers_key)))
        return set()

    def set_subscribers(self, subscribers, subscribers_key="subscribers"):
        self.client.set(subscribers_key, json.dumps(list(subscribers)))

    def get_seen(self, seen_key="seen"):
        if self.client.exists(seen_key):
            return set(json.loads(self.client.get(seen_key)))
        return None

    def set_seen(self, urls, seen_key="seen"):
        self.client.set(seen_key, json.dumps(list(urls)))

    def get_posts(self, posts_key="posts"):
        if self.client.exists(posts_key):
            return json.loads(self.client.get(posts_key))
        return []

    def set_posts(self, posts, posts_key="posts"):
        self.client.set(posts_key, json.dumps(list(posts)))
