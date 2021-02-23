"""
server.py

A server to fulfill the requirements detailed in pdf lab description

NOTE: All cli args are required, or none
i.e. "python server.py" OR "python server.py ip port filename"
"""
import socket
import sys
import csv

CSV_FILE_NAME = "course_grades_2021.csv"

class Server:
    # Command string consts
    GET_MIDTERM_AVG_CMD = "GMA"
    GET_LAB_1_AVG_CMD = "GLA1"
    GET_LAB_2_AVG_CMD = "GLA2"
    GET_LAB_3_AVG_CMD = "GLA3"
    GET_LAB_4_AVG_CMD = "GLA4"

    MAX_CONNECTION_BACKLOG = 10

    def __init__(self, ip_address='localhost', port=1234, file_name=CSV_FILE_NAME):
        # Add students
        self.students = {}
        self.averages = {}
        self.read_csv(file_name)

        # Socket init
        self.address = (ip_address, port)
        self.socket_setup()

    def read_csv(self, file_name):
        # Read csv at file_name and add students and averages to server instance
        with open(file_name, "r") as f:
            csv_reader = csv.reader(f, delimiter=",")

            headers = next(csv_reader, None)
            assignments = headers[4:]

            if headers == None:
                raise(Exception("No data in csv file."))

            for row in csv_reader:
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
            print(f"Listening on port {self.address[1]}...")
        except Exception as e:
            # Handle any exceptions by printing exception and exiting program
            print(e)
            sys.exit(1)

        
    
    def handle_command(self, cmd):
        # Recieve command and return required information
        pass

class Student:
    def __init__(self, id, password, lastname, firstname, grades):
        self.id = id
        self.password = password
        self.lastname = lastname
        self.firstname = firstname
        self.grades = grades

HELPTEXT = "\nThis command can be run to create an IPv4 TCP server. The IP address, port number and\
csv file location can be provided as command line arguments, in that order.\n"

if __name__ == "__main__":
    if len(sys.argv) == 2 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print(HELPTEXT)
        print("NOTE: All command line args are required, OR none.")
        print('i.e. Use "python server.py" for defaults OR "python server.py ip port filename".')
        sys.exit(0)
    if len(sys.argv) == 1:
        # If no cli args are provided
        server = Server()
    else:
        # Use cli args instead of defauls
        try:
            server = Server(ip_address=sys.argv[1], port=int(sys.argv[2]), file_name=sys.argv[3])
        except Exception:
            print("\nAn error occured setting up the server.\n")
            print("NOTE: All command line args are required, OR none.")
            print('i.e. Use "python server.py" for defaults OR "python server.py ip port filename".')