import socket
import threading

# IP = socket.gethostbyname(socket.gethostname())
IP = socket.gethostbyname(socket.gethostname())
PORT = 60000
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"

file_info = {}
client_sockets = {}

# set up threading flag to wait for other task to be done before getting more user input
event_flag = threading.Event()

# add file information to the data base
def add_file_info(filename, hostname, last_modified, file_size):
    client_info = {
        "hostname" : hostname,
        "last_modified" : last_modified,
        "file_size" : file_size
    }
    
    if filename not in file_info:
        file_info[filename] = [client_info]
    else:
         # Check if the hostname exists for the given file
        found = False
        for info in file_info[filename]:
            if info['hostname'] == hostname:
                # Update existing information for the same hostname
                info.update(client_info)
                found = True
                break

        # If the hostname doesn't exist, add the new information
        if not found:
            file_info[filename].append(client_info)
    
    
def add_files_from_a_client(client_file_info, hostname) :
    client_data = []
    for line in client_file_info.strip().split('\n'):
        filename, last_modified, file_size = line.split('|')
        # update or add more file from new information
        add_file_info(filename, hostname, last_modified, file_size)
        per_file_info = [filename, last_modified, file_size]
        client_data.append(per_file_info)

    return client_data

def remove_client_from_a_file(filename, hostname_to_remove):
    if filename in file_info:
        clients = file_info[filename]
        # keep other clients that are not named hostname
        updated_clients = [client for client in clients if client['hostname'] != hostname_to_remove]
        file_info[filename] = updated_clients
        
        # delete files that have no information
        if not updated_clients:
            del file_info[filename]

def get_file_info(filename):
    if filename in file_info:
        return file_info.get(filename, [])
    else:
        return None
    
def remove_hostname_from_file_info(hostname):
    for filename, clients_list in list(file_info.items()):
        # keep those clients that are not named hostname
        clients_to_keep = [client for client in clients_list if client['hostname'] != hostname]
        clients_list[:] = clients_to_keep  # Update the clients_list in-place
        
        # delete files that have no information
        if not clients_to_keep:
            del file_info[filename]
     
    if hostname in client_sockets:      
        del client_sockets[hostname]
            
# add client socket and upload_port for getting connection when needed
def add_client_info(client_socket, hostname, upload_port):
    client_sockets[hostname] = {
        "socket": client_socket,
        "upload_port": upload_port
    }

def get_client_info(hostname):
    if hostname in client_sockets:
        return client_sockets[hostname]
    else:
        return None

def process_discover_list(client_file_info, hostname, event_flag):
    client_data = add_files_from_a_client(client_file_info, hostname)
    
    # Determine maximum width for each column
    max_widths = [max(len(row[i]) for row in client_data) for i in range(len(client_data[0]))]

    # Add extra padding to the maximum widths for spacing between columns
    max_widths = [width + 2 for width in max_widths]

    # Printing header with dynamic alignment
    print(f"{'Filename':<{max_widths[0]}}{'Last Modified':<{max_widths[1]}}{'File Size(bytes)':<{max_widths[2]}}")

    # Printing data with dynamic alignment
    for row in client_data:
        print(f"{row[0]:<{max_widths[0]}}{row[1]:<{max_widths[1]}}{row[2]:<{max_widths[2]}}")
        
    event_flag.set()
        

def handle_publish(msg, hostname):
    filename, last_modified, file_size = msg.split("|")

    add_file_info(filename, hostname, last_modified, file_size)
    

def check_file_status(conn, requesting_client, requested_client, filename):
    client_socket = get_client_info(requested_client)
    if client_socket:
        client_socket = client_socket["socket"]
        # send check status request to requested client
        msg = f"CHECK_STATUS@{filename}|{requesting_client}"
        client_socket.send(msg.encode(FORMAT))        
    else:
        remove_hostname_from_file_info(requested_client)
        msg = f"REPLY_PEER@N/A"
        conn.send(msg.encode(FORMAT))


def handle_fetch(filename, conn, requesting_client):
    per_file_info = get_file_info(filename)

    if per_file_info:
        # Filtering out the dictionaries with the requesting client
        per_file_info = [client for client in per_file_info if client['hostname'] != requesting_client]
        
        # number_of_clients = len(per_file_info)
        # list all the owners of 'filename' for the requesting client to choose
        msg = f"REPLY_FETCH@{filename}"
        
        for client in per_file_info:
            msg += f"\n{client['hostname']}|{client['last_modified']}|{client['file_size']}"
            conn.send(msg.encode(FORMAT))
    else:
        # file does not exist
        msg = f"REPLY_PEER@N/A"
        conn.send(msg.encode(FORMAT))
        

