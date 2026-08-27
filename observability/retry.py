import time
import random

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


def call_with_backoff(fn, *args, **kwargs):
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            # crude transient check -- tighten once you see real error types
            transient = any(s in str(e).lower() for s in ("429", "rate", "unavailable", "timeout"))
            if not transient or attempt == MAX_RETRIES - 1:
                raise
            delay = BASE_DELAY_SECONDS * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)
    raise last_exc
