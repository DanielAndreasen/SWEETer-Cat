from flask import Flask, render_template, request, url_for, redirect, session
import json
from plot import plot_page
from utils import readSC, planetAndStar, hz


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'


@app.route('/')
def homepage(star=None):
    df, columns = readSC()
    dfs = df.sort_values('updated', ascending=False)[:50]  # TODO: Remove the slicing!
    for col in ('teff', 'tefferr'):  # These should be integers
        idx = dfs[col].isnull()
        dfs[col] = dfs[col].astype(str)
        dfs.loc[~idx, col] = list(map(lambda s: s[:-2], dfs.loc[~idx, col]))
    dfs.fillna('...', inplace=True)
    columns = dfs.columns
    dfs = dfs.loc[:, columns]
    dfs = dfs.to_dict('records')
    return render_template('main.html', rows=dfs, columns=columns[1:-1])


@app.route('/star/<string:star>/')
def stardetail(star=None):
    if star is not None:
        df, columns = planetAndStar(full=True, how='left')
        d = df.loc[df['Star'] == star, :]
        show_planet = bool(~d['plName'].isnull().values[0])
        if len(d):
            d.fillna('...', inplace=True)
            d['plName'] = list(map(lambda s: s.decode() if isinstance(s, bytes) else s, d['plName']))
            d['plName'] = list(map(lambda s: '{} {}'.format(s[:-2], s[-1].lower()), d['plName']))
            d['exolink'] = list(map(lambda s: 'http://exoplanet.eu/catalog/{}/'.format(s.lower().replace(' ', '_')), d['plName']))
            d['lum'] = (d.teff/5777)**4 * (d.mass/((10**d.logg)/(10**4.44)))**2
            d['hz1'] = round(hz(d.teff.values[0], d.lum.values[0], model=2), 5)
            d['hz2'] = round(hz(d.teff.values[0], d.lum.values[0], model=4), 5)
            return render_template('detail.html', info=d.to_dict('records'), show_planet=show_planet)
    return redirect(url_for('homepage'))


@app.route("/plot/", methods=['GET', 'POST'])
def plot():
    df, columns = readSC()
    return plot_page(df, columns, request, page="sc")


@app.route("/plot-exo/", methods=['GET', 'POST'])
def plot_exo():
    df, columns = planetAndStar()
    return plot_page(df, columns, request, page="exo")


@app.route("/publications/")
def publications():
    with open('publications.json') as pubs:
        pubs = json.load(pubs)
    return render_template('publications.html', publications=pubs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
