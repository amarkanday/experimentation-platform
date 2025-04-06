#!/usr/bin/env python3
import subprocess
import re

def close_close_wait_connections_mac():
    """Closes TCP connections in CLOSE_WAIT state on macOS."""

    try:
        netstat_output = subprocess.check_output(["netstat", "-an", "|", "grep", "tcp", "|", "grep", "CLOSE_WAIT"], shell=True, text=True)
        lines = netstat_output.strip().split("\n")

        for line in lines:
            if "CLOSE_WAIT" in line:
                print(f"Processing line: {line}") # Debugging print
                local_address = re.search(r"([\d\.]+:\d+)", line.split()[3]).group(1) # Extract local address:port
                remote_address = re.search(r"([\d\.]+:\d+)", line.split()[4]).group(1) # Extract remote address:port
                print(f"Local address: {local_address}, Remote address: {remote_address}") # Debugging print

                try:
                    lsof_output = subprocess.check_output(["lsof", "-n", "-P", "-i", f"tcp:{local_address}"], text=True, timeout=5) #Added timeout
                    print(f"lsof output: {lsof_output}") # Debugging print
                    pid_match = re.search(r"\n\S+\s+(\d+)", lsof_output)

                    if pid_match:
                        pid = pid_match.group(1)
                        print(f"PID: {pid}") #Debugging print
                        try:
                            print(f"Killing PID: {pid}") #Debugging print
                            subprocess.run(["kill", "-HUP", pid], check=True)
                            print(f"Killed PID: {pid}, Local: {local_address}, Remote: {remote_address}")
                        except subprocess.CalledProcessError as e:
                            print(f"Error killing connection (PID: {pid}): {e}")
                    else:
                        print(f"PID not found for line: {line}")

                except subprocess.CalledProcessError as e:
                    print(f"Error running lsof: {e}")
                except subprocess.TimeoutExpired:
                    print(f"lsof timed out for local address: {local_address}") #print timeout errors.

    except subprocess.CalledProcessError as e:
        print(f"Error running netstat: {e}")
    except FileNotFoundError:
        print("netstat or lsof not found. Please ensure they are installed.")


if __name__ == "__main__":
    close_close_wait_connections_mac()
