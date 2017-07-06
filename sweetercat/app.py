from flask import Flask, render_template, request, url_for, redirect, session
import numpy as np
import pandas as pd
from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models import HoverTool, ColorBar, LinearColorMapper
from bokeh.palettes import Viridis11

COLORS = Viridis11

colors = {
    'Blue': '#1f77b4',
    'Orange':   '#ff7f0e',
    'Green': '#2ca02c',
    'Red':  '#d62728',
    'Purple': '#9467bd',
}


def absolute_magnitude(parallax, m):
    d = 1/parallax
    mu = 5*np.log10(d) - 5
    M = m-mu
    return M


def readSC():
    names = ['Star', 'HD', 'RA', 'dec', 'Vmag', 'Vmagerr', 'par', 'parerr', 'source',
             'teff', 'tefferr', 'logg', 'loggerr', 'logglc', 'logglcerr',
             'vt', 'vterr', 'feh', 'feherr', 'mass', 'masserr', 'Author', 'flag', 'updated', 'Comment']
    df = pd.read_table('sc.txt', names=names, na_values=['~'])
    df['flag'] = df['flag'] == 1
    df['Vabs'] = [absolute_magnitude(p, m) for p, m in df[['par', 'Vmag']].values]

    plots = ['Vmag', 'Vmagerr', 'Vabs', 'par', 'parerr', 'teff', 'tefferr',
             'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
             'feh', 'feherr', 'mass', 'masserr']
    return df, plots

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'
df, columns = readSC()


@app.route('/')
def homepage():
    dfs = df.sort_values('updated', ascending=False)[:50]  # TODO: Remove the slicing!
    for col in ('teff', 'tefferr'):  # These should be integers
        idx = dfs[col].isnull()
        dfs[col] = dfs[col].astype(str)
        dfs.loc[~idx, col] = map(lambda s: s[:-2], dfs.loc[~idx, col])
    dfs.fillna('...', inplace=True)
    columns = dfs.columns
    dfs = dfs.loc[:, columns]
    dfs = dfs.to_dict('records')
    return render_template('main.html', rows=dfs, columns=columns[1:])


@app.route("/plot/", methods=['GET', 'POST'])
def plot():
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
            else:
                z = df[z]
                session['z'] = z.name
        x = df[x]
        y = df[y]
        x1, x2 = float(request.form['x1']), float(request.form['x2'])
        y1, y2 = float(request.form['y1']), float(request.form['y2'])

        if x.name != session['x']:
            x1 = min(x)
            x2 = max(x)
            session['x'] = x.name
        if y.name != session['y']:
            y1 = min(y)
            y2 = max(y)
            session['y'] = y.name

        title = '{} vs. {}'.format(x.name, y.name)
    else:
        color = 'Blue'
        x = df['teff']
        y = df['Vabs']
        z = df['logg']
        x1, x2 = 9000, 2500
        y1, y2 = 10, 33
        title = 'HR diagram'
        session['x'] = 'teff'
        session['y'] = 'Vabs'
        session['z'] = 'logg'

    stars = list(df['Star'].values)
    source = ColumnDataSource(data=dict(x=x, y=y, star=stars))
    hover = HoverTool(tooltips=[
        ("{}".format(x.name), "$x"),
        ("{}".format(y.name), "$y"),
        ("Star", "@star"),
    ])


    tools="resize,crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select,save".split(',')
    fig = figure(title=title, tools=tools+[hover], plot_width=800, plot_height=400,
                 toolbar_location='above',
                 x_range=[x1, x2], y_range=[y1, y2])

    if z is not None:  # Add colours and a colorbar
        groups = pd.qcut(z.values, len(COLORS))
        c = [COLORS[xx] for xx in groups.codes]
        color_mapper = LinearColorMapper(palette="Viridis256", low=z.min(), high=z.max())
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12,
                             border_line_color=None, location=(0,0))
        fig.add_layout(color_bar, 'right')
        cr = fig.circle('x', 'y', source=source, size=10,
                        color=c, fill_alpha=0.2, line_color=None)
        z = z.name
    else:  # Simple colorbar
        cr = fig.circle('x', 'y', source=source, size=10,
                        color=colors[color], fill_alpha=0.2, line_color=None)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script, div = components(fig)
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
        columns=columns
    )
    return encode_utf8(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
