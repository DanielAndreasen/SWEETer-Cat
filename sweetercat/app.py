from flask import Flask, render_template, request, url_for, redirect, session, send_from_directory
import os
import json
from plot import plot_page
from utils import readSC, planetAndStar, hz


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'


@app.before_first_request
def cache_data():
    # This will cache the databases when the app starts
    _ = planetAndStar(full=True)


@app.route('/')
def homepage(star=None):
    df, columns = readSC()
    dfs = df.sort_values('updated', ascending=False)[:50]  # TODO: Remove the slicing!
    for col in ('teff', 'tefferr'):  # These should be integers
        idx = dfs[col].isnull()
        dfs[col] = dfs[col].astype(str)
        dfs.loc[~idx, col] = [s[:-2] for s in dfs.loc[~idx, col]]
    dfs.fillna('...', inplace=True)
    columns = dfs.columns
    dfs = dfs.loc[:, columns]
    dfs = dfs.to_dict('records')
    return render_template('main.html', rows=dfs, columns=columns[1:-1])


@app.route('/star/<string:star>/')
def stardetail(star=None):
    if star is not None:
        df, columns = planetAndStar(full=True, how='left')
        index = df['Star'] == star
        d = df.loc[index, :]
        show_planet = bool(~d['plName'].isnull().values[0])
        if len(d):
            df.fillna('...', inplace=True)
            if show_planet:
                s = df.loc[index, 'plName'].values[0]
                df.loc[index, 'plName'] = s.decode() if isinstance(s, bytes) else s
                s = df.loc[index, 'plName'].values[0]
                df.loc[index, 'plName'] = '{} {}'.format(s[:-2], s[-1].lower())
                s = df.loc[index, 'plName'].values[0]
                df.loc[index, 'exolink'] = 'http://exoplanet.eu/catalog/{}/'.format(s.lower().replace(' ', '_'))
            df.loc[index, 'lum'] = (d.teff/5777)**4 * (d.mass/((10**d.logg)/(10**4.44)))**2
            df.loc[index, 'hz1'] = round(hz(df.loc[index, 'teff'].values[0],
                                            df.loc[index,  'lum'].values[0],
                                            model=2), 5)
            df.loc[index, 'hz2'] = round(hz(df.loc[index, 'teff'].values[0],
                                            df.loc[index,  'lum'].values[0],
                                            model=4), 5)
            info = df.loc[index, :].to_dict('records')
            return render_template('detail.html', info=info, show_planet=show_planet)
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


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html')


@app.route('/download/<path:filename>')
def download(filename):
    if os.path.isfile(os.path.join('data', filename)):
        return send_from_directory('data', filename)
    else:
        return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
