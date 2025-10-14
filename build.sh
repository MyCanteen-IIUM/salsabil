#!/usr/bin/env bash
# exit on error
set -o errexit

# Force Python 3.9
export PYTHON_VERSION=3.9.18

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
