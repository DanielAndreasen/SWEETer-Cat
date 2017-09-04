#!/bin/bash

echo -n $HOME/PyAData > $HOME/.pyaConfigWhere
mkdir $HOME/PyAData
python -c "from PyAstronomy.pyasl import ExoplanetEU2; ExoplanetEU2()"
