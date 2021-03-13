#!/usr/bin/env python3

########################################################################
#
# GET File Transfer
#
# When the client connects to the server, it immediately sends a
# 1-byte GET command followed by the requested filename. The server
# checks for the GET and then transmits the file. The file transfer
# from the server is prepended by an 8 byte file size field. These
# formats are shown below.
#
# The server needs to have REMOTE_FILE_NAME defined as a text file
# that the client can request. The client will store the downloaded
# file using the filename LOCAL_FILE_NAME. This is so that you can run
# a server and client from the same directory without overwriting
# files.
#
########################################################################

import socket
import argparse
import threading
import os
import json

from service_announcement import Server as DiscoveryServer
from service_discovery_cycles import Client as DiscoveryClient

########################################################################

# Define all of the packet protocol field lengths. See the
# corresponding packet formats below.
CMD_FIELD_LEN = 1 # 1 byte commands sent from the client.
FILE_SIZE_FIELD_LEN  = 8 # 8 byte file size field.
FILE_NAME_FIELD_LEN = 127
PACKET_SIZE_FIELD_LEN = 8

# Packet format when a GET command is sent from a client, asking for a
# file download:

# -------------------------------------------
# | 1 byte GET command  | ... file name ... |
# -------------------------------------------

# When a GET command is received by the server, it reads the file name
# then replies with the following response:

# -----------------------------------
# | 8 byte file size | ... file ... |
# -----------------------------------

# Define a dictionary of commands. The actual command field value must
# be a 1-byte integer. For now, we only define the "GET" command,
# which tells the server to send a file.

CMD = { "PUT": 1, "GET": 2, "SCAN": 3, "CONNECT": 4, "LLIST": 5, "RLIST": 6, "BYE": 7 }

MSG_ENCODING = "utf-8"
    
########################################################################
# SERVER
########################################################################

