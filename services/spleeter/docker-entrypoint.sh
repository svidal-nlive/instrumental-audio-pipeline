#!/bin/bash
set -e

# Make sure pipeline data directory is writable
mkdir -p /pipeline-data/output
mkdir -p /pipeline-data/error
mkdir -p /pipeline-data/archive
# Create model directory for persistence
mkdir -p /pipeline-data/models/spleeter

# If PUID/PGID are set, set proper permissions and run as that user
if [ -n "$PUID" ] && [ -n "$PGID" ]; then
    # Change ownership of pipeline directories and model cache
    chown -R $PUID:$PGID /pipeline-data
    
    # Run as the specified user
    exec gosu $PUID:$PGID "$@"
else
    # If no PUID/PGID specified, run as current user
    exec "$@"
fi
