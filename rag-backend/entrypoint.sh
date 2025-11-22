#!/bin/sh

# Fix appuser permissions for mounted directories
chown -R appuser:appuser /app/chroma
chown -R appuser:appuser /app/uploads
chown -R appuser:appuser /app/temp

# Set user to appuser and run the app
exec runuser -u appuser -- "$@"