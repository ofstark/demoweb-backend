#!/usr/bin/env bash
# Convenience script to run the dev server.
uvicorn app.main:app --reload --port 8000
