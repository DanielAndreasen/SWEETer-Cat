import numpy as np
import pandas as pd
from astropy import constants as c
from cachelib import SimpleCache
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
    df = cache.get('exoplanetDB')
    if df is None:
        df = pd.read_csv('data/exoplanetEU.csv', engine='c')
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
        df.rename(columns=rename, inplace=True)
        idx = np.zeros(len(df), dtype=bool)
        for pl in 'abcdefgh':
            idx = idx | df['plName'].str.endswith(' {}'.format(pl))
        df.loc[idx, 'stName'] = df.loc[idx, 'plName'].str[:-2]
        df.loc[~idx, 'stName'] = df.loc[~idx, 'plName']
        df['plDensity'] = plDensity(df['plMass'], df['plRadius'])  # Add planet density
        cache.set('exoplanetDB', df, timeout=5*60)
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
    d = 1. / (parallax*1e-3)  # Conversion to arcsecond before deriving distance
    mu = 5 * np.log10(d) - 5
    return m - mu


def luminosity(teff, m, par, mass):
    """
    Calculate the luminosity the real way

    Inputs
    ------
    teff : int
      Effective temperature in K
    m : float
      Apparent magnitude
    par : float
      Parallax in arcsec
    mass : float
      Stellar mass in solar units

    Output
    ------
    lum : float
      Stellar luminosity in solar units
    """
    if teff == 0:
        return np.nan
    if mass == 0:
        return np.nan
    bcflow = bolcor(teff)
    dpc = 1./par
    mabs = m + 5 - 5*np.log10(dpc)
    mbol = mabs + bcflow
    return (10**(-2.*mbol/5.))*78.9336121


def bolcor(teff):
    """
    The bolometric correction

    Input
    -----
    teff : int
      Effective temperature in K

    Output
    ------
    bcflow : float
      The bolometric correction
    """
    lteff = np.log10(teff)
    if lteff < 3.7:
        p = [-0.190537291496456e+05, 0.155144866764412e+05, -0.421278819301717e+04, 0.381476328422343e+03]
    elif (3.7 <= lteff) and (lteff < 3.9):
        p = [-0.370510203809015e+05, 0.385672629965804e+05, -0.150651486316025e+05, 0.261724637119416e+04, -0.170623810323864e+03]
    else:
        p = [-0.118115450538963e+06, 0.137145973583929e+06, -0.636233812100225e+05, 0.147412923562646e+05, -0.170587278406872e+04, 0.788731721804990e+02]

    # The arrays are in form of:
    #   p[0] + p[1]*x + p[2]*x**2 + ...
    # But np.poly1d expects it reversed
    bcflow = np.poly1d(p[::-1])(lteff)
    return bcflow


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
        df = pd.read_table('data/sweet-cat.tsv', engine='c')
        df.drop('tmp', axis=1, inplace=True)
        df['flag'] = df['flag'] == 1  # Turn to bool
        df['Vabs'] = absolute_magnitude(df['par'], df['Vmag'])
        df['lum'] = list(map(luminosity, df['teff'], df['Vmag'], df['par']*1E-3, df['mass']))
        df['Star'] = df['Star'].str.strip()

        # Generate missing link https://github.com/DanielAndreasen/SWEETer-Cat/issues/135
        for star in df.Star[df['link'].isnull()].values:
            df.loc[df['Star'] == star, ['link']] = generate_missing_link(star)

        plots = ['Vmag', 'Vmagerr', 'Vabs', 'par', 'parerr', 'teff', 'tefferr',
                 'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
                 'feh', 'feherr', 'mass', 'masserr', 'lum']
        cache.set('starDB', df, timeout=5*60)
        cache.set('starCols', plots, timeout=5*60)

    if nrows is not None:
        return df.loc[:nrows-1, :], plots
    return df, plots


def planetAndStar(how='inner'):
    """Read the SWEET-Cat and ExoplanetEU databases and merge them.

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
    df, columns = readSC()
    deu = readExoplanetEU()
    cols = ['stName', 'plMass', 'plRadius', 'period', 'sma', 'eccentricity',
            'inclination', 'discovered', 'dist', 'b',
            'mag_v', 'mag_i', 'mag_j', 'mag_h', 'mag_k', 'plDensity']
    d = pd.merge(df, deu, left_on='Star', right_on='stName', how=how)
    d['radius'] = list(map(stellar_radius, d['mass'], d['logg']))
    d['teq0'] = d.teff * np.sqrt((d.radius*700000)/(2*d.sma*150000000))
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

    M = float(M)
    return M/(10**(logg-4.44))


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
    return np.sqrt(lum/seff)


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


def author_html(author, link):
    """
    Create HTML anchor tag for author with correct link to ADSABS

    Inputs
    ------
    author : str
      Name of the author(s)
    link : str
      Link to article

    Output
    ------
    alink : str
      Author anchor tag to link
    """
    if (',' in author) and (',' in link):
        authors = author.split(',')
        links = link.split(',')
        alinks = []
        for author, link in zip(authors, links):
            alinks.append('<a target="_blank" href="{}">{}</a>'.format(link.strip(), author.strip()))
        alink = ', '.join(alinks)
    else:
        alink = '<a target="_blank" href="{}">{}</a>'.format(link, author)
    return alink


def generate_missing_link(star=None):
    """Give exoplanet.eu link if link is missing.

    See https://github.com/DanielAndreasen/SWEETer-Cat/issues/135.

    Parameters
    ----------
    Star: str Optional
        Star name from Sweet-cat.

    Returns
    -------
    link: str
        Link to exoplanet.eu.
    """
    if star is None:
         return "http://exoplanet.eu/catalog/"
    else:
        star_formatted = star.lower().replace(" ", "_")
        return "http://exoplanet.eu/catalog/{}_b/".format(star_formatted)

