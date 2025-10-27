#!/bin/bash
set -e

# Always run from project root (Hospital Management/)
cd "$(dirname "$0")"

# For local/dev only.
# If the user didn't export SECRET_KEY already, set a safe-but-not-production key.
if [ -z "$SECRET_KEY" ]; then
  export SECRET_KEY="local-dev-insecure-key"
fi

# Reasonable defaults for local run
export FLASK_ENV=production
export DEBUG=False
export TESTING=False

# Start the backend by invoking app.py directly.
# app.py will:
#   - create the Flask app using create_app(testing=False)
#   - init_db(seed_demo_users=True)
#   - run it on 0.0.0.0:5000
python backend/app.py
