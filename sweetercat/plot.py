from flask import session, render_template, redirect, url_for

import numpy as np
import pandas as pd
from utils import colors

from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.palettes import Viridis11
from bokeh.layouts import row, column
from bokeh.util.string import encode_utf8
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import HoverTool, ColorBar, LinearColorMapper, Spacer

COLORS = Viridis11


def plot_page(df, columns, request, page):
    """Render the Bokeh plot.

    Inputs
    ------
    df : pd.DataFrame
      The DataFrame with the data
    columns : list
      Which columns to use for choices in the plot
    request : flask
      The request object from flask
    page : str ('exo', 'star')
      Which page to render (for combined [exo] or just stars [star])

    Output
    ------
    The rendered page with the plot
    """
    if request.method == 'POST':  # Something is being submitted
        color = request.form['color']
        x = str(request.form['x'])
        y = str(request.form['y'])
        z = str(request.form['z'])
        z = None if z == 'None' else z

        if (x not in columns) or (y not in columns):
            return redirect(url_for('plot'))
        if (z is not None) and (z not in columns):
            return redirect(url_for('plot'))

        if z is not None:
            cols = list(set(['Star', x, y, z, "flag"]))
            df = df.loc[:, cols].dropna()
            z = df[z]
        else:
            cols = list(set(['Star', x, y, "flag"]))
            df = df.loc[:, cols].dropna()
        x = df[x]
        y = df[y]

        # Setting the limits
        x1, x2, y1, y2 = get_limits(request, x, y)

        if x.name != session.get('x', None):
            x1 = min(x)
            x2 = max(x)
            session['x'] = x.name
        if y.name != session.get('y', None):
            y1 = min(y)
            y2 = max(y)
            session['y'] = y.name

        xscale = str(request.form['xscale'])
        yscale = str(request.form['yscale'])

        checkboxes = request.form.getlist("checkboxes")
    else:
        if page == "exo":
            color = 'Blue'
            cols = list(set(['Star', 'discovered', 'plMass']))
            df = df.loc[:, cols].dropna()
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
            cols = list(set(['Star', 'teff', 'Vabs', 'logg']))
            df = df.loc[:, cols].dropna()
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
        fig.circle('x', 'y', source=source, size=10,
                        color='c', fill_alpha=0.2, line_color=None)
        z = z.name
        fig.xaxis.axis_label = x.name
        fig.yaxis.axis_label = y.name
        color_bar.title = z
    else:  # Simple colorbar
        source = ColumnDataSource(data=dict(x=x, y=y, star=stars))
        fig.circle('x', 'y', source=source, size=10,
                        color=colors[color], fill_alpha=0.2, line_color=None)
        fig.xaxis.axis_label = x.name
        fig.yaxis.axis_label = y.name

    # Horizontal historgram
    hhist, hedges, hmax = scaled_histogram(x, num_points, xscale)

    ph = figure(toolbar_location=None, plot_width=fig.plot_width, plot_height=200, x_range=fig.x_range,
                y_range=(-hmax*0.1, hmax), min_border=10, min_border_left=50, y_axis_location="right",
                x_axis_type=xscale)
    ph.xgrid.grid_line_color = None
    ph.yaxis.major_label_orientation = np.pi / 4
    ph.background_fill_color = "#fafafa"

    ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hhist, color="white", line_color=colors[color])

    # Vertical historgram
    vhist, vedges, vmax = scaled_histogram(y, num_points, yscale)

    pv = figure(toolbar_location=None, plot_width=200, plot_height=fig.plot_height, x_range=(-vmax*0.1, vmax),
                y_range=fig.y_range, min_border=10, y_axis_location="right", y_axis_type=yscale)
    pv.ygrid.grid_line_color = None
    pv.xaxis.major_label_orientation = np.pi / 4
    pv.background_fill_color = "#fafafa"

    pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vhist, color="white", line_color=colors[color])

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


def scaled_histogram(data, num_points, scale):
    if scale == 'linear':
        hist, edges = np.histogram(data, bins=max([5, int(num_points / 50)]))
    else:
        # Conditional catches an empty data input.
        h1, h2 = ((np.log10(min(data)), np.log10(max(data))) if len(data) > 0 else (0, 1))
        hist, edges = np.histogram(data, bins=np.logspace(h1, h2, 1 + max([5, int(num_points / 50)])))
    hist_max = max(hist) * 1.1
    return hist, edges, hist_max


def get_limits(request, x, y):
    def default_value(x, default):
        try:
            return float(x)
        except (ValueError, TypeError):
            return default

    defaults = [min(x), max(x), min(y), max(y)]
    if hasattr(request, 'form'):
        limits = [request.form['x1'], request.form['x2'], request.form['y1'], request.form['y2']]
    else:
        limits = [request['x1'], request['x2'], request['y1'], request['y2']]
    for i, (limit, default) in enumerate(zip(limits, defaults)):
        limits[i] = default_value(limit, default)
    return limits
