import time
import socket   
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler 
import traceback

class FSHandler:
    path = "C:\\Users\\josue.ruiz\\Documents\\ESCOM\\Redes\\Prácticas\\Practica 3\\client_files\\" 
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    def __init__(self, socket, host, port):
        self.socket = socket
        self.host = host
        self.port = port
        self.my_event_handler = PatternMatchingEventHandler(self.patterns, self.ignore_patterns, self.ignore_directories, self.case_sensitive)
        self.configure()
        self.create_observer()

    def configure(self):
        self.my_event_handler.on_created = self.on_created
        self.my_event_handler.on_deleted = self.on_deleted
        self.my_event_handler.on_modified = self.on_modified
        self.my_event_handler.on_moved = self.on_moved

    def create_observer(self):
        try:
            go_recursively = True
            self.my_observer = Observer()
            self.my_observer.schedule(self.my_event_handler, self.path, recursive=go_recursively)
        except:
            print("Error")

    def start_observer(self):
        self.my_observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.my_observer.stop()
            self.my_observer.join()

    def on_created(self, event):
        try:
            client_message = f"created, {event.src_path}"
            self.socket.send(bytes(client_message, 'utf-8'))
        except:
            print("Error de permisos")

    def on_deleted(self, event):
        client_message = f"deleted, {event.src_path}"
        self.socket.send(bytes(client_message, 'utf-8'))

    def on_modified(self, event):
        client_message = f"modified, {event.src_path}"
        self.socket.send(bytes(client_message, 'utf-8'))
        time.sleep(2)
        while True:
            file = open(event.src_path, 'rb')
            content = file.read(1024)
            while content:
                self.socket.send(content)
                content = file.read(1024)
                time.sleep(2)
                # self.socket.recv(1024)
            break
        try:
            self.socket.send(bytes("Finish", "utf-8"))
            # self.socket.recv(1024)
        except Exception:
            self.socket.send(bytes("Finish", "utf-8"))
            traceback.print_exc()
        file.close()
        
    def on_moved(self, event):
        client_message = f"moved, {event.src_path}, {event.dest_path}"
        self.socket.send(bytes(client_message, 'utf-8'))
