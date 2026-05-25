"""
Tests for memory_client rate limit — race condition fix.
"""

import pytest
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.memory_client import MemoryCacheClient
from src.cache.redis_client import RedisCacheClient
from src.cache.upstash_kv_client import UpstashCacheClient


class TestMemoryCacheClientRateLimit:
    """Test that check_rate_limit is thread-safe under concurrent access."""

    def test_rate_limit_basic(self):
        """Basic rate limit should allow requests under threshold."""
        key = f"test_basic_{time.time()}"
        # Use a very short window for testing
        MemoryCacheClient.check_rate_limit(key, 3600, 5)
        # Should not raise

    def test_rate_limit_exceeded(self):
        """Should raise 429 when exceeding threshold."""
        key = f"test_exceeded_{time.time()}"
        from fastapi import HTTPException

        # Use a 1-second window, 2 requests max
        for _ in range(2):
            MemoryCacheClient.check_rate_limit(key, 1, 2)

        with pytest.raises(HTTPException) as exc_info:
            MemoryCacheClient.check_rate_limit(key, 1, 2)
        assert exc_info.value.status_code == 429

    def test_rate_limit_concurrent(self):
        """Concurrent requests should not cause race condition (all counted correctly)."""
        key = f"test_concurrent_{time.time()}"
        errors = []
        raised_count = [0]

        def make_request():
            try:
                MemoryCacheClient.check_rate_limit(key, 3600, 10)
            except Exception as e:
                errors.append(e)
                raised_count[0] += 1

        # Launch 15 concurrent requests (limit is 10)
        threads = [threading.Thread(target=make_request) for _ in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly 5 rejections (15 - 10 = 5)
        rejections = raised_count[0]
        assert rejections == 5, f"Expected 5 rejections, got {rejections}. Errors: {errors}"

    def test_rate_limit_lock_exists(self):
        """_rate_limit_lock should be a threading.Lock (not asyncio.Lock)."""
        assert hasattr(MemoryCacheClient, "_rate_limit_lock")
        lock = MemoryCacheClient._rate_limit_lock
        lock_type_name = type(lock).__name__
        assert lock_type_name == "lock", f"Expected 'lock', got '{lock_type_name}'"


class FakeRedisPipeline:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.commands = []

    def zremrangebyscore(self, key, min_score, max_score):
        self.commands.append(("zremrangebyscore", key, min_score, max_score))

    def zadd(self, key, mapping):
        self.commands.append(("zadd", key, mapping))

    def expire(self, key, seconds):
        self.commands.append(("expire", key, seconds))

    def zcard(self, key):
        self.commands.append(("zcard", key))

    def execute(self):
        results = []
        for command in self.commands:
            name = command[0]
            if name == "zremrangebyscore":
                _, key, _min_score, max_score = command
                zset = self.redis_client.zsets.setdefault(key, {})
                expired_members = [
                    member for member, score in zset.items()
                    if score <= max_score
                ]
                for member in expired_members:
                    zset.pop(member, None)
                results.append(len(expired_members))
            elif name == "zadd":
                _, key, mapping = command
                self.redis_client.zsets.setdefault(key, {}).update(mapping)
                results.append(len(mapping))
            elif name == "expire":
                results.append(True)
            elif name == "zcard":
                _, key = command
                results.append(len(self.redis_client.zsets.get(key, {})))
        return results


class FakeRedis:
    def __init__(self):
        self.zsets = {}

    def pipeline(self):
        return FakeRedisPipeline(self)


class TestRedisCacheClientRateLimit:
    def test_same_second_requests_are_counted_with_unique_members(self, monkeypatch):
        """Redis rate limiting should not overwrite requests in the same second."""
        fake_redis = FakeRedis()
        monkeypatch.setattr(RedisCacheClient, "redis_client", fake_redis)
        monkeypatch.setattr(RedisCacheClient, "init_redis", classmethod(lambda cls: None))
        monkeypatch.setattr("src.cache.redis_client.time.time", lambda: 1000)

        key = "redis_same_second"
        RedisCacheClient.check_rate_limit(key, 60, 2)
        RedisCacheClient.check_rate_limit(key, 60, 2)

        assert len(fake_redis.zsets[key]) == 2

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            RedisCacheClient.check_rate_limit(key, 60, 2)
        assert exc_info.value.status_code == 429


class FakeUpstashResponse:
    def __init__(self, payload, status_code=200, text=""):
        self.payload = payload
        self.status_code = status_code
        self.text = text

    def json(self):
        return self.payload


class TestUpstashCacheClient:
    def test_token_commands_are_sent_as_json(self, monkeypatch):
        calls = []

        def fake_post(url, json=None, headers=None):
            calls.append({"url": url, "json": json, "headers": headers})
            if json[0] == "SET":
                return FakeUpstashResponse({"result": "OK"})
            return FakeUpstashResponse({"result": "stored-token"})

        monkeypatch.setattr("src.cache.upstash_kv_client.requests.post", fake_post)

        UpstashCacheClient.store_token('user:"quoted"', 'token:"quoted"', 60)
        token = UpstashCacheClient.get_token('user:"quoted"')

        assert token == "stored-token"
        assert calls[0]["json"] == ["SET", 'user:"quoted"', 'token:"quoted"', "EX", 60]
        assert calls[1]["json"] == ["GET", 'user:"quoted"']

    def test_same_second_requests_are_counted_with_unique_members(self, monkeypatch):
        """Upstash rate limiting should use unique ZADD members in the same second."""
        members = set()

        def fake_post(url, json=None, headers=None):
            zadd_command = json[1]
            members.add(zadd_command[3])
            return FakeUpstashResponse([
                {"result": 0},
                {"result": 1},
                {"result": 1},
                {"result": len(members)},
            ])

        monkeypatch.setattr("src.cache.upstash_kv_client.requests.post", fake_post)
        monkeypatch.setattr("src.cache.upstash_kv_client.time.time", lambda: 1000)

        key = "upstash_same_second"
        UpstashCacheClient.check_rate_limit(key, 60, 2)
        UpstashCacheClient.check_rate_limit(key, 60, 2)

        assert len(members) == 2

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            UpstashCacheClient.check_rate_limit(key, 60, 2)
        assert exc_info.value.status_code == 429
