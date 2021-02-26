"""
main.py

A socket API client and server to fulfill the requirements detailed in the lab description pdf file.
"""
import socket
import sys
import getpass
import hashlib
import json
import csv


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
                try:
                    self.socket.close()
                finally:
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

CSV_FILE_NAME = "course_grades_2021.csv"

class Server:

    # Command string consts
    GET_MIDTERM_AVG_CMD = "GMA"
    GET_LAB_1_AVG_CMD = "GLA1"
    GET_LAB_2_AVG_CMD = "GLA2"
    GET_LAB_3_AVG_CMD = "GLA3"
    GET_LAB_4_AVG_CMD = "GLA4"

    MAX_CONNECTION_BACKLOG = 10
    RECV_BUFFER_SIZE = 1024

    MSG_ENCODING = "utf-8"

    def __init__(self, ip_address='localhost', port=1234, file_name=CSV_FILE_NAME):
        # Set up and run server

        # Add students
        self.students = {}
        self.averages = {}
        self.read_csv(file_name)

        # Socket init
        self.address = (ip_address, port)
        self.socket_setup()

        # Handle connections
        self.handle_connections_forever()

    def read_csv(self, file_name):
        # Read csv at file_name and add students and averages to server instance
        with open(file_name, "r") as f:
            csv_reader = csv.reader(f, delimiter=",")
            
            headers = next(csv_reader, None)
            assignments = headers[4:]

            print("Data read from CSV file: ")
            print(headers)

            if headers == None:
                raise(Exception("No data in csv file."))
            

            for row in csv_reader:
                print(row)
                # For each row, create a student object and add it to the serve
                grades = row[4:]
                if row[0] != "Averages":
                    # Build grades dictionary
                    grades_dict = {}
                    for assignment, grade in zip(assignments, grades):
                        grades_dict[assignment] = grade
                    # Create student
                    if self.students.get(row[0]) != None:
                        print(f"Replacing student with id {row[0]}.")
                    self.students[row[0]] = Student(row[0], row[1], row[2], row[3], grades_dict)
                else:
                    for assignment, average in zip(assignments, grades):
                        if self.averages.get(assignment) != None:
                            print(f"Replacing average for assignment {assignment}.") 
                        self.averages[assignment] = average

    def socket_setup(self):
        # Init socket and start listening for commands
        try:
            # Create IPv4, TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Bind socket to specified port and address
            self.socket.bind(self.address)
            # Start listening for connections
            self.socket.listen(Server.MAX_CONNECTION_BACKLOG)
            print("-" * 72)
            print(f"Listening for connections on port {self.address[1]}...")
        except Exception as e:
            # Handle any exceptions by printing exception and exiting program
            print(e)
            sys.exit(1)

    def handle_connections_forever(self):
        try:
            while True:
                # Block waiting for incoming connection, then any connections to connection handler function
                self.handle_connection(self.socket.accept())
        except Exception as e:
            print(e)
        except KeyboardInterrupt:
            print("Manually interupted while handling connections indefinitely. Server shutting down.")
        finally:
            # Clean up and end program
            self.socket.close()
            sys.exit(1)
        
    def handle_connection(self, client):
        # Recieve command and return required information
        conn, address_port = client
        print("-" * 72)
        print(f"Connection received from {address_port}")

        while True:
            try:
                recvd_bytes = conn.recv(Server.RECV_BUFFER_SIZE)
                # Handle closed connections
                if len(recvd_bytes) == 0:
                    print(f"Closing client connection from: {address_port}...")
                    conn.close()
                    break
                #Convert to string
                try:
                    recvd_string = recvd_bytes.decode()
                except Exception as e:
                    # Can't decode hash => Auth request
                    recvd_string = recvd_bytes

                # Pass to command handler
                response = self.handle_command(recvd_string)
                
                # Send response
                if response != None:
                    sent_bytes = conn.sendall(response.encode(Server.MSG_ENCODING))
                else:
                    # Invalid command, send message to client
                    sent_bytes = conn.sendall("Invalid command. Please try again.".encode(Server.MSG_ENCODING))

            except KeyboardInterrupt:
                print()
                print(f"Closing client connection from: {address_port}...")
                conn.close()
                break
            except Exception as e:
                print(f"Error during connection: {e}")
        
    def handle_command(self, cmd_string):
        try:
            if cmd_string.upper() == Server.GET_MIDTERM_AVG_CMD:
                print(f"Received {Server.GET_MIDTERM_AVG_CMD} command from client")
                return self.averages["Midterm"]
            elif cmd_string.upper() == Server.GET_LAB_1_AVG_CMD:
                print(f"Received {Server.GET_LAB_1_AVG_CMD} command from client")
                return self.averages["Lab 1"]
            elif cmd_string.upper() == Server.GET_LAB_2_AVG_CMD:
                print(f"Received {Server.GET_LAB_2_AVG_CMD} command from client")
                return self.averages["Lab 2"]
            elif cmd_string.upper() == Server.GET_LAB_3_AVG_CMD:
                print(f"Received {Server.GET_LAB_3_AVG_CMD} command from client")
                return self.averages["Lab 3"]
            elif cmd_string.upper() == Server.GET_LAB_4_AVG_CMD:
                print(f"Received {Server.GET_LAB_4_AVG_CMD} command from client")
                return self.averages["Lab 4"]
            else:
                print(f"Received ID/password hash {cmd_string} from client.")
                try:
                    student_id = self.handle_auth(cmd_string)
                    if student_id != None:
                        return json.dumps(self.students[student_id].grades)
                    else:
                        return "Invalid student ID or password. Please try again."
                except AuthError as e:
                    print(e.message)
                    raise(e)
        except Exception as e:
            print(f'Exception handling command "{cmd_string}": {e}')
            return "Server error while handling command."

    def handle_auth(self, hash):
        try:
            # Return student corresponding to hash provided, or None if no student found
            for student in self.students.values():
                if student.get_password_hash() == hash:
                    print("Correct password, record found.")
                    return student.id
            print("Password failure.")
            return None
        except Exception as e:
            raise(AuthError("An error occured while authenticating user."))

class Student:
    def __init__(self, id, password, lastname, firstname, grades):
        self.id = id
        self.lastname = lastname
        self.firstname = firstname
        self.grades = grades
        self.password_hash = _get_hash(id, password)

    def get_password_hash(self):
        return self.password_hash

class Error(Exception):
    pass

class AuthError(Error):
    def __init__(self, message):
        self.message = message

# Util functions

def _get_hash(id, password):
        h = hashlib.sha256() # Create sha256 hash object
        # Update object with id and password
        h.update(id.encode("utf-8")) 
        h.update(password.encode("utf-8"))
        # return the hash
        return h.digest()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Command line argument 'runclient' or 'runserver' is required.")
    elif len(sys.argv) == 2:
        if sys.argv[1].lower() == "runclient":
            client = Client()
        elif sys.argv[1].lower() == "runserver":
            server = Server() 
        else:
            print("Invalid argument. Command line argument 'runclient' or 'runserver' is required.")
    else:
        # Use cli args instead of defauls
        print("Too many command line arguments. 'runclient' or 'runserver' only is required.")
