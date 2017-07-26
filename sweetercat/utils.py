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
        df = pd.read_table('table/sweet-cat.tsv', names=names)
        df.drop('tmp', axis=1, inplace=True)
        df['flag'] = df['flag'] == 1  # Turn to bool
        df['Vabs'] = [absolute_magnitude(p, m) for p, m in df[['par', 'Vmag']].values]

        plots = ['Vmag', 'Vmagerr', 'Vabs', 'par', 'parerr', 'teff', 'tefferr',
                 'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
                 'feh', 'feherr', 'mass', 'masserr']
        cache.set('starDB', df, timeout=5*60)
        cache.set('starCols', plots, timeout=5*60)
    return df, plots


def planetAndStar(full=False, how='inner'):
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
        deu['stName'] = [s.decode() if isinstance(s, bytes) else s for s in deu['stName']]
        df, columns = readSC()
        d = pd.merge(df, deu, left_on='Star', right_on='stName', how=how)
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


def hz(teff, lum, model=1):
    """Calculate inner and outer HZ limits using different models.

    Lum is in solar units.
    Reference: Kopparapu+ 2013
    http://adsabs.harvard.edu/abs/2013ApJ...765..131K
    """
    if model == 1:  # Recent Venus
        p = [1.7753, 1.4316E-4, 2.9875E-9, -7.5702E-12, -1.1635E-15]
    elif model == 2:  # Runaway greenhouse
        p = [1.0512, 1.3242E-4, 1.5418E-9, -7.9895E-12, -1.8328E-15]
    elif model == 3:  # Moist greenhouse
        p = [1.0140, 8.1774E-5, 1.7063E-9, -4.3241E-12, -6.6462E-16]
    elif model == 4:  # Maximum greenhouse
        p = [0.3438, 5.8942E-5, 1.6558E-9, -3.0045E-12, -5.2983E-16]
    elif model == 5:  # Early Mars
        p = [0.3179, 5.4513E-5, 1.5313E-9, -2.7786E-12, -4.8997E-16]

    Seff_sun = p[0]
    ts = teff-5780
    a, b, c, d = p[1], p[2], p[3], p[4]
    Seff = Seff_sun + a*ts + b*ts**2 + c*ts**3 + d*ts**4
    dist = np.sqrt(lum/Seff)
    return dist
