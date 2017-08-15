from flask import Flask, render_template, request, url_for, redirect, send_from_directory, after_this_request
import os
import json
from plot import plot_page
from utils import readSC, planetAndStar, hz, table_convert


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SC_secret']


@app.before_first_request
def cache_data():
    # This will cache the databases when the app starts
    _ = planetAndStar()


@app.route('/')
def homepage(star=None):
    """Home page for SWEETer-Cat with updated table"""
    df, columns = readSC()
    dfs = df.sort_values('updated', ascending=False)[:50]  # TODO: Remove the slicing!
    decimals = dict.fromkeys(['Vmag', 'Vmagerr', 'par', 'parerr', 'logg',
                              'loggerr', 'logglc', 'logglcerr', 'vterr', 'feh',
                              'feherr', 'mass', 'masserr'], 2)
    dfs = dfs.round(decimals=decimals)
    for col in ('teff', 'tefferr'):  # These should be integers
        idx = dfs[col].isnull()
        dfs[col] = dfs[col].astype(str)
        dfs.loc[~idx, col] = [s[:-2] for s in dfs.loc[~idx, col]]
        dfs.loc[idx, col] = '...'
    dfs.fillna('...', inplace=True)
    columns = dfs.columns
    dfs = dfs.loc[:, columns]
    dfs = dfs.to_dict('records')
    return render_template('main.html', rows=dfs, columns=columns[1:-1])


@app.route('/star/<string:star>/')
def stardetail(star=None):
    """Page with details on the individual system"""
    if star:
        df, _ = planetAndStar(how='left')
        index = df['Star'] == star
        d = df[index].copy()
        if len(d):
            show_planet = bool(~d['plName'].isnull().values[0])
            if show_planet:
                s = d['plName'].values[0]
                s = s.decode() if isinstance(s, bytes) else s
                s = '{} {}'.format(s[:-2], s[-1].lower())
                d['exolink'] = 'http://exoplanet.eu/catalog/{}/'.format(s.lower().replace(' ', '_'))
            d['lum'] = (d.teff.values[0]/5777)**4 * (d.mass.values[0]/((10**d.logg.values[0])/(10**4.44)))**2
            d['hz1'] = round(hz(d['teff'].values[0], d['lum'].values[0], model=2), 5)
            d['hz2'] = round(hz(d['teff'].values[0], d['lum'].values[0], model=4), 5)
            d = d.fillna('...')
            info = d.to_dict('records')
            return render_template('detail.html', info=info, show_planet=show_planet)
        else:
            return redirect(url_for('homepage'))


@app.route("/plot/", methods=['GET', 'POST'])
def plot():
    """Plot stellar parameters"""
    df, columns = readSC()
    return plot_page(df, columns, request, page="plot")


@app.route("/plot-exo/", methods=['GET', 'POST'])
def plot_exo():
    """Plot stellar and planetary parameters"""
    df, columns = planetAndStar()
    return plot_page(df, columns, request, page="plot_exo")


@app.route("/publications/")
def publications():
    """Show relevant publications for SWEET-Cat"""
    with open('data/publications.json') as pubs:
        pubs = json.load(pubs)
    return render_template('publications.html', publications=pubs)


@app.errorhandler(404)
def error_404(error):
    """Simple handler for status code: 404"""
    return render_template('404.html')


@app.route('/download/<path:fname>')
def download(fname):
    """Download SWEET-Cat table in different formats and clean afterwards"""
    fmt = fname.split('.')[-1]
    if fmt in ['csv', 'hdf']:
        table_convert(fmt=fmt)
        @after_this_request
        def remove_file(response):
            try:
                os.remove('data/{}'.format(fname))
            except OSError:
                pass
            return response
        return send_from_directory('data', fname)
    elif fmt == 'tsv':
        return send_from_directory('data', fname)
    else:
        return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
