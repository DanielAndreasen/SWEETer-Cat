from flask import Flask, render_template, request, url_for, redirect, session
import json
from plot import plot_page
from utils import readSC, planetAndStar


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'


@app.route('/')
@app.route('/<string:star>')
def homepage(star=None):
    df, columns = readSC()
    print(star)
    if star is not None:
        d = df.loc[df['Star'] == star, :]
        if len(d):
            print(d)
            # TODO: Merge with exoplanetEU to get planetary details
            return render_template('detail.html', info=d.to_dict('records')[0])
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
