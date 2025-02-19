#!/usr/bin/env bash

# Ensure the system is updated
apt-get update && apt-get install -y openjdk-17-jdk

# Verify that Java is installed
java -version

pip install -r requirements.txt
