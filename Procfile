release: echo -n $HOME/PyAData > $HOME/.pyaConfigWhere
release: mkdir $HOME/PyAData
release: python -c "from PyAstronomy.pyasl import ExoplanetEU2; ExoplanetEU2()"
web: sh -c 'cd ./sweetercat/ && gunicorn -c config.py app:app'
