from flask import Flask, render_template, flash, jsonify, request, url_for, \
                  redirect, session, g


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cniuo324fny7w98r4m8374ty893724hf8'


@app.route('/')
def homepage():
    return render_template('main.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
