#!/usr/bin/env python
import os
import argparse
from PyAstronomy import pyasl

from tornado.ioloop import IOLoop
from apscheduler.schedulers.tornado import TornadoScheduler


def tick():
    print('Downloading exoplanetEU')
    df = pyasl.ExoplanetEU2(forceUpdate=True)
    df = df.getAllDataPandas()
    df['name'] = [s.decode() if isinstance(s, bytes) else s for s in df['name']]
    df['star_name'] = [s.decode() if isinstance(s, bytes) else s for s in df['star_name']]
    path = 'sweetercat/data/exoplanetEU.csv'
    df.to_csv(path, index=False)
    print('Saved as exoplanetEU.csv')


def setup():
    home = os.path.expanduser('~')
    pya = os.path.join(home, 'PyAData')
    print('Setup starting...')
    if not os.path.exists(pya):
        print('Creating dir and config file')
        os.makedirs(pya)
        with open(os.path.join(home, '.pyaConfigWhere'), 'w') as f:
            f.write(pya)
    print('Setup done!')


def parse_args():
    """Take care of all the argparse stuff.

    :returns: the args Namespace
    """
    parser = argparse.ArgumentParser(description='Update DB on schedule.')
    parser.add_argument("-i", "--interval", help='Update interval in minutes',
                        type=int, default=15)
    parser.add_argument("-n", "--now", help='Update DB now only.', action="store_true")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    interval = args.interval

    # Prepare PyAstronomy
    setup()

    if args.now:
        # Single update
        tick()
    else:
        print('Starting scheduler...')
        scheduler = TornadoScheduler()
        scheduler.add_job(tick, 'interval', minutes=interval)
        scheduler.start()

        try:
            IOLoop.instance().start()
        except (KeyboardInterrupt, SystemExit):
            pass
