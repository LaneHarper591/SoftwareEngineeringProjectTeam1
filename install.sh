#!/bin/bash
sudo apt install python3-pip python3-dev
pip install pygame
pip install psycopg2-binary
python3 addplayers.py
python3 game.py
