import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import client
import os
import time

files_to_display = []

def add_info_to_display(hostname, last_updated, size):
    per_client = {
        "hostname" : hostname,
        "last_updated" : last_updated,
        "size" : size
    }

    files_to_display.append(per_client)


class MyDialog:
    def __init__(self, parent):
        self.parent = parent
        self.wait_window = None

    def create_dialog(self, message):
        self.wait_window = tk.Toplevel(self.parent)
        self.wait_window.title("Modal Dialog")

        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        center_x = int((screen_width - 300) / 2)  # 300 is the window width
        center_y = int((screen_height - 200) / 2)  # 200 is the window height

        self.wait_window.geometry(f"200x60+{center_x}+{center_y}")
        self.wait_window.overrideredirect(True)

        label = tk.Label(self.wait_window, text=message)
        label.pack(padx=20, pady=20)

        self.wait_window.grab_set()  # Make the wait window modal

        while not client.finish:
            self.parent.update()  # Update the GUI to avoid freezing
            time.sleep(0.05)  # Wait for a short duration before re-checking the flag

        self.wait_window.destroy()  # Destroy the wait window when the task is done

            
class FileSharingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Peer-to-Peer File Sharing App")
        
        self.filename = ""
        
        self.wait_window = MyDialog(self.root)

        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=20, pady=20)
        
        # main menu init
        self.publish_button = tk.Button(self.frame, text="Publish", command=self.publish_file, width=10, height=2)
        self.publish_button.grid(row=0, column=0, padx=20, pady=20)

        self.fetch_button = tk.Button(self.frame, text="Fetch", command=self.fetch_file, width=10, height=2)
        self.fetch_button.grid(row=0,column=1, padx=20, pady=20)

        # publish init
        self.filename_label = tk.Label(self.frame, text="Filename:")
        self.filename_entry = tk.Entry(self.frame, width=40)

        self.file_path_label = tk.Label(self.frame, text="File Path:")
        self.file_path_entry = tk.Entry(self.frame, width=40)
        self.browse_button = tk.Button(self.frame, text="Browse", command=self.browse_file_path)

        self.submit_button = tk.Button(self.frame, text="Submit",command=self.process_publish, width=10, height=2)
        self.back_button = tk.Button(self.frame, text="Back", command=self.back_to_main_menu, width=10, height=2)


        # fetch init
        self.search_label = tk.Label(self.frame, text="Search:")

        self.search_entry = tk.Entry(self.frame, width=30)

        self.search_entry.bind("<Return>", self.process_fetch_request)  # Bind <Return> key press to search_files function

        self.tree = ttk.Treeview(self.frame, columns=("Hostname", "Last updated", "Size"), show="headings")
        # Align the all columns to the right
        self.tree.column("Hostname",width=150, anchor="center")  
        self.tree.column("Last updated",width=150, anchor="center")
        self.tree.column("Size",width=150, anchor="center") 

        self.tree.heading("Hostname", text="Hostname")
        self.tree.heading("Last updated", text="Last updated")
        self.tree.heading("Size", text="Size(Bytes)")

        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=self.scrollbar.set)

        self.tree.bind('<Double-1>', self.on_select)

        self.status_label = tk.Label(self.frame, text="", fg="red")


        # Disable resizing
        # self.root.resizable(False, False)

        self.root.mainloop()

            
    # Methods part
    def browse_file_path(self):
        file_path = filedialog.askopenfilename()
        self.file_path_entry.delete(0, tk.END)
        self.file_path_entry.insert(0, file_path)

    def fetch_file(self):
        # hide main menu
        self.fetch_button.grid_forget()
        self.publish_button.grid_forget()
        
        self.search_label.grid(row=0, column=0, padx=5, pady=5)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
        self.scrollbar.grid(row=1, column=3, sticky='ns')
        
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        self.back_button.grid(row=2, column=2, sticky='e')


    def back_to_main_menu(self):
        # Hide elements related to publishing or fetching files
        # Replace these lines with grid_forget for elements used in publish_file or fetch_file
        self.file_path_label.grid_forget()
        self.file_path_entry.grid_forget()
        self.browse_button.grid_forget()
        self.filename_label.grid_forget()
        self.filename_entry.grid_forget()
        self.submit_button.grid_forget()
        self.back_button.grid_forget()
        self.search_label.grid_forget()
        self.search_entry.grid_forget()
        self.tree.grid_forget()
        self.status_label.grid_forget()
        self.scrollbar.grid_forget()

        # Show main menu buttons
        self.publish_button.grid(row=0, column=0, padx=20, pady=20)
        self.fetch_button.grid(row=0,column=1, padx=20, pady=20)

    def publish_file(self):
        #hide main menu
        self.fetch_button.grid_forget()
        self.publish_button.grid_forget()
        
        self.file_path_label.grid(row=0, column=0, sticky="w")
        self.file_path_entry.grid(row=0, column=1, padx=10, pady=5)
        self.browse_button.grid(row=0, column=2, padx=5)

        self.filename_label.grid(row=1, column=0, sticky="w", pady=5)
        self.filename_entry.grid(row=1, column=1)

        self.submit_button.grid(row=2, column=1, pady=10, sticky="e")  # Use columnspan=2 for two columns
        self.back_button.grid(row=2, column=2, pady=10)  # Use column=2 for the third column

    # publish methods
    def process_publish(self):
        filepath = self.file_path_entry.get()
        filename = self.filename_entry.get()
        if filepath and filename:
            publish_file_to_server(filepath, filename)
        else:
            tk.messagebox.showwarning("Warning", "Please type in required information")

        
    # fetch methods
    def process_fetch_request(self, event):
        filename = self.search_entry.get()
        # clear the previous files_to_display buffer
        files_to_display.clear()
        local_repo_path = client.get_local_repository_path()
        file_path = os.path.join(local_repo_path, filename)  # Construct full file path
        # check file exists or not, if not send out the message
        if os.path.isfile(file_path) == True:
            self.status_label.config(text="File already exists in local repository", fg="red")
        else:
            self.status_label.config(text="")   
            cmd = "FETCH"
            msg = filename
            data = f"{cmd}@{msg}"
            
            
            # reset flag before open wait window
            client.finish = False
            client.client.send(data.encode(client.FORMAT))
            # open wait window
            self.wait_window.create_dialog("Requesting file to the server...")
            print(f"{filename} has been requested to server.")
            self.process_fetch_reply(client.msg_to_ui)
            
        
    def update_treeview(self, files):
        self.tree.delete(*self.tree.get_children())
        for file in files:
            self.tree.insert("", tk.END, values=(file['hostname'], file['last_updated'], file['size']))        
            
    def process_fetch_reply(self, msg):
        if msg == "N/A":
            # clear the tree
            self.tree.delete(*self.tree.get_children())
            # notify the user if the file is not available on server
            self.status_label.config(text="File not found", fg="red")
            return
            
        try:
            lines = msg.splitlines()
            filename = lines[0]
        except (IndexError, ValueError) as e:
            print(f"Error occurred: {e}")
            return
        except Exception as ex:
            print(f"Unexpected error occurred: {ex}")
            return
        
        # save filename to send back request
        self.filename = filename
        # clear the list before displaying
        files_to_display.clear()
        for line in lines[1:]:
            hostname, last_updated, size = line.split("|")
            add_info_to_display(hostname, last_updated, size)
            
        # start to display the list on treeview
        self.update_treeview(files_to_display)
    
        # clearing the notification
        self.status_label.config(text="")



    def on_select(self, event):
        item_id = self.tree.identify_row(event.y)  # Get the item ID at the clicked position

        if item_id:
            # Clicked on an item
            item = self.tree.item(item_id)["values"]
            hostname = item[0]
            self.request_to_server(self.filename, hostname)


    def request_to_server(self, filename, hostname):
        cmd = "SELECT_PEER"
        data = f"{cmd}@{filename}|{hostname}"
        
        # reset flag before open wait window
        client.finish = False
        
        client.client.send(data.encode(client.FORMAT))
        self.wait_window.create_dialog(f"Getting file from {hostname}...")
        if client.msg_to_ui == "N/A":
            tk.messagebox.showerror("Error", "File has been moved or deleted")
            self.status_label.config(text="")
        else:
            self.status_label.config(text="Downloaded file successfully", fg="green")
        
        
def publish_file_to_server(filepath, filename):
    if os.path.isfile(filepath) == True:
        #publish file in local file's system to local_repository
        client.publish_to_local_repository(filepath, filename)

        #make the updated messsage and send to server
        cmd = "PUBLISH"
        local_repository_path = client.get_local_repository_path()
        file_path = local_repository_path + filename
        last_modified = client.time.ctime(os.path.getmtime(file_path))
        file_size = os.path.getsize(file_path)
        msg = filename + "|" + last_modified + "|" + str(file_size) 

        # send updated messsage to server
        data = f"{cmd}@{msg}"
        client.client.send(data.encode(client.FORMAT))
    else:
        tk.messagebox.showerror("Error", "File doesn't exist")



app = FileSharingApp();