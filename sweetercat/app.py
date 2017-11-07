from flask import Flask, render_template, request, url_for, redirect, send_from_directory, after_this_request
import os
import json
from plot import plot_page, plot_page_mpld3, detail_plot
from utils import readSC, planetAndStar, hz, table_convert

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SC_secret']


@app.route('/')
def homepage(star=None):
    """Home page for SWEETer-Cat with updated table"""
    df, columns = readSC()
    dfs = df.sort_values('updated', ascending=False)#[:50]  # TODO: Remove the slicing!
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
    return render_template('main.html', rows=dfs, columns=columns[1:-2])


@app.route('/star/<string:star>/')
def stardetail(star=None):
    """Page with details on the individual system"""
    if star:
        df, _ = planetAndStar(how='left')
        t1, t2 = min(df['teff']), max(df['teff'])
        index = df['Star'] == star
        d = df.loc[index, :]
        if len(d):
            show_planet = bool(~d['plName'].isnull().values[0])
            df.fillna('...', inplace=True)
            if show_planet:
                s = df.loc[index, 'plName'].values
                df.loc[index, 'plName'] = [si.decode() if isinstance(si, bytes) else si for si in s]
                s = df.loc[index, 'plName'].values
                df.loc[index, 'plName'] = ['{} {}'.format(si[:-2], si[-1].lower()) for si in s]
                s = df.loc[index, 'plName'].values
                df.loc[index, 'exolink'] = ['http://exoplanet.eu/catalog/{}/'.format(si.lower().replace(' ', '_')) for si in s]
            df.loc[index, 'lum'] = (d.teff/5777)**4 * (d.mass/((10**d.logg)/(10**4.44)))**2
            df.loc[index, 'hz1'] = round(hz(df.loc[index, 'teff'].values[0],
                                            df.loc[index,  'lum'].values[0],
                                            model=2), 5)
            df.loc[index, 'hz2'] = round(hz(df.loc[index, 'teff'].values[0],
                                            df.loc[index,  'lum'].values[0],
                                            model=4), 5)
            df.fillna('...', inplace=True)
            info = df.loc[index, :].to_dict('records')

            plot = detail_plot(df[index], t1, t2)
            return render_template('detail.html', info=info, show_planet=show_planet, plot=plot)
    return redirect(url_for('homepage'))


@app.route('/mpld3/', methods=['GET', 'POST'])
def mpld3_plot():
    df, columns = planetAndStar()
    return plot_page_mpld3(df, columns, request)


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


@app.route('/about/')
def about():
    return render_template('about.html')


@app.errorhandler(404)
def error_404(error):
    """Simple handler for status code: 404"""
    return render_template('404.html')


@app.route('/download/<path:fname>')
def download(fname):
    """Download SWEET-Cat table in different formats and clean afterwards"""
    if fname.startswith('sweet-cat'):
        print(fname)
        fmt = fname.split('.')[-1]
        if fmt in ['csv', 'hdf']:
            table_convert(fmt=fmt)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove('data/{}'.format(fname))
                except OSError:  # pragma: no cover
                    pass  # pragma: no cover
                return response
        return send_from_directory('data', fname)
    else:
        return send_from_directory('data', fname)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # pragma: no cover
    app.run(host='0.0.0.0', port=port, debug=True)  # pragma: no cover
