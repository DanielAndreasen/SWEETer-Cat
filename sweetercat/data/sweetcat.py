from __future__ import division, print_function
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['xtick.major.width'] = 2
plt.rcParams['ytick.major.width'] = 2


def parser():
    c = ['Vabs', 'Vmag', 'Vmagerr', 'par', 'parerr', 'teff', 'tefferr', 'lum',
        'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr', 'feh', 'feherr',
        'mass', 'masserr', 'radius', 'plMass', 'plRadius',  'period', 'sma',
        'eccentricity', 'inclination', 'discovered', 'omega', 'tperi', 'b',
        'geometric_albedo', 'mag_v', 'mag_i', 'mag_j', 'mag_h', 'mag_k', 'dist',
        'plDensity', 'hz1', 'hz2']
    parser = argparse.ArgumentParser(description='Script for working with SWEET-Cat')
    parser.add_argument('-o', '--output', action='store_true',
                help='Save the output in sweet-cat-combined.csv')
    parser.add_argument('-x', choices=c,
                help='x value to plot')
    parser.add_argument('-y', choices=c,
                help='y value to plot')
    return parser.parse_args()


def readSC():
    """Read the SWEET-Cat database.
    """
    df = pd.read_csv('sweet-cat.csv')
    df['Vabs'] = absolute_magnitude(df.par, df.Vmag)
    df['radius'] = map(lambda x, y: stellar_radius(x, y), df['mass'], df['logg'])
    return df


def readExo():
    """Read the exoplanet.eu database and store as pandas DataFrame.
    """
    return pd.read_csv('exoplanetEU.csv')


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


def combine(df1, df2, how='inner'):
    """Read the SWEET-Cat and ExoplanetEU databases, merge them and cache them
    (if it isn't already).

    Input
    -----
    df1 : pd.DataFrame
      SWEET-Cat DataFrame
    df2 : pd.DataFrame
      ExoplanetEU DataFrame
    how : str (default: 'inner')
      How to merge the two DataFrames. See pd.merge for documentation

    Output
    ------
    df : pd.DataFrame
      The DataFrame of merged DataFrame
    """
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
    df2.rename(columns=rename, inplace=True)
    idx = np.zeros(len(df2), dtype=bool)
    df2['plName'] = [s.decode() if isinstance(s, bytes) else s for s in df2['plName']]
    for i, planet in enumerate(df2['plName']):
        for pl in 'abcdefgh':
            if planet.endswith(' {}'.format(pl)):
                idx[i] = True
                continue
    df2.loc[idx, 'stName'] = df2.loc[idx, 'plName'].str[:-2]
    df2.loc[~idx, 'stName'] = df2.loc[~idx, 'plName']
    df2['plDensity'] = plDensity(df2['plMass'], df2['plRadius'])  # Add planet density
    df = pd.merge(df1, df2, left_on='Star', right_on='stName', how=how)
    df['lum'] = (df.teff/5777)**4 * (df.mass/((10**df.logg)/(10**4.44)))**2
    df['hz1'] = map(lambda x, y: round(hz(x, y, 2), 5), df['teff'], df['lum'])
    df['hz2'] = map(lambda x, y: round(hz(x, y, 4), 5), df['teff'], df['lum'])
    return df


def plDensity(mass, radius):
    """Calculate planet density.

    Assumes Jupiter mass and radius given."""
    mjup_cgs = 1.8986e30     # Jupiter mass in g
    rjup_cgs = 6.9911e9      # Jupiter radius in cm
    return 3 * mjup_cgs * mass / (4 * np.pi * (rjup_cgs * radius)**3)  # g/cm^3


def stellar_radius(M, logg):
    """Calculate stellar radius given mass and logg"""
    try:
        M = float(M)
        R = M/(10**(logg-4.44))
    except ValueError:
        return np.nan
    return R


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


def hist(arr):
    arr = arr.dropna().values
    plt.hist(arr, histtype='step', lw=3)
    plt.tight_layout()
    plt.show()


def plot(x, y):
    plt.scatter(x, y, alpha=0.7)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    print('Thanks for using SWEET-Cat')
    print('Feel free to use this script as a starting point for your research')
    args = parser()

    df1 = readSC()
    df2 = readExo()
    df = combine(df1, df2)

    if args.output:
        print('\nSaving combined data set to sweet-cat-combined.csv')
        df.to_csv('sweet-cat-combined.csv', index=False)
        print('To read use the following snippet:')
        print('\timport pandas as pd')
        print("\tdf = pd.read_csv('sweet-cat-combined.csv')")

    if args.x and not args.y:
        hist(df[args.x])
    elif not args.x and args.y:
        hist(df[args.y])
    elif args.x:
        plot(df[args.x], df[args.y])
