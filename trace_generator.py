import redis
import os
import sys
import random
import time
from dotenv import load_dotenv

load_dotenv()

redisClient = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def generate_trace_filter():
    return random.randint(0, 100)


def generate_status():
    return random.randint(0, 5)


def generate_jitter():
    return random.randint(0, 10)


def generate_latency():
    return random.randint(10, 500)


def run(stream='events:trace'):
    """
    Generate mock Traces to a Redis stream
    """
    print(f'Starting cdr generator publishing to {stream}')

    while True:
        redisClient.xadd(
            stream,
            {
                '_version': 'v1',
                'status': generate_status(),
                'filter': generate_trace_filter(),
                'jitter_ms': generate_jitter(),
                'latency_ms':  generate_latency()
            },
            maxlen=10000
        )
        time.sleep(1)


if __name__ == "__main__":
    """
    Example: python trace_generator.py events:trace
    """
    run(sys.argv[1])
