import socket
import argparse
import threading
import random

class Server:
    
    HOSTNAME = "127.0.0.1"

    PORT = 30001
    RECV_SIZE = 1024
    BACKLOG = 5

    def __init__(self):
        self.next_room_id = 0
        print("Running server")
        self.directory = {} # A list of current chat rooms
        self.create_listen_socket()
        self.process_connections_forever()

    def create_room(self, address, port):
        pass

    def create_listen_socket(self):
        try:
            # Create the TCP server listen socket in the usual way.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((Server.HOSTNAME, Server.PORT))
            self.socket.listen(Server.BACKLOG)
            print("Chat Room Directory Server listening on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(msg)
            exit()
    
    def process_connections_forever(self):
        try:
            while True:
                self.connection_handler(self.socket.accept())
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()
    
    def connection_handler(self):
        pass

class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.username = f"User{random.randint(100)}"

    def run(self):
        # Get and parse input
        while True:
            self.user_input = input("Enter a command: ")

            if (self.user_input.lower() == "bye"):
                self.close_connection()
                break
            else:
                inputs = self.user_input.split()
                cmd = inputs[0]
                if (len(inputs) > 1):
                    args = inputs[1:]
                if(cmd.lower() == "connect"):
                    self.get_connection()

    def handle_connection(self):
        pass

    def handle_chat(self):
        pass

    def get_connection(self):
        pass

    def set_name(self, name):
        self.username = name

    def close_connection(self):
        self.socket.close()


if __name__ == '__main__':
    roles = {'client': Client,'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()