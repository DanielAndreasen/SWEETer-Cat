from flask import Flask, render_template, request, url_for, redirect, session

import pandas as pd
from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models import HoverTool

colors = {
    'Blue': '#1f77b4',
    'Orange':   '#ff7f0e',
    'Green': '#2ca02c',
    'Red':  '#d62728',
    'Purple': '#9467bd',
}

def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]


def readSC():
    names = ['Star', 'HD', 'RA', 'dec', 'Vmag', 'Vmagerr', 'par', 'parerr', 'source',
             'teff', 'tefferr', 'logg', 'loggerr', 'logglc', 'logglcerr',
             'vt', 'vterr', 'feh', 'feherr', 'mass', 'masserr', 'Author', 'flag', 'updated', 'Comment']
    df = pd.read_table('sc.txt', names=names, na_values=['~'])

    plots = ['Vmag', 'Vmagerr', 'par', 'parerr', 'teff', 'tefferr',
             'logg', 'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr',
             'feh', 'feherr', 'mass', 'masserr']
    return df, plots

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route("/plot/", methods=['GET', 'POST'])
def plot():
    # Read SC
    df, columns = readSC()
    if request.method == 'POST':  # Something is being submitted
        color = request.form['color']
        x = request.form['x']
        y = request.form['y']
        if (not x in columns) or (not y in columns):
            return redirect(url_for('plot'))
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
        y = df['logg']
        x1, x2 = 9000, 2500
        y1, y2 = 1, 5.5
        title = 'HR diagram'
        session['x'] = 'teff'
        session['y'] = 'logg'

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
        x=x.name, y=y.name,
        x1=x1, x2=x2, y1=y1, y2=y2,
        columns=columns
    )
    return encode_utf8(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
