import mpld3
import numpy as np
from utils import hz
import matplotlib
import matplotlib.pyplot as plt
from mpld3 import fig_to_html, plugins, utils
from flask import flash, redirect, render_template, session, url_for


class LinkedView(plugins.PluginBase):
    """A simple plugin showing how multiple axes can be linked"""

    JAVASCRIPT = """
        mpld3.register_plugin("linkedview", LinkedViewPlugin);
        LinkedViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
        LinkedViewPlugin.prototype.constructor = LinkedViewPlugin;
        LinkedViewPlugin.prototype.requiredProps = ["idpts", "idline", "data"];
        LinkedViewPlugin.prototype.defaultProps = {}
        function LinkedViewPlugin(fig, props){
            mpld3.Plugin.call(this, fig, props);
        };

        LinkedViewPlugin.prototype.draw = function(){
          var pts = mpld3.get_element(this.props.idpts);
          var line = mpld3.get_element(this.props.idline);
          var data = this.props.data;

          function mouseover(d, i){
            line.data = data[i];
            line.elements().transition()
                .attr("d", line.datafunc(line.data))
                .style("stroke", this.style.fill);
          }
          pts.elements().on("mouseover", mouseover);
        };
    """

    def __init__(self, points, line, linedata):
        if isinstance(points, matplotlib.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}


def plot2(df):
    fig, ax = plt.subplots(2, figsize=(14, 8))
    # scatter periods and amplitudes
    # P = 0.2 + np.random.random(size=20)
    # A = np.random.random(size=20)
    # x = np.linspace(0, 10, 100)
    # data = np.array([[x, Ai * np.sin(x / Pi)]
    #                  for (Ai, Pi) in zip(A, P)])
    # points = ax[1].scatter(P, A, c=P + A,
    #                        s=200, alpha=0.5)
    # ax[1].set_xlabel('Period')
    # ax[1].set_ylabel('Amplitude')
    #
    # # create the line object
    # lines = ax[0].plot(x, 0 * x, '-w', lw=3, alpha=0.5)
    # ax[0].set_ylim(-1, 1)
    #
    # ax[0].set_title("Hover over points to see lines")
    #
    # # transpose line data and add plugin
    # linedata = data.transpose(0, 2, 1).tolist()
    # plugins.connect(fig, LinkedView(points, lines[0], linedata))

    df['lum'] = (df['teff']/5777)**4 * (df['mass']/((10**df['logg'])/(10**4.44)))**2
    df['hz1'] = [hz(teff, lum, model=2) for (teff, lum) in df[['teff', 'lum']].values]
    df['hz2'] = [hz(teff, lum, model=4) for (teff, lum) in df[['teff', 'lum']].values]
    df = df.loc[:, ['sma', 'teff', 'hz1', 'hz2']].dropna(axis=0)

    data = np.array([[sma, 1] for sma in df['sma'].values])

    points = ax[1].semilogx(df['sma'], df['teff'], 'o')
    ax[1].set_xlabel('Semi major axis')
    ax[1].set_ylabel('Teff')
    lines = ax[0].scatter([1, 2], [0, 0], '-w', lw=3, alpha=0.6)
    # linedata = data.transpose(0, 2, 1).tolist()
    # plugins.connect(fig, LinkedView(points[0], lines, linedata))
    plugins.connect(fig, LinkedView(points[0], lines, data))

    plot = fig_to_html(fig)
    return render_template('plot2.html', plot=plot)
