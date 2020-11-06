import redis
import os
import sys
from dotenv import load_dotenv

load_dotenv()

redisClient = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def run(consumer, group='trace_worker', stream='events:trace'):
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

    while True:
        for offset in ['0', '>']:
            for _, entries in redisClient.xreadgroup(
                    group, consumer, {stream: offset}, block=0):
                for id, entry in entries:
                    print((id, entry))
                    redisClient.hset(f'trace:{entry["filter"]}', mapping={
                        'jitter_ms': int(entry['jitter_ms']),
                        'latency_ms': int(entry['latency_ms']),
                        'status': int(entry['status'])
                        # TODO enrichment field
                    })
                    redisClient.xack(stream, group, id)


if __name__ == "__main__":
    """
    Example: python search_analytics_queries_worker.py consumer1
    """
    run(sys.argv[1])
