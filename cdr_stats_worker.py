import redis
from redisbloom.client import Client
import os
import sys
from dotenv import load_dotenv

load_dotenv()

redisClient = Client.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def run(consumer, group='cdr_stats_worker', stream='events:cdr'):
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

    if not redisClient.exists('stats:callers:top50'):
        redisClient.topkReserve('stats:callers:top50', 50, 2000, 7, 0.925)

    while True:
        for offset in ['0', '>']:
            for _, entries in redisClient.xreadgroup(
                    group, consumer, {stream: offset}, block=0):
                for id, entry in entries:
                    print((id, entry))
                    # count all the callers
                    redisClient.incr('stats:callers:counter')
                    # add to HLL
                    redisClient.pfadd('stats:callers:unique', entry['a_party'])
                    # add to bloom filter
                    redisClient.bfAdd('stats:callers:set', entry['a_party'])
                    # add to bloom top-k
                    redisClient.topkAdd('stats:callers:top50', entry['a_party'])

                    redisClient.xack(stream, group, id)


if __name__ == "__main__":
    """
    Example: python cdr_stats_worker.py consumer1
    """
    run(sys.argv[1])
