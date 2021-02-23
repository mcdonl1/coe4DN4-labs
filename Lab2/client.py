"""
client.py

A socket API client to fulfill the requirements detailed in the lab description pdf file.
"""
import socket
import sys
import getpass
import hashlib
import json


class Client:
    MSG_ENCODING = "utf-8"
    RECV_BUFFER_SIZE = 1024

    GET_MIDTERM_AVG_CMD = "GMA"
    GET_LAB_1_AVG_CMD = "GLA1"
    GET_LAB_2_AVG_CMD = "GLA2"
    GET_LAB_3_AVG_CMD = "GLA3"
    GET_LAB_4_AVG_CMD = "GLA4"
    GET_GRADES_CMD = "GG"

    def __init__(self, hostname=socket.gethostbyname("localhost"), port=1234):
        self.hostname = hostname
        self.port = port
        self.run()
        
    
    def socket_setup(self):
        try:
            # Create an IPv4 TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            print(e)
            sys.exit(1)
        
    def get_user_input(self):
        self.user_input = input("Enter command: ")
        print(f"Command entered: {self.user_input}")
    
    def run(self):
        while True:
            self.get_user_input()
            if self.user_input == "q":
                #End program
                self.socket.close()
                sys.exit(1)
            elif self.user_input.upper() == Client.GET_MIDTERM_AVG_CMD:
                print("Fetching Midterm average:")
            elif self.user_input.upper() == Client.GET_LAB_1_AVG_CMD:
                print("Fetching Lab 1 average:")
            elif self.user_input.upper() == Client.GET_LAB_2_AVG_CMD:
                print("Fetching Lab 2 average:")
            elif self.user_input.upper() == Client.GET_LAB_3_AVG_CMD:
                print("Fetching Lab 3 average:")
            elif self.user_input.upper() == Client.GET_LAB_4_AVG_CMD:
                print("Fetching Lab 4 average:")
            
            if self.user_input.upper() == Client.GET_GRADES_CMD:
                payload = self.get_auth_hash()
            else:
                payload = self.user_input.encode(Client.MSG_ENCODING)

            # Connect and send payload to server
            try:
                self.socket_setup()
                self.socket.connect((self.hostname, self.port))
                self.socket.sendall(payload)
            except Exception as e:
                print(e)
                continue

            if self.user_input.upper() == Client.GET_GRADES_CMD:
                print(f"ID/password hash {payload} sent to server.")

            # Wait for server response
            recvd_bytes = self.socket.recv(Client.RECV_BUFFER_SIZE)
            recvd_string = recvd_bytes.decode(Client.MSG_ENCODING)

            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)
            
            # for GG command, format response
            copy = recvd_string
            if self.user_input.upper() == Client.GET_GRADES_CMD:
                try:
                    grades = json.loads(recvd_string, strict=False)
                    recvd_string = "\n"
                    for key, val in grades.items():
                        recvd_string += f"{key}: {val}\n"
                except Exception as e:
                    recvd_string = copy

            #display response       
            print(f"Server response: {recvd_string}")
            self.socket.close()

    def get_auth_hash(self):
        try:
            id = input("Enter Student ID: ")
            pswd = getpass.getpass(prompt="Enter Password: ")
            print(f"ID number {id} and password {pswd} received.")
            return _get_hash(id, pswd)
        except Exception as e:
            print(f"Error getting authorization: {e}")



# Util functions

def _get_hash(id, password):
        h = hashlib.sha256() # Create sha256 hash object
        # Update object with id and password
        h.update(id.encode("utf-8")) 
        h.update(password.encode("utf-8"))
        # return the hash
        return h.digest()

HELPTEXT = "\nThis command can be run to create an IPv4 TCP client. The IP address and port number\
can be provided as command line arguments, in that order.\n"

if __name__ == "__main__":
    if len(sys.argv) == 2 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print(HELPTEXT)
        print("NOTE: All command line args are required, OR none.")
        print('i.e. Use "python client.py" for defaults OR "python client.py ip port".')
        sys.exit(0)
    if len(sys.argv) == 1:
        # If no cli args are provided
        client = Client()
    else:
        # Use cli args instead of defauls
        try:
            client = client(ip_address=sys.argv[1], port=int(sys.argv[2]), file_name=sys.argv[3])
        except Exception:
            print("\nAn error occured setting up the server.\n")
            print("NOTE: All command line args are required, OR none.")
            print('i.e. Use "python server.py" for defaults OR "python server.py ip port".')
