import numpy as np
import pandas as pd
from PyAstronomy import pyasl
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

colors = {
    'Blue': '#1f77b4',
    'Orange': '#ff7f0e',
    'Green': '#2ca02c',
    'Red': '#d62728',
    'Purple': '#9467bd',
}


def absolute_magnitude(parallax, m):
    d = 1 / parallax
    mu = 5 * np.log10(d) - 5
    M = m - mu
    return M


def readSC():
    df = cache.get('starDB')
    plots = cache.get('starCols')
    if (df is None) or (plots is None):
        names = ['Star', 'HD', 'RA', 'dec', 'Vmag', 'Vmagerr', 'par', 'parerr', 'source',
                 'teff', 'tefferr', 'logg', 'loggerr', 'logglc', 'logglcerr',
                 'vt', 'vterr', 'feh', 'feherr', 'mass', 'masserr', 'Author', 'link',
                 'flag', 'updated', 'Comment', 'tmp']
        df = pd.read_table('WEBSITE_online.rdb', names=names)
        df.drop('tmp', axis=1, inplace=True)
        df['flag'] = df['flag'] == 1  # Turn to bool
        df['Vabs'] = [absolute_magnitude(p, m) for p, m in df[['par', 'Vmag']].values]

        plots = ['Vmag', 'Vmagerr', 'Vabs', 'par', 'parerr', 'teff', 'tefferr',
                 'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
                 'feh', 'feherr', 'mass', 'masserr']
        cache.set('starDB', df, timeout=5*60)
        cache.set('starCols', plots, timeout=5*60)
    return df, plots


def planetAndStar(full=False):
    d = cache.get('planetDB')
    c = cache.get('planetCols')
    if (d is None) or (c is None):
        deu = pd.DataFrame(pyasl.ExoplanetEU().data)
        deu['plDensity'] = plDensity(deu['plMass'], deu['plRadius'])  # Add planet density
        cols = ['stName', 'plMass', 'plRadius', 'period', 'sma', 'eccentricity',
                'inclination', 'discovered', 'dist',
                'mag_v', 'mag_i', 'mag_j', 'mag_h', 'mag_k', 'plDensity']
        if not full:
            deu = deu[cols]
        deu['stName'] = [s.decode() for s in deu['stName']]
        df, columns = readSC()
        d = pd.merge(df, deu, left_on='Star', right_on='stName')
        c = columns + cols[1:]
        cache.set('planetDB', d, timeout=5*60)
        cache.set('planetCols', c, timeout=5*60)
    return d, c


def plDensity(mass, radius):
    """Calculate planet density.

    Assumes Jupiter mass and radius given."""
    Mjup_cgs = 1.8986e30     # Jupiter mass in g
    Rjup_cgs = 6.9911e9      # Jupiter radius in cm
    return 3 * Mjup_cgs * mass / (4 * np.pi * (Rjup_cgs * radius)**3)   # g/cm^3
