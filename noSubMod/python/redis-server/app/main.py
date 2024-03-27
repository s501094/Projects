import socket
import threading
import time
import argparse

READ_BUFFER = 1024
responsePong = "+PONG\r\n"
BULK_STRING = "$-1\r\n"
randomDictionary = {}
infoDictionary = {"role": "master", "connected_clients": 1, "connected_slaves": 0, "db0": {"keys": 0, "expires": 0}}


def main(port, replicaof):
    print(f"Starting main function with port={port} and replicaof={replicaof}")
    if replicaof is not None:
        master_host, master_port = replicaof
        print(f"Starting replication with master_host={master_host} and master_port={master_port}")
        # Start replication in a separate thread
        replication_thread = threading.Thread(target=start_replication, args=(master_host, master_port))
        replication_thread.start()
    else:
        print("No replicaof argument provided, starting as master")
    # Start the server in either case
    print(f"Starting server on port={port}")
    start_server(port)

def start_replication(master_host, master_port):
    print("Starting replication...")
    master_port = int(master_port)  # Convert master_port to an integer
    client_socket = socket.create_connection((master_host, master_port))
    while True:
        data = client_socket.recv(READ_BUFFER)
        if not data:
            break  # Server closed connection
        # Process data...
    # Update the role to replica after the replication has completed
    global infoDictionary
    infoDictionary["role"] = "replica"
    print("Role set to replica")

def start_server(port):
    print("Starting server...")
    server_socket = socket.create_server(("0.0.0.0", port), reuse_port=True)
    while True:
        conn, addr = server_socket.accept()  
        handler = threading.Thread(target= request_handler, args=(conn,))
        handler.start()

def request_handler(conn):
    while True:
        try:
            connect_data = conn.recv(READ_BUFFER).decode()
            # Ensure that there's data to process
            if not connect_data:
                break  # No data received, possibly close connection

            parts = connect_data.strip().split("\r\n")
            # Ensure that the received data has enough parts to extract a command
            if len(parts) < 3:
                # Not enough parts for a valid command, log error, or handle accordingly
                print("Error: Command format is incorrect.")
                continue  # Skip to the next iteration

            command = parts[2].lower()
            if command == "echo":
                conn.send("+".encode() + parts[4].encode() + "\r\n".encode())
            elif command == "ping":
                conn.send("+PONG\r\n".encode())
            elif command == "set":
                handle_set_command(parts, conn)
            elif command == "get":
                handle_get_command(parts, conn)
            elif command == "info":
                handle_info_command(parts, conn)                                                      #FIX ME: Uncomment and fix dictionary
            elif command == "quit":
                conn.send("+OK\r\n".encode())
                break
        except IndexError as e:
            # Handle the case where parts do not contain the expected indices
            print(f"Error processing command: {e}")
            # Optionally send an error response back to the client
            conn.send("-Error: Command processing failed.\r\n".encode())
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            break  


def handle_set_command(parts, conn):
    key = parts[4]
    value = parts[6]
    if "px" in parts:
        px_Place = parts.index("px") + 2
        expiry_ms = int(parts[px_Place])
        expiry_time = time.time() + (expiry_ms / 1000.0)
    else:
        expiry_time = None  # Default expiry time is None
    # Loop through the parts to find the "px" option and its value
    for i in range(len(parts)):
        if parts[i].lower() == "px" and i + 1 < len(parts):
            try:
                expiry_ms = int(parts[i + 1])
                expiry_time = time.time() + (expiry_ms / 1000.0)
                break  # Exit the loop once the px option is handled
            except ValueError:
                # Log or handle the case where the px value is not an integer
                pass
    # Store the key, value, and expiry time in the dictionary
    randomDictionary[key] = (value, expiry_time)
    #print(randomDictionary[key])
    conn.send("+OK\r\n".encode())

def handle_get_command(parts, conn):
    key = parts[4]
    if key in randomDictionary:
        value, expiry_time = randomDictionary[key]
        current_time = time.time()
        # Check if the key has expired
        if expiry_time is not None and current_time > expiry_time:
            del randomDictionary[key]  # Remove expired key
            conn.send(BULK_STRING.encode())  # Send null bulk string to indicate expired key
        else:
            # Key has not expired, send the value
            conn.send("$".encode() + str(len(value)).encode() + "\r\n".encode() + value.encode() + "\r\n".encode())
    else:
        # Key does not exist, send null bulk string
        conn.send(BULK_STRING.encode())

def handle_info_command(parts, conn):
    #conn.send("+".encode() + "Replication".encode() + "\r\n".encode())
    for i in infoDictionary:
        conn.send("+".encode() + i.encode() + ":".encode() + str(infoDictionary[i]).encode() + "\r\n".encode())

def arg_parser():
    parser = argparse.ArgumentParser(description="Redis Server")
    parser.add_argument("-p","--port", type=int, help="Port number", default=6379)
    parser.add_argument("-r" , "--replicaof", nargs=2, type=str, help="Replicate to another server", default=None)
    args = parser.parse_args()
    return args



if __name__ == "__main__":
    # print("starting server"
    args = arg_parser()
    main(args.port, args.replicaof)

