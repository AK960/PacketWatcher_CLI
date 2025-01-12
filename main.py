import socket
import threading
import time

# ==================== TCP-Server ====================
def start_tcp_server(port):
    def server_thread():
        address_family = socket.AF_INET
        server_socket = socket.socket(address_family, socket.SOCK_STREAM)
        bind_address = "0.0.0.0"
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((bind_address, port))
        server_socket.listen(5)
        print(f"TCP Server listening on port {port}... \n")

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"\nConnection from {client_address}")

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
                            packet_count = 1
                            print(f"[TCP-Server][P#{packet_count}] First packet: No IAT calculated.")
                            print(f"[TCP-Client]{message}.")
                        else:
                            # Calculate IAT
                            iat = recv_time - ref_time
                            ref_time = recv_time
                            packet_count += 1
                            print(f"[TCP-Server][P#{packet_count}] Inter-Arrival-Time (IAT): {iat} ms.")
                            print(f"[TCP-Client]{message}.")

                        # Respond to the client
                        server_response = f"[ACK] Messages acknowledged.\n"
                        try:
                            client_socket.sendall(server_response.encode())
                            #print(f"[TCP-Server]{server_response}.")
                        except Exception as e:
                            print(f"[TCP-Server] Error sending response to client: {e}")

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

# ==================== UDP-Server ====================
def start_udp_server(port):
    def server_thread():
        address_family = socket.AF_INET
        server_socket = socket.socket(address_family, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_address = "0.0.0.0"
        response_address = None
        server_socket.bind((bind_address, port))
        print(f"UDP Server listening on port {port}... \n")

        try:
            # Initialize variables
            ref_time = None
            packet_count = 0

            while True:
                # Receive a message and the client's address
                message, client_address = server_socket.recvfrom(1024)
                response_address = client_address
                recv_time = time.time() * 1000  # Current time in milliseconds
                message = message.decode()

                # Process IAT calculation
                if ref_time is None:
                    # First packet: no IAT calculation
                    ref_time = recv_time
                    packet_count = 1
                    print(f"[UDP-Server][P#{packet_count}] First packet: No IAT calculated.")
                    print(f"[UDP-Client]{message}.")
                else:
                    # Calculate IAT for subsequent packets
                    iat = recv_time - ref_time
                    ref_time = recv_time
                    packet_count += 1
                    print(f"[UDP-Server][P#{packet_count}] Inter-Arrival-Time (IAT): {iat} ms.")
                    print(f"[UDP-Client]{message}.")

                # Respond to the client
                server_response = f"[ACK] Messages acknowledged."
                if response_address:
                    try:
                        server_socket.sendto(server_response.encode(), response_address)
                        #print(f"[UDP-Server]{server_response}.")
                    except Exception as e:
                        print(f"[UDP-Server] Error sending response to client: {e}")

        except KeyboardInterrupt:
            print("UDP Server stopped.")
        finally:
            server_socket.close()
            print("Server socket closed.")

    threading.Thread(target=server_thread, daemon=True).start()

# ==================== TCP-Client ====================

def start_tcp_client(ip, port, n_packages, message):
    def client_thread():
        client_socket = None

        try:
            address_family = socket.AF_INET
            client_socket = socket.socket(address_family, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            ref_time = None
            print(f"Connected to TCP-Server {ip}:{port}")

            for i in range(n_packages):
                send_time = time.time() * 1000

                if ref_time is None:
                    ref_time = send_time
                    # Send message with newline
                    client_socket.sendall((message + "\n").encode())
                    print(f"[TCP-Client][P#{i+1}] First packet: No IAT calculated.")
                else:
                    iat = send_time - ref_time
                    ref_time = send_time
                    client_socket.sendall((message + "\n").encode())
                    print(f"[TCP-Client][P#{i+1}] Inter-Arrival-Time (IAT): {iat} ms")

            # Shutdown write side of connection to signal the server we are done
            client_socket.shutdown(socket.SHUT_WR)
            client_socket.settimeout(5.0)
            try:
                # Receive the final response from the server
                response = client_socket.recv(1024).decode()
                print(f"[TCP-Server]{response}")
            except socket.timeout:
                print("No response from server within 5 seconds. Closing socket.")

        except Exception as e:
            print(f"Error connecting to TCP server: {e}")
        finally:
            if client_socket:
                client_socket.close()
                print(f"Disconnected from TCP-Server {ip}:{port}")

    threading.Thread(target=client_thread, daemon=True).start()

# ==================== UDP-Client ====================
def start_udp_client(ip, port, n_packages, message):
    def client_thread():
        client_socket = None

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_address = (ip, port)
            ref_time = None

            for i in range(n_packages):
                send_time = time.time() * 1000

                if ref_time is None:
                    ref_time = send_time
                    # Send message to the server
                    client_socket.sendto(message.encode(), server_address)
                    print(f"[UDP-Client][P#{i+1}] First packet: No IAT calculated.")
                else:
                    iat = send_time - ref_time
                    ref_time = send_time
                    client_socket.sendto(message.encode(), server_address)
                    print(f"[UDP-Client][P#{i+1}] Inter-Arrival-Time (IAT): {iat} ms")

                # Set timeout for waiting for a response
                if i is n_packages-1:
                    #client_socket.settimeout(5.0)
                    try:
                        # Wait for a response after sending all packages
                        response, server_address = client_socket.recvfrom(1024)
                        print(f"[UDP-Server] {response.decode()}")
                    except socket.timeout:
                        print("No response from server within 5 seconds. Closing socket.")

        except Exception as e:
            print(f"Error during UDP communication: {e}")
        finally:
            if client_socket:
                client_socket.close()
                print("Socket closed.")

    threading.Thread(target=client_thread, daemon=True).start()

# ==================== Main ====================
def main():
    menu = """
Select mode:
1. Start TCP Server
2. Start TCP Client
3. Start UDP Server
4. Start UDP Client
5. Exit
Enter mode (1, 2, 3, 4, or 5):
==================================================
"""
    print(menu)

    while True:
        mode = input("$ ").strip()

        if mode == "1":
            # TCP Server Mode
            try:
                port = int(input("Enter port to start the TCP server: ").strip())
                print("Starting TCP Server...")
                start_tcp_server(port)
            except ValueError:
                print("Invalid port number. Please try again.\n")

        elif mode == "2":
            # TCP Client Mode
            try:
                ip = input("Enter TCP server IP address: ").strip()
                port = int(input("Enter TCP server port: ").strip())
                n_packages = int(input("Enter nPackets: ").strip())
                message = input("Enter message to send to TCP server: ").strip()
                print("\nStarting TCP Client...")
                start_tcp_client(ip, port, n_packages, message)
            except ValueError:
                print("Invalid input. Please check the IP, port, or message and try again.\n")

        elif mode == "3":
            # UDP Server Mode
            try:
                port = int(input("Enter port to start the UDP server: ").strip())
                print("Starting UDP Server...")
                start_udp_server(port)
            except ValueError:
                print("Invalid port number. Please try again.\n")

        elif mode == "4":
            # UDP Client Mode
            try:
                ip = input("Enter UDP server IP address: ").strip()
                port = int(input("Enter UDP server port: ").strip())
                n_packages = int(input("Enter nPackets: ").strip())
                message = input("Enter message to send to UDP server: ").strip()
                print("\nStarting UDP Client...")
                start_udp_client(ip, port, n_packages, message)
            except ValueError:
                print("Invalid input. Please check the IP, port, or message and try again.\n")

        elif mode == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.\n")

        # Delay before printing next input
        time.sleep(0.5)

if __name__ == "__main__":
    main()