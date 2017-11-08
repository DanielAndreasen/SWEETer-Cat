import os
import shutil
import warnings
from PyAstronomy import pyasl
from astropy.io import votable

from tornado.ioloop import IOLoop
from apscheduler.schedulers.tornado import TornadoScheduler


def convert_to_csv(fname):
    d = os.path.dirname(fname)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vot = votable.parse(fname, invalid='mask')
    vot = vot.get_first_table().to_table(use_names_over_ids=True)
    df = vot.to_pandas()
    fout = os.path.join(d, 'exoplanetEU.csv')
    df.to_csv(fout, index=False)


def tick():
    print('Downloading exoplanetEU')
    _ = pyasl.ExoplanetEU2(forceUpdate=True)
    home = os.path.expanduser('~')
    path1 = os.path.join(home, 'PyAData/pyasl/resBased/epeu.vo.gz')
    path2 = 'sweetercat/data/exoplanetEU.vo.gz'
    shutil.copyfile(path1, path2)
    convert_to_csv(path2)
    os.remove(path2)
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


if __name__ == '__main__':
    # Prepare PyAstronomy
    setup()

    print('Starting scheduler...')
    scheduler = TornadoScheduler()
    scheduler.add_job(tick, 'interval', minutes=15)
    scheduler.start()

    try:
        IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        pass
