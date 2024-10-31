#!/bin/bash

echo "Starting stream forwarder" >> /var/log/nginx/stream_forwarder.log
echo "Arguments: $@" >> /var/log/nginx/stream_forwarder.log

ffmpeg -re -i rtmp://localhost:1935/live/$1 \
       -c copy -f mpegts \
       -loglevel info \
       "srt://ingest.af-south-1.pulselive.tv:25000?streamid=publisher/sctm/$1&mode=caller&latency=200000" \
       2>> /var/log/nginx/ffmpeg-debug.log

echo "FFmpeg exited with code $?" >> /var/log/nginx/stream_forwarder.log