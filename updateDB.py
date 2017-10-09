import os
from PyAstronomy import pyasl

from tornado.ioloop import IOLoop
from apscheduler.schedulers.tornado import TornadoScheduler


def tick():
    # os.system('echo %s >> time.txt' % datetime.now())
    _ = pyasl.ExoplanetEU2(forceUpdate=True)
    path1 = '$HOME/PyAData/pyasl/resBased/epeu.vo.gz'
    path2 = 'sweetercat/data/exoplanetEU.vo.gz'
    os.system('cp {} {}'.format(path1, path2))


if __name__ == '__main__':
    # Prepare PyAstronomy
    os.system('mkdir -p $HOME/PyAData')
    os.system('echo -n $HOME/PyAData > $HOME/.pyaConfigWhere')

    scheduler = TornadoScheduler()
    scheduler.add_job(tick, 'interval', hours=1)
    scheduler.start()

    try:
        IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        pass