class Server:

    HOSTNAME = "127.0.0.1"

    PORT = 30001
    RECV_SIZE = 1024
    BACKLOG = 5

    FILE_NOT_FOUND_MSG = "Error: Requested file is not available!"
    DIR_NAME = "server_dir"

    def __init__(self):
        # Start discovery server thread
        self.discovery_server = None
        self.discovery_thread = threading.Thread(target=self.create_discovery_server)
        self.discovery_thread.start()

        
        self.create_listen_socket()

        print("-" * 72)
        print("Files available in shared directory:\n")

        for item in os.listdir(Server.DIR_NAME):
            print(item)
        self.process_connections_forever()
        

    def create_discovery_server(self):
        self.discovery_server = DiscoveryServer()

    def create_listen_socket(self):
        try:
            # Create the TCP server listen socket in the usual way.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((Server.HOSTNAME, Server.PORT))
            self.socket.listen(Server.BACKLOG)
            print("Listening on for file sharing connections on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(msg)
            exit()

    def process_connections_forever(self):
        try:
            while True:
                threading.Thread(target=self.connection_handler(self.socket.accept())).start()
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()

    def connection_handler(self, client):
        connection, address = client
        print("-" * 72)
        print(f"Connection received from {address[0]} on port {address[1]}.")

        while True:
            recvd = connection.recv(CMD_FIELD_LEN)
            if len(recvd) == 0:
                print("Connection closed by client.")
                connection.close()
                return

            cmd = int.from_bytes(recvd, byteorder='big')
            
            if cmd == CMD["GET"]:
                recv_bytes = connection.recv(Server.RECV_SIZE)
                recv_string = recv_bytes.decode(MSG_ENCODING)
                pkt = self.handle_get_cmd(recv_string, connection)
            elif cmd == CMD["RLIST"]:
                print("Received rlist command.")
                pkt = self.handle_list_cmd()
            elif cmd == CMD["PUT"]:
                recv_bytes = connection.recv(Server.RECV_SIZE)
                pkt = self.handle_put_cmd(recv_bytes, conn)

            
            try:
                # Send the packet to the connected client.
                connection.sendall(pkt)
                # print("Sent packet bytes: \n", pkt)
                
            except socket.error:
                # If the client has closed the connection, close the
                # socket on this end.
                print("Closing client connection ...")
                connection.close()
                return
    
    def handle_get_cmd(self, filename, conn):
        # Open the requested file and get set to send it to the
        # client.
        try:
            file = open(f"{Server.DIR_NAME}/{filename}", 'r').read()
        except FileNotFoundError:
            print(Server.FILE_NOT_FOUND_MSG)
            conn.close()                   
            return

        # Encode the file contents into bytes, record its size and
        # generate the file size field used for transmission.
        file_bytes = file.encode(MSG_ENCODING)
        file_size_bytes = len(file_bytes)
        file_size_field = file_size_bytes.to_bytes(FILE_SIZE_FIELD_LEN, byteorder='big')

        # Create the packet to be sent with the header field.
        pkt = file_size_field + file_bytes
        
        return pkt

    def handle_put_cmd(self, filebytes, conn):
        # Extract information about file
        filename = filebytes[:FILE_NAME_FIELD_LEN].decode(MSG_ENCODING)
        file_size = int.from_bytes(filebytes[FILE_NAME_FIELD_LEN:FILE_SIZE_FIELD_LEN])
        file_contents = bytearray(filebytes[FILE_SIZE_FIELD_LEN:])
        
        while(len(file_contents) < file_size):
            # Recv until entire file is uploaded
            recvd = conn.recv(Server.RECV_SIZE)
            file_contents += recvd

            if (len(recvd) == 0):
                print("Error while receiving file, closing connection.")
                conn.close()
                return
                

        # Write the file 
        try:
            with open(f"{Server.DIR_NAME}/{filename}", "w") as f:
                f.write(file_contents.decode(MSG_ENCODING))
            print(f"Received file: {filename}")
        except Exception as e:
            print(f"Error writing file {filename}: {e}")

    def handle_list_cmd(self):
        # Read contents of shared directory and build a list of the contents
        dir_contents = os.listdir(Server.DIR_NAME)
        pkt_string = ""
        print(dir_contents)
        for item in dir_contents:
            pkt_string += f"{item}\n"

        pkt_bytes = pkt_string.encode(MSG_ENCODING)

        pkt_size_bytes = len(pkt_bytes)
        pkt_size_field = pkt_size_bytes.to_bytes(PACKET_SIZE_FIELD_LEN, byteorder='big')

        return pkt_size_field + pkt_bytes

########################################################################
# CLIENT
########################################################################

class Client:

    RECV_SIZE = 10

    # Define the local file name where the downloaded file will be
    # saved.
    DIR_NAME = "client_dir"

    def __init__(self):
        self.get_socket()
        self.discovery_client = DiscoveryClient()
        self.run()

    def run(self):
        while True:
            cmd, args = self.get_input()
            if cmd == CMD["PUT"]:
                if len(args) >= 2:
                    self.put_file(args[0], args[1])
            elif cmd == CMD["GET"]:
                if len(args) >= 2:
                    self.get_file(args[0], args[1])
            elif cmd == CMD["SCAN"]:
                self.discovery_client.scan_for_service()
            elif cmd == CMD["CONNECT"]:
                if len(args) < 2:
                    self.connect_to_server()
                else:
                    self.connect_to_server(args[0], args[1])
            elif cmd == CMD["LLIST"]:
                if len(args) < 1:
                    self.get_local_list()
                else:
                    self.get_local_list(args[0])
            elif cmd == CMD["RLIST"]:
                self.get_remote_list()
            elif cmd == CMD["BYE"]:
                self.close_connection()
                return
    
    def get_local_list(self, dir=None):
        if dir == None:
            dir = Client.DIR_NAME
        contents = os.listdir(dir)
        for entry in contents:
            print(f"{entry}")

    def get_input(self):
        # Get user input and act
        while True:
            user_input = input("Enter a command: ")
            args = user_input.split(" ")
            if len(args) > 1:
                user_input = args[0]
                args = args[1:]
            else:
                args = []

            if user_input == "quit":
                return CMD["BYE"], args
            user_input = user_input.upper()
            for cmd_string, cmd_byte in CMD.items():
                if user_input == cmd_string:
                    return cmd_byte, args
            
            print("Invalid command, please try again.")

    def get_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as msg:
            print(msg)
            exit()

    def connect_to_server(self, ip=Server.HOSTNAME, port=Server.PORT):
        try:
            self.socket.connect((ip, port))
            print(f"Connected to server at {ip}:{port}")
        except Exception as msg:
            print(msg)
            exit()

    def socket_recv_size(self, length):
        bytes = self.socket.recv(length)
        if len(bytes) < length:
            self.socket.close()
            exit()
        return(bytes)
            
    def get_file(self, remote_filename, local_filename):

        # Create the packet GET field.
        get_field = CMD["GET"].to_bytes(CMD_FIELD_LEN, byteorder='big')

        # Create the packet filename field.
        filename_field = remote_filename.encode(MSG_ENCODING)

        # Create the packet.
        pkt = get_field + filename_field

        # Send the request packet to the server.
        self.socket.sendall(pkt)

        # Read the file size field.
        file_size_bytes = self.socket_recv_size(FILE_SIZE_FIELD_LEN)
        if len(file_size_bytes) == 0:
            self.socket.close()
            return

        # Make sure that you interpret it in host byte order.
        file_size = int.from_bytes(file_size_bytes, byteorder='big')

        # Receive the file itself.
        recvd_bytes_total = bytearray()
        try:
            # Keep doing recv until the entire file is downloaded. 
            while len(recvd_bytes_total) < file_size:
                recvd_bytes_total += self.socket.recv(Client.RECV_SIZE)

            # Create a file using the received filename and store the
            # data.
            print("Received {} bytes. Creating file: {}" \
                  .format(len(recvd_bytes_total), local_filename))

            with open(f"{Client.DIR_NAME}/{local_filename}", 'w') as f:
                f.write(recvd_bytes_total.decode(MSG_ENCODING))
        except KeyboardInterrupt:
            print()
            exit(1)
        # If the socket has been closed by the server, break out
        # and close it on this end.
        except socket.error:
            self.socket.close()
    
    def put_file(self, local_filename, remote_filename):
        pass

    def get_remote_list(self):
        # Helper function to test rlist command
        pkt = CMD["RLIST"].to_bytes(CMD_FIELD_LEN, byteorder='big')
        self.socket.sendall(pkt)
        list_size_bytes = self.socket_recv_size(PACKET_SIZE_FIELD_LEN)
        list_size = int.from_bytes(list_size_bytes, byteorder='big')
        if len(list_size_bytes) == 0:
            self.socket.close()
            return

        recvd_bytes = bytearray()
        while(len(recvd_bytes) < list_size):
            recvd_bytes += self.socket.recv(Client.RECV_SIZE)

        recvdstring = recvd_bytes.decode(MSG_ENCODING)
        print(recvdstring)
    
    def close_connection(self):
        self.socket.close()
        print("Closed connection.")
            
########################################################################

if __name__ == '__main__':
    roles = {'client': Client,'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################






