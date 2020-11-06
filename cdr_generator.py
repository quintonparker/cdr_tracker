import redis
import os
import sys
import random
import time
from dotenv import load_dotenv

load_dotenv()

redisClient = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)

parties = []

for i in range(10000):
    # todo generate only valid country codes
    country = str(random.randint(1, 100))
    segment1 = str(random.randint(0, 999)).zfill(3)
    segment2 = str(random.randint(0, 999)).zfill(3)
    segment3 = str(random.randint(0, 9999)).zfill(4)
    parties.append(f'+{country} {segment1}-{segment2}-{segment3}')


def generate_party():
    return random.choice(parties)


def generate_trace_filter():
    return random.randint(0, 100)


def generate_timings():
    duration = random.randint(0, 1200)
    start = int(time.time()) - duration
    return (start, duration)


def generate_status():
    return random.randint(0, 5)


def run(stream='events:cdr'):
    """
    Generate mock CDRs to a Redis stream
    """
    print(f'Starting cdr generator publishing to {stream}')

    while True:
        start, duration = generate_timings()
        redisClient.xadd(
            stream,
            {
                '_version': 'v1',
                'a_party': generate_party(),
                'b_party': generate_party(),
                'trace_filter': generate_trace_filter(),
                'start_time':  start,
                'duration': duration,
                'status': generate_status()
            },
            maxlen=10000
        )
        time.sleep(0.1)


if __name__ == "__main__":
    """
    Example: python cdr_generator.py events:cdr
    """
    run(sys.argv[1])
