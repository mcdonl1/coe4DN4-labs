"""
server.py

A server to fulfill the requirements detailed in pdf lab description
"""
import socket
import sys
import csv

class Server:
    CSV_FILE_NAME = "course_grades_2021.csv"

    # Command string consts
    GET_MIDTERM_AVG_CMD = "GMA"
    GET_LAB_1_AVG_CMD = "GLA1"
    GET_LAB_2_AVG_CMD = "GLA2"
    GET_LAB_3_AVG_CMD = "GLA3"
    GET_LAB_4_AVG_CMD = "GLA4"

    def __init__(self, ip_address='localhost', port=1234):
        self.students = {}
        self.averages = {}
        self.read_csv(Server.CSV_FILE_NAME)
        print(self.students)

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

if __name__ == "__main__":
    for i, arg in enumerate(sys.argv):
        # Get args from cli
        print(f"Arg number: {i}, Arg: {arg}")

    # Set up and run server using cli args
    server = Server()