import matplotlib
matplotlib.use('Agg')

from bokeh.embed import components
from bokeh.layouts import column, row
from bokeh.models import ColorBar, HoverTool, LinearColorMapper, Spacer
from bokeh.palettes import Viridis11, Inferno11, Plasma11
from bokeh.plotting import ColumnDataSource, figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from flask import flash, redirect, render_template, session, url_for
import numpy as np
import pandas as pd
from utils import colors, get_default, planetary_radius

import matplotlib.cm as cm
import matplotlib.pyplot as plt
from mpld3 import fig_to_html, plugins


colorschemes = {'Viridis': [Viridis11, 'Viridis256'],
                'Inferno': [Inferno11, 'Inferno256'],
                'Plasma':  [Plasma11,  'Plasma256']}

# Name: [distance (AU), diameter (km)]
# From http://www.enchantedlearning.com/subjects/astronomy/planets/
ss_planets = {
    'Mercury': [0.39, 4878],
    'Venus': [0.723, 12104],
    'Earth': [1, 12756],
    'Mars': [1.524, 6787],
    'Jupiter': [5.203, 142796],
    'Saturn': [9.539, 120660],
    'Uranus': [19.18, 51118],
    'Neptune': [30.06, 48600],
    'Pluto': [39.53, 2274]}


def detail_plot(df, tlow, thigh):

    hz1 = get_default(df['hz1'].values[0], -2, float)
    hz2 = get_default(df['hz2'].values[0], -1, float)
    M = get_default(df['mass'].values[0], 1, float)
    logg = get_default(df['logg'].values[0], 4.44, float)
    color = get_default(df['teff'].values[0], 5777, float)
    tlow = get_default(max(2500, tlow), 2500, int)
    thigh = get_default(min(8500, thigh), 8500, int)

    R = df.iloc[0]['radius']
    r = [planetary_radius(mi, ri) for mi, ri in df.loc[:, ['plMass', 'plRadius']].values]
    smas = df['sma'].values
    max_smas = max([smai for smai in smas if isinstance(smai, (int, float))])
    Rs = max(500, 500*R)
    rs = [max(80, 30*ri) for ri in r]

    fig, ax = plt.subplots(1, figsize=(14, 2))
    ax.scatter([0], [1], s=Rs, c=color, vmin=tlow, vmax=thigh, cmap=cm.autumn)
    no_sma = []
    for i, sma in enumerate(smas):
        if np.isnan(sma):
            no_sma.append('{} has no SMA'.format(df['plName'].values[i]))
            continue
        if sma < hz1:
            dist = hz1-sma
            ax.scatter(sma, [1], s=rs[i], c=dist, vmin=0, vmax=hz1, cmap=cm.autumn)
        elif hz1 <= sma <= hz2:
            ax.scatter(sma, [1], s=rs[i], c='k')
        else:
            dist = sma-hz2
            ax.scatter(sma, [1], s=rs[i], c=dist, vmin=hz2, vmax=max_smas, cmap=cm.winter_r)

    if 0 < hz1 < hz2:
        x = np.linspace(hz1, hz2, 10)
        y = np.linspace(0.9, 1.1, 10)
        z = np.array([[xi]*10 for xi in x[::-1]]).T
        plt.contourf(x, y, z, 300, alpha=0.8, cmap=cm.summer)

    for planet in ss_planets.keys():
        s = ss_planets[planet][0]
        r = 30*ss_planets[planet][1]/2.
        r /= float(ss_planets['Jupiter'][1])
        ax.scatter(s, [0.95], s=r*10, c='g')
        ax.text(s-0.01, 0.97, planet, color='white')

    ax.set_xlim(0.0, max_smas*1.2)
    ax.set_ylim(0.9, 1.1)
    ax.set_xlabel('Semi-major axis [AU]')
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    ax.set_facecolor('black')
    plt.tight_layout()

    for i, text in enumerate(no_sma):
        ax.text(max_smas*0.8, 1.05-i*0.02, text, color='white')

    try:
        h = fig_to_html(fig, no_extras=True, template_type='simple', use_http=True)
        return h
    except TypeError:
        return None


