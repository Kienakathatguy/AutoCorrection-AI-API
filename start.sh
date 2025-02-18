#!/bin/bash

# Install Java if needed
sudo apt-get update
sudo apt-get install -y default-jre

# Install Python dependencies
pip install -r requirements.txt

# Start your web application (replace with the actual command)
python AutoCorrect.py
