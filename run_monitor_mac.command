#!/bin/bash
cd "$(dirname "$0")"
pip3 install -r requirements.txt
python3 loadcell_gui.py
