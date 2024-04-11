import socket               # Import socket module
import time					# Import time module
import platform				# Import platform module to get our OS
import os
import shutil
import random
from _thread import *
import struct


# Returns the local repository path based on the operating system.
def get_local_repository_path():
    """

    Returns:
        str: Local repository path.
    """
    local_repository_path = os.getcwd();
    OS = platform.system()
    if OS == "Windows":  # determine local_repository path for two different system
        local_repository_path = "local_repository\\" 
    else:
        local_repository_path = "local_repository/" 

    if not os.path.exists(local_repository_path):
       os.mkdir(local_repository_path)

    return local_repository_path


# Publishes a file in client's file system to the local repository.   
def publish_to_local_repository(lname, fname):
    """

    Args:
        lname (str): Source file path.
        fname (str): Destination file name.

    Returns:
        None
    """
    file_path = get_local_repository_path() + fname
    shutil.copyfile(lname, file_path)
    print(f"Successfully copied files in {lname} to local repository named {fname}")

# Creates a dictionary-like list of files in the local repository.
def make_dict_list_of_files():
    """

    Returns:
        str: A formatted string containing file information (name, last modified timestamp, and size separated by "|").
    """
    local_repository_path = get_local_repository_path()

    dict_list_of_files = ""
    for file_name in os.listdir(local_repository_path):
        file_path = os.path.join(local_repository_path, file_name)
        last_modified = time.ctime(os.path.getmtime(file_path))
        file_size = os.path.getsize(file_path)
        file_info = file_name + "|" + last_modified + "|" + str(file_size) + "\n"
        dict_list_of_files = dict_list_of_files + file_info
    return dict_list_of_files

# Retrieves information about the local repository and peer.
def peer_information():
    """

    Returns:
        str: A formatted message containing the hostname, upload port number, and a list of files.
    """
    list_of_files = make_dict_list_of_files()
    message = f"{str(upload_port_num)}#{list_of_files}"
    return message 

# Creates a P2P request message to retrieve a specific file.
def p2p_request_message(fname, host):
    """

    Args:
        fname (str): The name of the requested file.
        host (str): The hostname of the peer.

    Returns:
        str: The formatted P2P request message.
    """
    message = "GET File: "+str(fname)+"\n"\
              "Host: "+str(host)+"\n"\
 
    return message

# Extracts the file name from a received message.
def extract_fname_from_message(received_message):
    """

    Args:
        received_message (str): The received message containing the file name.

    Returns:
        str or None: Extracted file name or None if the format is not as expected.
    """
    # Split the message by newline characters
    lines = received_message.split("\n")

    # Assuming the first line contains "GET File: file_name"
    first_line = lines[0]
    if first_line.startswith("GET File: "):
        fname = first_line[len("GET File: "):]  # Extract the file_name
        return fname.strip()  # Remove any leading/trailing spaces

    # If the message format is not as expected, handle it accordingly
    # (e.g., raise an exception or return a default value)
    return None
 

def receive_file_size(sck: socket.socket):
    # This funcion makes sure that the bytes which indicate
    # the size of the file that will be sent are received.
    # The file is packed by the client via struct.pack(),
    # a function that generates a bytes sequence that
    # represents the file size.
    fmt = "<Q"
    expected_bytes = struct.calcsize(fmt)
    received_bytes = 0
    stream = bytes()
    while received_bytes < expected_bytes:
        chunk = sck.recv(expected_bytes - received_bytes)
        stream += chunk
        received_bytes += len(chunk)
    filesize = struct.unpack(fmt, stream)[0]
    return filesize


def receive_file(sck: socket.socket, file_name):
    # First read from the socket the amount of
    # bytes that will be received from the file.
    global finish
    filesize = receive_file_size(sck)
    # Open a new file where to store the received data.
    file_path = get_local_repository_path() + file_name

    with open(file_path, "wb") as f:
        received_bytes = 0
        # Receive the file data in 1024-bytes chunks
        # until reaching the total amount of bytes
        # that was informed by the client.
        while received_bytes < filesize:
            chunk = sck.recv(1024)
            if chunk:
                f.write(chunk)
                received_bytes += len(chunk)

        # close file when receive file completely
        f.close()    
            
    print("Recieve file" , file_name, "complete!\n")
    sck.close()
    finish = True


# send file to peers
def send_file(sck: socket.socket, file_name):
    # Get the size of the outgoing file.
    file_path = get_local_repository_path() + file_name
    filesize = os.path.getsize(file_path)
    # First inform the server the amount of
    # bytes that will be sent.
    sck.sendall(struct.pack("<Q", filesize))
    # Send the file in 1024-bytes chunks.
    with open(file_path, "rb") as f:        
        while read_bytes := f.read(1024):
            sck.sendall(read_bytes)

        # close file when receive file completely
        f.close()
    print("Send file" , file_name, "complete!\n")
    sck.close()


