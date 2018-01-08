#!/usr/bin/env bash
cat requirements.system | xargs apt-get -y install 
pip3 install -r requirements.txt
