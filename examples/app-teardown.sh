#!/bin/sh

export FLASK_APP=app.py

# Clean the database
flask db destroy --yes-i-know

# Clean the indices
flask index destroy --yes-i-know