def p2s_listen_thread():
    """
    Listens for incoming messages from the server and handles different commands.

    Returns:
        None
    """
    # global declaration msg to communicate with UI
    global msg_to_ui
    global finish
    
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        
        try:
            cmd, msg = data.split("@")
        except ValueError:
            continue

        if cmd == "OK":
            print(msg)
        elif cmd == "CHECK_STATUS":
            #Reply to server file_name in msg is exist or not
            #msg = fname|host
            #msg_reply = fname|host|status|last-modified|size
            cmd = "REPLY_STATUS"
            file_name, _ = msg.split("|")
            file_path = get_local_repository_path() + file_name
            #check file_name in repository
            if os.path.isfile(file_path) == True:
                last_modified = time.ctime(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                msg_reply = f"{msg}|OK|{last_modified}|{file_size}"
            else: 
                msg_reply = msg + "|N/A||"
            
            data = f"{cmd}@{msg_reply}"
            client.send(data.encode(FORMAT))
        elif cmd == "REPLY_FETCH":
            # assign global communicate variable to message
            msg_to_ui = msg    
            
            # set flag to continue processing message
            finish = True
        #Server reply with peer's infomation
        elif cmd == "REPLY_PEER":
            #Connect to peer for tranfer file 
         
            #msg = fname|peer_hostname|peer_port  

            #if no peeer have fname
            #msg = "N/A"
            
            if msg != "N/A" :
                fname, peer_hostname, peer_port = msg.split("|")
                download_socket=socket.socket()          # Create a socket object to recieve file
                download_socket.connect((peer_hostname, int(peer_port)))
                data = p2p_request_message(fname, HOST)
                download_socket.send(data.encode(FORMAT))
                receive_file(download_socket, fname)
                msg_to_ui = "OK"
            else:
                # inform the UI to print the request's status
                msg_to_ui = msg
                # close the wait window
                finish = True
                
        #Server request to discover the list of local files 
        elif cmd == "DISCOVER":
            #Send list of file to server
            #msg = fname|date-modified|size
            cmd = "REPLY_DISCOVER"
            msg = make_dict_list_of_files()
            data = f"{cmd}@{msg}"
            client.send(data.encode(FORMAT))
        elif cmd == "PING":
            cmd = "REPLY_PING"
            msg_reply = f"{msg}|OK" 
            data = f"{cmd}@{msg_reply}"
            client.send(data.encode(FORMAT))

def handle_publish(words):
    lname, fname = words[1], words[2]
    # Check if a file exists in lname 
    if os.path.isfile(lname) == True:
        #publish file in local file's system to local_repository
        publish_to_local_repository(lname, fname)

        #make the updated messsage and send to server
        cmd = "PUBLISH"
        local_repository_path = get_local_repository_path()
        file_path = local_repository_path + fname
        last_modified = time.ctime(os.path.getmtime(file_path))
        file_size = os.path.getsize(file_path)
        msg = fname + "|" + last_modified + "|" + str(file_size) 

        # send updated messsage to server
        data = f"{cmd}@{msg}"
        client.send(data.encode(FORMAT))

        print(f"Published information of {fname} {lname}.")
    else:
        print("File doesn't exist. Can't publish to local repository")


def handle_fetch(words):
    fname = words[1]
    # Check if a file exists in local_repository
    file_path = get_local_repository_path() + fname
    if os.path.isfile(file_path) == True:
        print("File already exists in repository")
    else:   
        cmd = "FETCH"
        msg = fname
        data = f"{cmd}@{msg}"
        client.send(data.encode(FORMAT))
        print(f"{fname} has been requested to server.")

def process_command():
    """
    Recognize and process commands from the command line.

    Args:
        command (str): String of commands from the command line.

    Returns:
        str: Processing result or error message.
    """
    while True:
        if select_peer_flag ==False:
            command = input()

            # Separate words in the command
            words = command.split()

            # Handling the "publish" statement
            if words[0] == "publish":
                if len(words) != 3:
                    print("The 'publish' command requires 2 parameters: lname and fname.")
                else:
                    handle_publish(words)

            # Handling the "fecth" statement
            elif words[0] == "fetch":
                if len(words) != 2:
                    print("The 'fetch' command requires 1 parameter: fname.")
                else:
                    handle_fetch(words)
            # Handling the "logout" statement
            elif words[0] == "logout":
                print("Disconnected from the server.")
                cmd = "LOGOUT@"
                client.send(cmd.encode(FORMAT))
                client.close()
                break
            else:
                print("Invalid command. Please use the format:\n publish <lname> <fname>\n fetch <fname>\n")


def p2p_listen_thread():
    """
    Sets up a listener thread for P2P file transfer.

    Returns:
        None
    """
    upload_socket = socket.socket()
    upload_socket.bind((HOST, upload_port_num))
    upload_socket.listen(5)
    while True:
        c, addr = upload_socket.accept()
        print (f"Got connection from {addr}")
        data_p2p = c.recv(SIZE).decode(FORMAT)
        fname = extract_fname_from_message(data_p2p)# get the rfc_number
        
        print(f"Start sending {fname} to {addr}")
        start_new_thread(send_file, (c, fname))
        

# change to server IP address if you want to connect to other machine
IP = socket.gethostbyname(socket.gethostname())
PORT = 60000
HOST = socket.gethostname()
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

upload_port_num = 65000+random.randint(1, 500)  # generate a upload port randomly in 65000~65500
select_peer_flag = False
select_peer_num = 0

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

cmd = "CONNECT"
msg = peer_information()

data = f"{cmd}@{msg}"
client.send(data.encode(FORMAT))

msg_to_ui = ""
finish = False

start_new_thread(p2s_listen_thread,())
start_new_thread(p2p_listen_thread,())


