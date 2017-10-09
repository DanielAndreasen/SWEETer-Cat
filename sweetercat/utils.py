from __future__ import division
import warnings
import numpy as np
import pandas as pd
from astropy.io import votable
from astropy import constants as c
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

colors = {
    'Blue': '#1f77b4',
    'Orange': '#ff7f0e',
    'Green': '#2ca02c',
    'Red': '#d62728',
    'Purple': '#9467bd',
}


def readExoplanetEU():
    """Read the exoplanet.eu database from the 'data' folder and store as
    pandas DataFrame
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vot = votable.parse('data/exoplanetEU.vo.gz', invalid='mask')
    vot = vot.get_first_table().to_table(use_names_over_ids=True)
    df = vot.to_pandas()
    return df


def absolute_magnitude(parallax, m):
    """Calculate the absolute magnitude based on distance and apparent mag.
    Inputs
    ------
    parallax : float
      The parallax in mas
    m : float
      The apparent magnitude

    Output
    ------
    M : float
      The absolute magnitude
    """
    d = 1 / (parallax*1e-3)  # Conversion to arcsecond before deriving distance
    mu = 5 * np.log10(d) - 5
    M = m - mu
    return M


def luminosity(mass, teff, logg):
    """Stellar luminosity based on standard formula:
            L=4\pi R^2 \sigma Teff^4
    scaled with Solar values.

    Inputs
    ------
    mass : int, float, np.ndarray
      Stellar mass in Solar units
    teff : int, float, np.ndarray
      Stellar effective temperature in K
    logg : int, float, np.ndarray
      Stellar surface gravity in cgs

    Output
    ------
    Stellar luminosity in Solar units
    """
    return mass * (teff/5777)**4 * (10**(4.44-logg))


def luminosity2(parallax, m):
    """Stellar luminosity based on magnitude (probably V) and parallax based on
            m = ms-2.5*log10(L/Ls*(d/ds)**2)

    Inputs
    ------
    parallax : int, float, np.ndarray
      Parallax in milli-arcsecond. Note: not arcseconds. It will be conversion
    m : in, float, np.ndarray
      Apparent magnitude. Usually from V band

    Output
    ------
    Stellar luminosity in Solar units
    """
    ds = 4.848136811133344e-06  # Distance to Sun in pc
    ms = -26.74
    d = 1/(parallax*1e-3)
    L = (d/ds)**2 * 10**((ms-m)/2.5)
    return L


def readSC(nrows=None):
    """Read the SWEET-Cat database and cache it (if it isn't already).

    Output
    ------
    df : pd.DataFrame
      The DataFrame of SWEET-Cat
    plots : list
      The columns that can be used for plotting
    """
    df = cache.get('starDB')
    plots = cache.get('starCols')
    if (df is None) or (plots is None):
        df = pd.read_table('data/sweet-cat.tsv')
        df.drop('tmp', axis=1, inplace=True)
        df['flag'] = df['flag'] == 1  # Turn to bool
        df['Vabs'] = absolute_magnitude(df['par'], df['Vmag'])
        df['lum'] = luminosity(df['mass'], df['teff'], df['logg'])
        df['Star'] = df['Star'].str.strip()

        plots = ['Vmag', 'Vmagerr', 'Vabs', 'par', 'parerr', 'teff', 'tefferr',
                 'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
                 'feh', 'feherr', 'mass', 'masserr', 'lum']
        cache.set('starDB', df, timeout=5*60)
        cache.set('starCols', plots, timeout=5*60)
    if nrows is not None:
        return df.loc[:nrows-1, :], plots
    return df, plots


def planetAndStar(how='inner'):
    """Read the SWEET-Cat and ExoplanetEU databases, merge them and cache them
    (if it isn't already).

    Input
    -----
    how : str (default: 'inner')
      How to merge the two DataFrames. See pd.merge for documentation

    Output
    ------
    d : pd.DataFrame
      The DataFrame of merged DataFrame
    c : list
      The columns that can be used for plotting
    """
    deu = cache.get('exoplanetDB')
    if deu is None:
        deu = readExoplanetEU()
        rename = {'name': 'plName',
                  'star_name': 'stName',
                  'mass': 'plMass',
                  'radius': 'plRadius',
                  'orbital_period': 'period',
                  'semi_major_axis': 'sma',
                  'eccentricity': 'eccentricity',
                  'inclination': 'inclination',
                  'discovered': 'discovered',
                  'impact_parameter': 'b',
                  'star_distance': 'dist',
                  'mag_v': 'mag_v',
                  'mag_i': 'mag_i',
                  'mag_j': 'mag_j',
                  'mag_h': 'mag_h',
                  'mag_k': 'mag_k'}
        deu.rename(columns=rename, inplace=True)
        idx = np.zeros(len(deu), dtype=bool)
        deu['plName'] = [s.decode() if isinstance(s, bytes) else s for s in deu['plName']]
        for i, planet in enumerate(deu['plName']):
            for pl in 'abcdefgh':
                if planet.endswith(' {}'.format(pl)):
                    idx[i] = True
                    continue
        deu.loc[idx, 'stName'] = deu.loc[idx, 'plName'].str[:-2]
        deu.loc[~idx, 'stName'] = deu.loc[~idx, 'plName']
        deu['plDensity'] = plDensity(deu['plMass'], deu['plRadius'])  # Add planet density
        cache.set('exoplanetDB', deu, timeout=5*60)

    cols = ['stName', 'plMass', 'plRadius', 'period', 'sma', 'eccentricity',
            'inclination', 'discovered', 'dist', 'b',
            'mag_v', 'mag_i', 'mag_j', 'mag_h', 'mag_k', 'plDensity']
    df, columns = readSC()
    d = pd.merge(df, deu, left_on='Star', right_on='stName', how=how)
    c = columns + cols[1:]
    return d, c


def plDensity(mass, radius):
    """Calculate planet density.

    Assumes Jupiter mass and radius given."""
    mjup_cgs = 1.8986e30     # Jupiter mass in g
    rjup_cgs = 6.9911e9      # Jupiter radius in cm
    return 3 * mjup_cgs * mass / (4 * np.pi * (rjup_cgs * radius)**3)  # g/cm^3


def stellar_radius(M, logg):
    """Calculate stellar radius given mass and logg"""
    if not isinstance(M, (int, float)):
        raise TypeError('Mass must be int or float. {} type given'.format(type(M)))
    if not isinstance(logg, (int, float)):
        raise TypeError('logg must be int or float. {} type given'.format(type(logg)))
    if M < 0:
        raise ValueError('Only positive stellar masses allowed.')

    R = M/(10**(logg-4.44))
    return R


def planetary_radius(mass, radius):
    """Calculate planetary radius if not given assuming a density dependent on
    mass"""
    if not isinstance(mass, (int, float)):
        if isinstance(radius, (int, float)):
            return radius
        else:
            return '...'
    if mass < 0:
        raise ValueError('Only positive planetary masses allowed.')

    Mj = c.M_jup
    Rj = c.R_jup
    if radius == '...' and isinstance(mass, (int, float)):
        if mass < 0.01:  # Earth density
            rho = 5.51
        elif 0.01 <= mass <= 0.5:
            rho = 1.64  # Neptune density
        else:
            rho = Mj/(4./3*np.pi*Rj**3)  # Jupiter density
        R = ((mass*Mj)/(4./3*np.pi*rho))**(1./3)  # Neptune density
        R /= Rj
    else:
        return radius
    return R.value


def hz(teff, lum, model=1):
    """Calculate inner and outer HZ limits using different models.

    Lum is in solar units.
    Reference: Kopparapu+ 2013
    http://adsabs.harvard.edu/abs/2013ApJ...765..131K
    """
    for parameter in (teff, lum):
        if not isinstance(parameter, (int, float)):
            return np.nan
    if not (2500 < teff < 7200):
        return np.nan

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

    seff_sun = p[0]
    ts = teff-5780
    a, b, c, d = p[1], p[2], p[3], p[4]
    seff = seff_sun + a*ts + b*ts**2 + c*ts**3 + d*ts**4
    dist = np.sqrt(lum/seff)
    return dist


def table_convert(fmt="csv"):
    """Convert the SC data into different formats.

    To make available for download.
    """
    # others netcdf, fits?
    # https://pandas.pydata.org/pandas-docs/stable/io.html
    if fmt not in ['tsv', 'csv', 'hdf']:
        raise NotImplementedError("Conversion format to {} not available.".format(fmt))
    name = "data/sweet-cat.{}".format(fmt)
    if fmt is "tsv":  # This is the standard
        pass
    else:
        df = pd.read_table('data/sweet-cat.tsv')
        if fmt == "hdf":
            df.to_hdf(name, key="sweetcat", mode="w", format='table')
        elif fmt == "csv":
            df.to_csv(name, sep=",", index=False)


def get_default(value, default, dtype, na_value='...'):
    if isinstance(value, dtype) and (value != na_value):
        return value
    else:
        return default
