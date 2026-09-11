# MKALFLAWLESS Shorts Creator Backend

Render-ready FFmpeg backend for the MKALFLAWLESS mobile Shorts Creator.

## Render
Deploy as a Web Service using the included Dockerfile.

Endpoints:
- GET /health
- POST /export

The export endpoint accepts a video plus reel start/length, camera crop, camera top/bottom, and gameplay horizontal position, and returns a 1080x1920 MP4.