def handle_client(conn, addr, event_flag):
    conn.send(f"OK@Welcome {addr} to the File Server.".encode(FORMAT))
    
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
        except ConnectionResetError:
            # if the client close the program suddenly, safely remove them out of data base
            remove_hostname_from_file_info(addr[0])
            break
        if not data: break
        
        cmd, msg = data.split("@", 1)
        
        if cmd == "CONNECT":
            upload_port, client_file_info = msg.split("#")

            # add socket and upload_port to use when needed
            add_client_info(conn, addr[0], upload_port)

            if client_file_info:
                # also add the client's repository's files list
                add_files_from_a_client(client_file_info, addr[0])
            
        elif cmd == "PUBLISH":
            handle_publish(msg, addr[0])
            
        elif cmd == "FETCH":
            handle_fetch(msg, conn, requesting_client = addr[0])
            
        elif cmd == "REPLY_STATUS":
            filename, hostname, status, last_modified, file_size = msg.split("|")
            requesting_client = get_client_info(hostname)["socket"]
            if status == "OK":
                hostname = addr[0]
                upload_port = get_client_info(hostname)["upload_port"]
                msg = f"{filename}|{hostname}|{upload_port}"
                # update lastest status to data base when getting status from client
                add_file_info(filename, hostname, last_modified, file_size)
            else:
                msg = "N/A"
                remove_client_from_a_file(filename, addr[0])

            # send status back to requesting client
            cmd = "REPLY_PEER"
            info = f"{cmd}@{msg}"
            if requesting_client:
                requesting_client.send(info.encode(FORMAT))
            
        elif cmd == "SELECT_PEER":
            filename, requested_client = msg.split("|")

            # check file status after choosing disired client
            check_file_status(conn, addr[0], requested_client, filename)
            
        elif cmd == "REPLY_DISCOVER":
            # check if the client's local repo is empty or not
            if msg:
                process_discover_list(msg, addr[0], event_flag)
            else:
                print(f"({addr[0]})'s local repository is currently empty.")
                
            event_flag.set()
        elif cmd == "REPLY_PING":
            print(f"{addr} is currently connected")
            event_flag.set()
            
    # delete all the client's information that file_info is containing
    remove_hostname_from_file_info(addr[0])
    conn.close()
    
def get_hostname_repo(hostname, event_flag):
    client_socket = get_client_info(hostname)
    if client_socket:
        client_socket = client_socket["socket"]
        msg = f"DISCOVER@"
        client_socket.send(msg.encode(FORMAT))
    else:
        print("The client does not exist or has disconnected.")
        event_flag.set()


def live_check(hostname, event_flag):
    client_socket = get_client_info(hostname)
    if client_socket:
        client_socket  = client_socket["socket"]
        client_socket.send("PING@".encode(FORMAT))
    else:
        print("The client does not exist or has disconnected.")
        event_flag.set()


def get_user_input(event_flag):
    print("Server commands:")
    print("	discover [hostname]	discover the list of local files of the host named hostname")
    print("	ping [hostname]		live check the host named hostname\n")
    while True:
        user_input = input("Enter a command: ")
        print("")
        # check syntax
        try:
            cmd, hostname = user_input.split(" ")
        except ValueError:
            print(f"Command '{user_input}' not recognized.\n")
            continue
            
        if cmd == "discover":
            event_flag.clear()
            get_hostname_repo(hostname, event_flag)
            event_flag.wait()
        elif cmd == "ping":
            event_flag.clear()
            live_check(hostname, event_flag)
            event_flag.wait()
        else:
            print(f"Command '{user_input}' not recognized.\n")
            
        print("")


#start the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
print(f"Server begin listening on {IP}:{PORT}.\n")

# start a new thread for reading user input
cli = threading.Thread(target=get_user_input, args=(event_flag, ))
cli.start()

while True:
    conn, addr = server.accept()
    # start a new thread for new client connected
    thread = threading.Thread(target=handle_client, args=(conn, addr, event_flag))
    thread.start()