def plot_page_mpld3(df, columns, request):
    if request.method == 'POST':  # Something is being submitted
        x1 = str(request.form['x1'])
        x2 = str(request.form['x2'])
        y1 = str(request.form['y1'])
        y2 = str(request.form['y2'])
        z = str(request.form['z'])
        if (x1 not in columns) or (x1 not in columns):
            return redirect(url_for(mpld3_plot))
        elif (y1 not in columns) or (y1 not in columns):
            return redirect(url_for(mpld3_plot))
        elif (z not in columns):
            return redirect(url_for(mpld3_plot))
    else:
        x1, x2, y1, y2, z = 'teff', 'vt', 'Vabs', 'feh', 'logg'
    # Does not work with NaN values!
    df = df.loc[:, list(set([x1, x2, y1, y2, z]))].dropna(axis=0)
    fig, ax = plt.subplots(2, 2, figsize=(14, 8), sharex='col', sharey='row')
    points = ax[0, 0].scatter(df[x1], df[y1], c=df[z], alpha=0.6)
    points = ax[1, 0].scatter(df[x1], df[y2], c=df[z], alpha=0.6)
    points = ax[0, 1].scatter(df[x2], df[y1], c=df[z], alpha=0.6)
    points = ax[1, 1].scatter(df[x2], df[y2], c=df[z], alpha=0.6)
    ax[1, 0].set_xlabel(x1)
    ax[1, 1].set_xlabel(x2)
    ax[0, 0].set_ylabel(y1)
    ax[1, 0].set_ylabel(y2)

    plugins.connect(fig, plugins.LinkedBrush(points))
    plot = fig_to_html(fig)
    return render_template('plot_mpld3.html', plot=plot, columns=columns,
                           x1=x1, x2=x2, y1=y1, y2=y2, z=z)


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
    page : str ('plot', 'plot_exo')
      Which page to render (for combined ['plot_exo'] or just SWEET-Cat ['plot'])

    Output
    ------
    The rendered page with the plot
    """
    colorscheme = 'Plasma'
    if request.method == 'POST':  # Something is being submitted
        color = request.form['color']
        x = str(request.form['x'])
        y = str(request.form['y'])
        z = str(request.form['z'])
        z = None if z == 'None' else z

        if (x not in columns) or (y not in columns):
            return redirect(url_for(page))
        if (z is not None) and (z not in columns):
            return redirect(url_for(page))

        colorscheme = str(request.form.get('colorscheme', colorscheme))
        if colorscheme not in colorschemes.keys():
            return redirect(url_for(page))

        checkboxes = request.form.getlist("checkboxes")
        if not checkboxes:  # When [] is returned
            checkboxes = ['']
        if checkboxes[0] not in [[], '', 'homo']:
            return redirect(url_for(page))

        df, x, y, z = extract(df, x, y, z, checkboxes)

        # Setting the limits
        x1, x2, y1, y2 = get_limits(request.form, x, y)

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
        if xscale not in ['linear', 'log']:
            return redirect(url_for(page))
        if yscale not in ['linear', 'log']:
            return redirect(url_for(page))

    else:
        if page == "plot_exo":
            x = 'discovered'
            y = 'plMass'
            z = None
            x1, x2 = 1985, 2020
            y1, y2 = 0.0001, 200
            yscale = 'log'
            session['x'] = 'discovered'
            session['y'] = 'plMass'
            session['z'] = 'None'
        else:
            x = 'teff'
            y = 'lum'
            z = 'logg'
            x1, x2 = 8000, 2500
            y1, y2 = 1e-3, 3000
            yscale = 'log'
            session['x'] = 'teff'
            session['y'] = 'lum'
            session['z'] = 'logg'
        color = 'Blue'
        xscale = 'linear'
        checkboxes = []
        df, x, y, z = extract(df, x, y, z, checkboxes)

    # Check scale
    xscale, yscale, error = check_scale(x, y, xscale, yscale)

    stars = df['Star']
    stars = list(stars.values)  # Turn series into list.
    hover = HoverTool(tooltips=[
        ("{}".format(x.name), "$x"),
        ("{}".format(y.name), "$y"),
        ("Star", "@star"),
    ])

    num_points = count(x, y, [x1, x2], [y1, y2])

    title = '{} vs. {}:\tNumber of objects in plot: {}'.format(x.name, y.name, num_points)

    tools = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select,save".split(',')
    fig = figure(title=title, tools=tools + [hover], plot_width=800, plot_height=400,
                 toolbar_location='above',
                 x_range=[x1, x2], y_range=[y1, y2],
                 x_axis_type=xscale, y_axis_type=yscale)

    if z is not None:  # Add colours and a colorbar
        COLORS, pallete = colorschemes[colorscheme]
        groups = pd.qcut(z.values, len(COLORS), duplicates="drop")
        c = [COLORS[xx] for xx in groups.codes]
        source = ColumnDataSource(data=dict(x=x, y=y, c=c, star=stars))

        color_mapper = LinearColorMapper(palette=pallete, low=z.min(), high=z.max())
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
    if error is not None:
        flash('Scale was changed from log to linear')
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
        columns=columns,
        colorschemes=colorschemes,
        colorscheme=colorscheme
    )
    return encode_utf8(html)


def check_scale(x, y, xscale, yscale):
    x = np.array(x)
    y = np.array(y)
    error = None
    if (xscale == 'log') and np.any(x <= 0):
        xscale = 'linear'
        error = True
    if (yscale == 'log') and np.any(y <= 0):
        yscale = 'linear'
        error = True
    return xscale, yscale, error


def scaled_histogram(data, num_points, scale):
    if scale == 'linear':
        hist, edges = np.histogram(data, bins=max([5, int(num_points / 50)]))
    else:
        # Conditional catches an empty data input.
        h1, h2 = ((np.log10(min(data)), np.log10(max(data))) if len(data) > 0 else (0, 1))
        hist, edges = np.histogram(data, bins=np.logspace(h1, h2, 1 + max([5, int(num_points / 50)])))
    hist_max = max(hist) * 1.1
    return hist, edges, hist_max


def get_limits(points, x, y):
    def default_value(x, default):
        try:
            return float(x)
        except (ValueError, TypeError):
            return default

    defaults = [min(x), max(x), min(y), max(y)]
    limits = [points['x1'], points['x2'], points['y1'], points['y2']]
    for i, (limit, default) in enumerate(zip(limits, defaults)):
        limits[i] = default_value(limit, default)
    return limits


def count(x, y, xlimits, ylimits):
    """Count number of points in x and y that lie within the given limits.

    Inputs
    x, y: array-like
    xlimits, ylimts: lists of two numbers.
    Returns
    count: int
        Number of points within the limits.
    """
    if not (isinstance(xlimits, list) and isinstance(ylimits, list)):
        raise TypeError("Axis limits are not of type List.")
    elif (len(xlimits) != 2) or (len(ylimits) != 2):
        raise ValueError("Axis limits not of length 2.")
    # Sort Incase axis is revesed
    xlimits.sort()
    ylimits.sort()
    return int(sum((xlimits[0] < x) & (x < xlimits[1]) &
                   (ylimits[0] < y) & (y < ylimits[1])))


def extract(df, x, y, z, checkboxes):
    """Extract columns from dataframe.

    Handles z=None case and homogenous masking with 'flag'.
    Input Types
    df: DataFrame
    x: str
    y: str
    z: str or None
    checkboxes: list
    """
    if "homo" in checkboxes:  # Homogenous filtering
        df = df[df["flag"]]

    cols = filter(None, set(['Star', x, y, z, "flag"]))
    df = df.loc[:, cols].dropna()
    x = df[x]
    y = df[y]
    z = None if z is None else df[z]
    return df, x, y, z
