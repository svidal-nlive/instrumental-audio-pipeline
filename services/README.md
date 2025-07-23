# Services

This directory contains the audio processing services for the Instrumental Maker pipeline.

## Services

- **spleeter/** - Spleeter-based stem separation service
- **demucs/** - Demucs-based stem separation service  
- **common/** - Shared utilities and libraries

## Usage

Each service is containerized and communicates with the main backend through the shared `/data` volume.

The services watch their respective input directories and process audio files according to the pipeline configuration.
