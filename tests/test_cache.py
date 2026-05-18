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