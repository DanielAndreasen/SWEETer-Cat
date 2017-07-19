from flask import Flask, render_template, request, url_for, redirect, session
from werkzeug.contrib.cache import SimpleCache
import json
import numpy as np
import pandas as pd
from PyAstronomy import pyasl
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.palettes import Viridis11
from bokeh.layouts import row, column
from bokeh.util.string import encode_utf8
from bokeh.plotting import figure, ColumnDataSource, curdoc
from bokeh.models import HoverTool, ColorBar, LinearColorMapper, LabelSet, Spacer

COLORS = Viridis11

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'
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
    if df is None:
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


def planetAndStar():
    d = cache.get('planetDB')
    c = cache.get('planetCols')
    if d is None:
        deu = pd.DataFrame(pyasl.ExoplanetEU().data)
        cols = ['stName', 'plMass', 'plRadius', 'period', 'sma', 'eccentricity',
                'inclination', 'discovered', 'dist',
                'mag_v', 'mag_i', 'mag_j', 'mag_h', 'mag_k']
        deu = deu[cols]
        deu['stName'] = [s.decode() for s in deu['stName']]
        df, columns = readSC()
        d = pd.merge(df, deu, left_on='Star', right_on='stName')
        c = columns+cols[1:]
        cache.set('planetDB', d, timeout=5*60)
        cache.set('planetCols', c, timeout=5*60)

    return d, c


@app.route('/')
def homepage():
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


