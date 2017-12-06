from flask import Flask, render_template, request, url_for, redirect, send_from_directory, after_this_request
import os
import json
from plot import plot_page, plot_page_mpld3, detail_plot
from utils import readSC, planetAndStar, hz, table_convert, author_html

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SC_secret']


@app.route('/')
def homepage():
    """Home page for SWEETer-Cat with updated table"""
    df, _ = readSC()
    df['alink'] = list(map(author_html, df['Author'], df['link']))
    dfs = df.sort_values('updated', ascending=False)#[:50]  # TODO: Remove the slicing!
    decimals = dict.fromkeys(['Vmag', 'Vmagerr', 'par', 'parerr', 'logg',
                              'loggerr', 'logglc', 'logglcerr', 'vterr', 'feh',
                              'feherr', 'mass', 'masserr'], 2)
    dfs = dfs.round(decimals=decimals)
    for col in ('teff', 'tefferr'):  # These should be integers
        dfs[col].fillna(0, inplace=True)
        dfs[col] = dfs[col].astype(int)
    dfs.fillna('...', inplace=True)
    columns = dfs.columns
    dfs = dfs.to_dict('records')
    return render_template('main.html', rows=dfs, columns=columns[1:-2])


@app.route('/star/<string:star>/')
def stardetail(star=None):
    """Page with details on the individual system"""
    if star:
        df, _ = planetAndStar(how='left')
        t1, t2 = min(df['teff']), max(df['teff'])
        index = df['Star'] == star
        d = df.loc[index, :].copy()
        if len(d):
            show_planet = bool(~d['plName'].isnull().values[0])
            if show_planet:
                s = d['plName'].values
                s = [si.decode() if isinstance(si, bytes) else si for si in s]
                s = ['{} {}'.format(si[:-2], si[-1].lower()) for si in s]
                d['exolink'] = ['http://exoplanet.eu/catalog/{}/'.format(si.lower().replace(' ', '_')) for si in s]
            d['lum'] = (d.teff/5777)**4 * (d.mass/((10**d.logg)/(10**4.44)))**2
            d['hz1'] = round(hz(d['teff'].values[0], d['lum'].values[0], model=2), 5)
            d['hz2'] = round(hz(d['teff'].values[0], d['lum'].values[0], model=4), 5)

            if len(d) == sum(d['sma'].isnull()):
                plot = None
            else:
                plot = detail_plot(d, t1, t2)
            d.fillna('...', inplace=True)
            info = d.to_dict('records')

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


@app.route('/local/')
def local():
    return render_template('local.html')


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
