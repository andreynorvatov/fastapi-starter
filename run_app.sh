#!/bin/bash
granian \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --interface asgi \
  --log-level info \
  --access-log \
  --reload \
  src.main:app