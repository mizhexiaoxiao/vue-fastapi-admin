#!/bin/sh
set -e

nginx
uvicorn app:app --reload --host 0.0.0.0 --port 9999 