def plot_page(df, columns, request, page):
    if request.method == 'POST':  # Something is being submitted
        color = request.form['color']
        x = str(request.form['x'])
        y = str(request.form['y'])
        z = str(request.form['z'])
        z = None if z == 'None' else z

        if (x not in columns) or (y not in columns):
            return redirect(url_for('plot'))
        if z is not None:
            if z not in columns:
                return redirect(url_for('plot'))

        if z is not None:
            df = df[list(set(['Star', x, y, z, "flag"]))]
            df.dropna(inplace=True)
            z = df[z]
        else:
            df = df[list(set(['Star', x, y, "flag"]))]
            df.dropna(inplace=True)
        x = df[x]
        y = df[y]

        # Setting the limits
        limits = [request.form['x1'], request.form['x2'],
                  request.form['y1'], request.form['y2']]
        for i, lim in enumerate(limits):
            try:
                limits[i] = float(lim)
            except ValueError:
                if i == 0:
                    limits[i] = min(x)
                elif i == 1:
                    limits[i] = max(x)
                elif i == 2:
                    limits[i] = min(y)
                elif i == 3:
                    limits[i] = max(y)
        x1, x2, y1, y2 = limits

        if x.name != session['x']:
            x1 = min(x)
            x2 = max(x)
            session['x'] = x.name
        if y.name != session['y']:
            y1 = min(y)
            y2 = max(y)
            session['y'] = y.name

        xscale = str(request.form['xscale'])
        yscale = str(request.form['yscale'])

        checkboxes = request.form.getlist("checkboxes")
    else:
        if page == "exo":
            color = 'Blue'
            df = df[list(set(['Star', 'discovered', 'plMass']))]
            df.dropna(inplace=True)
            x = df['discovered']
            y = df['plMass']
            z = None
            x1, x2 = 1985, 2020
            y1, y2 = 0.0001, 200
            xscale = 'linear'
            yscale = 'log'
            session['x'] = 'discovered'
            session['y'] = 'plMass'
            session['z'] = 'None'
            checkboxes = []
        else:
            color = 'Blue'
            df = df[list(set(['Star', 'teff', 'Vabs', 'logg']))]
            df.dropna(inplace=True)
            x = df['teff']
            y = df['Vabs']
            z = df['logg']
            x1, x2 = 8000, 2500
            y1, y2 = 33, 10
            xscale = 'linear'
            yscale = 'linear'
            session['x'] = 'teff'
            session['y'] = 'Vabs'
            session['z'] = 'logg'
            checkboxes = []

    stars = df['Star']
    if "homo" in checkboxes:
        flag = df["flag"]
        stars = stars[flag]
        x = x[flag]
        y = y[flag]
        if z is not None:
            z = z[flag]

    stars = list(stars.values)  # Turn series into list.
    hover = HoverTool(tooltips=[
        ("{}".format(x.name), "$x"),
        ("{}".format(y.name), "$y"),
        ("Star", "@star"),
    ])

    minx, maxx, miny, maxy = min([x1, x2]), max([x1, x2]), min([y1, y2]), max([y1, y2])  # Incase axis is revesed
    num_points = np.sum((minx < x) & (x < maxx) & (miny < y) & (y < maxy))
    title = '{} vs. {}:\tNumber of objects in plot: {}'.format(x.name, y.name, num_points)

    tools = "resize,crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select,save".split(',')
    fig = figure(title=title, tools=tools + [hover], plot_width=800, plot_height=400,
                 toolbar_location='above',
                 x_range=[x1, x2], y_range=[y1, y2],
                 x_axis_type=xscale, y_axis_type=yscale)

    if z is not None:  # Add colours and a colorbar
        groups = pd.qcut(z.values, len(COLORS), duplicates="drop")
        c = [COLORS[xx] for xx in groups.codes]
        source = ColumnDataSource(data=dict(x=x, y=y, c=c, star=stars))

        color_mapper = LinearColorMapper(palette="Viridis256", low=z.min(), high=z.max())
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12,
                             border_line_color=None, location=(0, 0))
        fig.add_layout(color_bar, 'right')
        cr = fig.circle('x', 'y', source=source, size=10,
                        color='c', fill_alpha=0.2, line_color=None)
        z = z.name
        fig.xaxis.axis_label = x.name
        fig.yaxis.axis_label = y.name
        color_bar.title = z
    else:  # Simple colorbar
        source = ColumnDataSource(data=dict(x=x, y=y, star=stars))
        cr = fig.circle('x', 'y', source=source, size=10,
                        color=colors[color], fill_alpha=0.2, line_color=None)
        fig.xaxis.axis_label = x.name
        fig.yaxis.axis_label = y.name

    # Horizontal historgram
    if xscale == 'linear':
        hhist, hedges = np.histogram(x, bins=int(num_points/50))
    else:
        xh1, xh2 = np.log10(min(x)), np.log10(max(x))
        hhist, hedges = np.histogram(x, bins=np.logspace(xh1, xh2, int(num_points/50)))
    hzeros = np.zeros(len(hedges) - 1)
    hmax = max(hhist) * 1.1

    LINE_ARGS = dict(color="#3A5785", line_color=None)

    ph = figure(toolbar_location=None, plot_width=fig.plot_width, plot_height=200, x_range=fig.x_range,
                y_range=(-hmax*0.1, hmax), min_border=10, min_border_left=50, y_axis_location="right",
                x_axis_type=xscale)
    ph.xgrid.grid_line_color = None
    ph.yaxis.major_label_orientation = np.pi / 4
    ph.background_fill_color = "#fafafa"

    ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hhist, color="white", line_color="#3A5785")
    hh1 = ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.5, **LINE_ARGS)
    hh2 = ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.1, **LINE_ARGS)

    # vertical historgram
    if yscale == 'linear':
        vhist, vedges = np.histogram(y, bins=int(num_points/50))
    else:
        yh1, yh2 = np.log10(min(y)), np.log10(max(y))
        vhist, vedges = np.histogram(y, bins=np.logspace(yh1, yh2, int(num_points/50)))
    vzeros = np.zeros(len(vedges) - 1)
    vmax = max(vhist) * 1.1

    pv = figure(toolbar_location=None, plot_width=200, plot_height=fig.plot_height, x_range=(-vmax*0.1, vmax),
                y_range=fig.y_range, min_border=10, y_axis_location="right", y_axis_type=yscale)
    pv.ygrid.grid_line_color = None
    pv.xaxis.major_label_orientation = np.pi / 4
    pv.background_fill_color = "#fafafa"

    pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vhist, color="white", line_color="#3A5785")
    # vh1 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.5, **LINE_ARGS)
    # vh2 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.1, **LINE_ARGS)

    # Selection updating code - not working.
    # def update(attr, old, new):
    #     inds = np.array(new['1d']['indices'])
    #     if len(inds) == 0 or len(inds) == len(x):
    #         hhist1, hhist2 = hzeros, hzeros
    #         vhist1, vhist2 = vzeros, vzeros
    #     else:
    #         neg_inds = np.ones_like(x, dtype=np.bool)
    #         neg_inds[inds] = False
    #         hhist1, _ = np.histogram(x[inds], bins=hedges)
    #         vhist1, _ = np.histogram(y[inds], bins=vedges)
    #         hhist2, _ = np.histogram(x[neg_inds], bins=hedges)
    #         vhist2, _ = np.histogram(y[neg_inds], bins=vedges)
    #
    #     hh1.data_source.data["top"]   =  hhist1
    #     hh2.data_source.data["top"]   = -hhist2
    #     vh1.data_source.data["right"] =  vhist1
    #     vh2.data_source.data["right"] = -vhist2
    #
    # cr.data_source.on_change('selected', update)
    #
    # curdoc().add_root(layout)
    # curdoc().title = "Selection Histogram"

    layout = column(row(fig, pv), row(ph, Spacer(width=200, height=200)))

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script, div = components(layout)
    html = render_template(
        'plot.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        color=color,
        colors=colors,
        x=x.name, y=y.name, z=z,
        x1=x1, x2=x2, y1=y1, y2=y2,
        xscale=xscale, yscale=yscale,
        checkboxes=checkboxes,
        columns=columns
    )
    return encode_utf8(html)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
