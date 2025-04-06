#!/bin/bash

# This script closes TCP connections in the CLOSE_WAIT state on macOS.

netstat -an | grep tcp | grep CLOSE_WAIT | while read line; do
  # Extract the local address and port.
  local_address=$(echo "$line" | awk '{print $4}')

  # Use lsof to find the PID associated with the local address.
  pid=$(lsof -n -P -i "tcp:$local_address" -t) # -t option returns only the pid

  if [[ -n "$pid" ]]; then
    # Send a HUP signal to the process to gracefully close the connection.
    if kill -HUP "$pid"; then
      echo "Closed connection (PID: $pid, Local: $local_address)"
    else
      echo "Error closing connection (PID: $pid, Local: $local_address)"
    fi
  else
    echo "PID not found for local address: $local_address"
  fi
done

if [ $? -ne 0 ]; then
  echo "Error running netstat, lsof, or kill."
fi
