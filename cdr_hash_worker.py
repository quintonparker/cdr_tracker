import redis
import os
import sys
from dotenv import load_dotenv

load_dotenv()

redisClient = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def run(consumer, group='cdr_worker', stream='events:cdr'):
    """
    Subscribe to CDR events and write to hashes
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
                    pipe = redisClient.pipeline()
                    pipe.hset(f'cdr:{id}', mapping={
                        'a_party': entry['a_party'],
                        'b_party': entry['b_party'],
                        'trace_filter': entry['trace_filter'],
                        'start_time': int(entry['start_time']),
                        'duration': int(entry['duration']),
                        'status': int(entry['status'])
                        # TODO a_party country code enrichment
                        # TODO b_party country code enrichment
                    })
                    pipe.expire(f'cdr:{id}', 3600)
                    pipe.execute()
                    redisClient.xack(stream, group, id)


if __name__ == "__main__":
    """
    Example: python search_analytics_queries_worker.py consumer1
    """
    run(sys.argv[1])
