import socket
import argparse
import threading
import random

CMD = { "getdir": 1, "makeroom": 2, "deleteroom": 3}
CMD_FIELD_LEN = 1 # 1 byte commands sent from the client.
ENCODING = "utf-8"

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

    def create_listen_socket(self):
        try:
            # Create the TCP server listen socket in the usual way.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((Server.HOSTNAME, Server.PORT))
            self.socket.listen(Server.BACKLOG)
            print("Chat Room Directory Server listening on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(f"Error while creating listen socket: {msg}")
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
            
            if cmd == CMD["getdir"]:
                # Get and parse directory infor into packet for transmission
                print("Received getdir command.")
                pkt = ""
                for entry in self.get_dir():
                    pkt += f"{entry[0]}: ({entry[1]}, {entry[2]})\n"
                if pkt == "":
                    pkt = "There are currently no rooms available."
                pkt = pkt.encode(ENCODING)

            elif cmd == CMD["makeroom"]:
                print("Received makeroom command.")
                recv_bytes = connection.recv(Server.RECV_SIZE)
                recv_str = recv_bytes.decode(ENCODING)
                args = recv_str.split()
                self.create_room(args[0], args[1], args[2])
                pkt = None

            elif cmd == CMD["deleteroom"]:
                recv_bytes = connection.recv(Server.RECV_SIZE)
                recv_str = recv_bytes.decode(ENCODING)
                args = recv_str.split()
                self.destroy_room(args[0])
                pkt = None
            try:
                # Send the packet to the connected client.
                if pkt != None:
                    connection.sendall(pkt)
                # print("Sent packet bytes: \n", pkt)
                
            except socket.error:
                # If the client has closed the connection, close the
                # socket on this end.
                print("Closing client connection ...")
                connection.close()
                return

    def get_dir(self):
        arr = []
        for room in self.directory.values():
            arr.append(room.get_info())
        return arr

    def create_room(self, name, address, port):
        self.directory[name] = ChatRoom(name, address, port)
    
    def destroy_room(self, name):
        self.directory.pop(name)

class ChatRoom:

    def __init__(self, name, ip, port):
        self.port = int(port)
        self.ip = ip
        self.name = name

    def get_info(self):
        return (self.name, self.ip, self.port)
    

class Client:

    RECV_SIZE = 1024
    CLI_MODES = {"CRDS": 1, "CHAT": 2, "NC": 3}
    def __init__(self):
        self.username = f"User{random.randint(0, 100)}"
        self.get_socket()
        self.mode = Client.CLI_MODES["NC"]
        self.nc_prompt()

    def crds_prompt(self):
        while True:
            self.user_input = input(f"[{self.username}, CRDS] Enter a command: ")
            if self.handle_input() == None:
                self.mode = Client.CLI_MODES["NC"]
                break

    def nc_prompt(self):
        while True:
            self.user_input = input(f"[{self.username}, local] Enter a command: ")
            if self.handle_input() == None:
                break

    def handle_input(self):
        inputs = self.user_input.split()
        cmd = inputs[0]
        if (len(inputs) > 1):
            args = inputs[1:]

        if (self.mode == Client.CLI_MODES["NC"]):
            if (cmd.lower() == "q"):
                return None
            elif(cmd.lower() == "connect"):
                self.connect_to_server()
                self.mode = Client.CLI_MODES["CRDS"]
                self.crds_prompt()
            elif(cmd.lower() == "name"):
                self.set_name(args[0])

        elif (self.mode == Client.CLI_MODES["CRDS"]):
            if (cmd.lower() == "bye"):
                self.close_connection()
                return None
            elif (cmd.lower() == "getdir"):
                self.handle_getdir_command()
            elif (cmd.lower() == "makeroom"):
                try:
                    self.handle_makeroom_command(args[0], args[1], args[2])
                except:
                    print("Invalid arguments. Try agian.")
            elif (cmd.lower() == "deleteroom"):
                try:
                    self.handle_deleteroom_command(args[0])
                except:
                    print("Invalid arguments. Try agian.")
            elif (cmd.lower() == "chat"):
                
                rooms = self.handle_getdir_command(parse=True)
                room = rooms.get(args[0])
                if room != None:
                    self.handle_chat(room)
                else:
                    print("Invalid room name. Please try again.")
                
            else:
                print("Invalid command. Please try again.")

        else:
            #Handle chats
            pass
        return True  
           

    def chat_prompt(self):
        pass

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

    def handle_getdir_command(self, parse=False):
        # Build and send the command packet
        pkt = CMD["getdir"].to_bytes(CMD_FIELD_LEN, byteorder='big')
        self.socket.sendall(pkt)

        # Await response
        recv_bytes = self.socket.recv(Client.RECV_SIZE)
        recv_str = recv_bytes.decode(ENCODING)

        if not parse:
            print(f"Recieved response from server:\n{recv_str}")
        
        if parse:
            rooms = recv_str.split("\n")
            rooms_dict = {}
            for room in rooms:
                if len(room) > 0:
                    name, address = room.split(":")
                    ip, port = address.lstrip()[1:-1].split(", ")
                    rooms_dict[name] = (ip, int(port))
            return rooms_dict
            

    def handle_makeroom_command(self, name, ip, port):
        # Build and send the command packet
        cmd_field = CMD["makeroom"].to_bytes(CMD_FIELD_LEN, byteorder='big')

        args_field = f"{name} {ip} {port}".encode(ENCODING)
        pkt = cmd_field + args_field

        self.socket.sendall(pkt)

    def handle_deleteroom_command(self, name):
        # Build and send the command packet
        cmd_field = CMD["deleteroom"].to_bytes(CMD_FIELD_LEN, byteorder='big')

        args_field = name.encode(ENCODING)
        pkt = cmd_field + args_field

        self.socket.sendall(pkt)

    def handle_chat(self, room):
        print(f"Handle chat: {room}")

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