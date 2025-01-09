import socket
import threading
import time

def start_tcp_server(port):
    """Start a TCP server with IAT calculation."""

    def server_thread():
        address_family = socket.AF_INET
        server_socket = socket.socket(address_family, socket.SOCK_STREAM)
        bind_address = "0.0.0.0"
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((bind_address, port))
        server_socket.listen(5)
        print(f"TCP Server listening on port {port}...")

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")

                try:
                    # Initialize variables for IAT calculation
                    ref_time = None
                    packet_count = 0

                    while True:
                        # Receive a message from the client
                        message = client_socket.recv(1024).decode()
                        if not message:  # Client disconnected
                            break

                        # Current time
                        recv_time = time.time() * 1000  # Convert to milliseconds

                        if ref_time is None:
                            # First packet, no IAT calculation
                            ref_time = recv_time
                            print(f"[Client: {client_address}] First packet received. No IAT calculated.")
                            server_response = f"[P#{packet_count}] [S-IAT: null]\n"
                        else:
                            # Calculate IAT
                            iat = recv_time - ref_time
                            ref_time = recv_time
                            packet_count += 1
                            print(f"[Client: {client_address}] Received: {message}")
                            print(f"[Client: {client_address}] Inter-Arrival-Time (IAT): {iat} ms")
                            server_response = f"[P#{packet_count}] [S-IAT: {iat:.2f} ms]\n"

                        # Respond to the client
                        client_socket.sendall(server_response.encode())

                except Exception as e:
                    print(f"Error while processing client messages: {e}")
                finally:
                    client_socket.close()
                    print(f"Connection with {client_address} closed.\n")
        except KeyboardInterrupt:
            print("TCP Server stopped.")
        finally:
            server_socket.close()
            print("Server socket closed.")

    threading.Thread(target=server_thread, daemon=True).start()

def start_udp_server(port):
    """Start a UDP server with IAT calculation."""

    def server_thread():
        address_family = socket.AF_INET
        server_socket = socket.socket(address_family, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_address = "0.0.0.0"
        server_socket.bind((bind_address, port))
        print(f"UDP Server listening on port {port}...")

        try:
            # Initialize variables
            ref_time = None
            packet_count = 0

            while True:
                # Receive a message and the client's address
                message, client_address = server_socket.recvfrom(1024)
                recv_time = time.time() * 1000  # Current time in milliseconds
                decoded_message = message.decode()

                # Process IAT calculation
                if ref_time is None:
                    # First packet: no IAT calculation
                    ref_time = recv_time
                    packet_count = 1
                    print(f"[Client: {client_address}] First packet received. No IAT calculated.")
                    server_response = f"[P#{packet_count}] [IAT: null]\n{decoded_message}"
                else:
                    # Calculate IAT for subsequent packets
                    iat = recv_time - ref_time
                    ref_time = recv_time
                    packet_count += 1
                    print(f"[Client: {client_address}] Received: {decoded_message}")
                    print(f"[Client: {client_address}] Inter-Arrival-Time (IAT): {iat:.2f} ms")
                    server_response = f"[P#{packet_count}] [IAT: {iat:.2f} ms]\n{decoded_message}"

                # Respond to the client
                server_socket.sendto(server_response.encode(), client_address)
                print(f"Response sent to {client_address}")

        except KeyboardInterrupt:
            print("UDP Server stopped.")
        finally:
            server_socket.close()
            print("Server socket closed.")

    threading.Thread(target=server_thread, daemon=True).start()

def start_tcp_client(ip, port, n_packages, message):
    """Start a TCP client."""
    try:
        address_family = socket.AF_INET
        client_socket = socket.socket(address_family, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        print(f"Connected to TCP server {ip}:{port}")

        for i in range(n_packages):
            # Send message with newline
            client_socket.sendall((message + "\n").encode())
            print(f"Package {i + 1} sent to server {ip}:{port}")

        # Optionally, shutdown the write side of the connection to signal the server that we are done
        client_socket.shutdown(socket.SHUT_WR)

        # Receive the final response from the server
        response = client_socket.recv(1024).decode()
        print(f"TCP Server responded: {response}")

    except Exception as e:
        print(f"Error connecting to TCP server: {e}")
    finally:
        client_socket.close()
        print("Connection closed.")


def start_udp_client(ip, port, n_packages, message):
    """Start a UDP client."""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (ip, port)

        for i in range(n_packages):
            # Send message to the server
            client_socket.sendto(message.encode(), server_address)
            print(f"Package {i + 1} sent to server {ip}:{port}")

        # Wait for a response after sending all packages
        response, server_address = client_socket.recvfrom(1024)
        print(f"UDP Server responded from {server_address}: {response.decode()}")

    except Exception as e:
        print(f"Error during UDP communication: {e}")
    finally:
        client_socket.close()

def main():
    while True:
        print("\nSelect mode: ")
        print("1. Start TCP Server")
        print("2. Start TCP Client")
        print("3. Start UDP Server")
        print("4. Start UDP Client")
        print("5. Exit")
        mode = input("Enter mode (1, 2, 3, 4, or 5): ").strip()

        if mode == "1":
            # TCP Server Mode
            try:
                port = int(input("Enter port to start the TCP server: ").strip())
                print("Starting TCP Server...")
                start_tcp_server(port)
            except ValueError:
                print("Invalid port number. Please try again.")
        elif mode == "2":
            # TCP Client Mode
            try:
                ip = input("Enter TCP server IP address: ").strip()
                port = int(input("Enter TCP server port: ").strip())
                n_packages = int(input("Enter nPackets: ").strip())
                message = input("Enter message to send to TCP server: ").strip()
                print("Starting TCP Client...")
                start_tcp_client(ip, port, n_packages, message)
            except ValueError:
                print("Invalid input. Please check the IP, port, or message and try again.")
        elif mode == "3":
            # UDP Server Mode
            try:
                port = int(input("Enter port to start the UDP server: ").strip())
                print("Starting UDP Server...")
                start_udp_server(port)
            except ValueError:
                print("Invalid port number. Please try again.")
        elif mode == "4":
            # UDP Client Mode
            try:
                ip = input("Enter UDP server IP address: ").strip()
                port = int(input("Enter UDP server port: ").strip())
                n_packages = int(input("Enter nPackets: ").strip())
                message = input("Enter message to send to UDP server: ").strip()
                print("Starting UDP Client...")
                start_udp_client(ip, port, n_packages, message)
            except ValueError:
                print("Invalid input. Please check the IP, port, or message and try again.")
        elif mode == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
4
