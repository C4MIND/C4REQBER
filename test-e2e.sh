#!/bin/bash
# End-to-end test: start server, run client, stop server

cd /Users/figuramax/LocalProjects/TURBO-CDI/v8
source ../.venv/bin/activate

# Start server in background
PYTHONPATH=. python3 api/websocket/server.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server
sleep 2

# Run client
python3 ../test-ws-client.py
EXIT_CODE=$?

# Stop server
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

exit $EXIT_CODE
