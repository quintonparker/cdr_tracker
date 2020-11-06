import redis
from redistimeseries.client import Client
import os
import sys
from dotenv import load_dotenv

load_dotenv()

redisClient = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)
rts = Client(redisClient)


def run(consumer, group='trace_stats_worker', stream='events:trace'):
    """
    Subscribe to Trace events and write to hashes
    """
    print(f'Starting {group}/{consumer} consumer listen on {stream}')
    try:
        redisClient.xgroup_create(stream, group, id='0', mkstream=True)
    except redis.exceptions.ResponseError as error:
        print(error)
        if not str(error) == 'BUSYGROUP Consumer Group name already exists':
            raise error

    if not redisClient.exists('stats:jitter'):
        rts.create('stats:jitter', retention=3600, labels={'type': 'trace'})

    if not redisClient.exists('stats:latency'):
        rts.create('stats:latency', retention=3600, labels={'type': 'trace'})

    while True:
        for offset in ['0', '>']:
            for _, entries in redisClient.xreadgroup(
                    group, consumer, {stream: offset}, block=0):
                for id, entry in entries:
                    print((id, entry))
                    ts = id[:id.index('-')]
                    rts.add('stats:jitter', ts, entry['jitter_ms'])
                    rts.add('stats:latency', ts, entry['latency_ms'])
                    redisClient.xack(stream, group, id)


if __name__ == "__main__":
    """
    Example: python trace_stats_worker.py consumer1
    """
    run(sys.argv[1])
