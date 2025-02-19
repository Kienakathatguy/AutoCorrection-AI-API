#!/usr/bin/env bash

# Install Java
apt-get update && apt-get install -y openjdk-17-jdk

# Verify Java installation
java -version

pip install -r requirements.txt
