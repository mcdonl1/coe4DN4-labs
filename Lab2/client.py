"""
client.py

A socket API client to fulfill the requirements detailed in the lab description pdf file.
"""
import socket
import sys
import getpass
import hashlib

class Client:

    def __init__(self):
        pass


if __name__ == "__main__":
    for i, arg in enumerate(sys.argv):
        # Get args from cli
        print(f"Arg number: {i}, Arg: {arg}")
    # Set up and run client using cli args
    client = Client()
