import socket
import threading
import os
import re
import traceback
import time
import asyncio
from dotenv import load_dotenv
import base64
from watcher_server import FSHandler
load_dotenv()
class SocketServer:

    max_clients = 10
    active_connections = []
    threads = []
    server_files = os.getenv("SERVER_ROUTE")
    
    def __init__(self, port, host):
        self.port = port
        self.host = host

    def configurate_socket(self):
        self.server_descriptor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_descriptor.bind((self.host, self.port))

    def make_listen(self):
        self.server_descriptor.listen(self.max_clients)

    def accept_clients(self):
        self.observer = FSHandler(self.server_descriptor, self.host, self.port, self.active_connections)
        threading.Thread(target=self.observer.start_observer).start()
        while True:
            try:
                client_socket, (client_host, client_port) = self.server_descriptor.accept()
                print(str(client_host) + ":" + str(client_port))
                self.active_connections.append(client_socket)
                self.observer.active_connections = self.active_connections
                threading.Thread(target = self.handle_connections, args=(self.active_connections[-1], ) ).start()
            except:
                break
        self.server_descriptor.close()

    def decode_base64(self, data, altchars=b'+/'):
        data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data)  # normalize
        missing_padding = len(data) % 4
        if missing_padding:
            data += b'='* (4 - missing_padding)
        print(len(data))
        return base64.b64decode(data, altchars)

    def handle_connections(self, connection):
        actions_maded = []
        valid_options = ['created','modified','moved','deleted']
        filename = ''
        info = ''
        while True:
            try:
                client_message =  connection.recv(1024)
                try:
                    client_message = client_message.decode("latin1")
                    option = client_message.split(',')[0]
                    if option in valid_options:
                        actions_maded.append(option)
                except Exception:
                    client_message = str(client_message.decode("latin1"))
                    option = 'non'
                print(client_message)
                split_message = client_message.split("__##")                
                if len(split_message) == 1:
                    filename, info = self.make_actions(option, split_message[0], actions_maded, filename, info, connection)
                elif len(split_message[0]) == 0:
                    filename, info = self.make_actions(option, "Finish", actions_maded, filename, info, connection)
                    filename, info = self.make_actions(option, split_message[2], actions_maded, filename, info, connection)
                elif len(split_message[2]) == 0:
                    filename, info = self.make_actions(option, split_message[0], actions_maded, filename, info, connection)
                    filename, info = self.make_actions(option, "Finish", actions_maded, filename, info, connection)    
                elif len(split_message[0]) == 0 and len(split_message[2]) == 0:
                    filename, info = self.make_actions(option, "Finish", actions_maded, filename, info, connection)                             
            except Exception:
                print("Connection ended")
                break
        connection.close()

    def create(self, client_message, option):
        filename =  client_message.split(',')[1].split("\\")[-1]
        if os.path.isfile(self.server_files + filename) == False:
            file = open(self.server_files+filename, "wb")
            file.close()
        print(option + " >>  " + filename)
        return filename

    def moved(self, client_message, option):
        src = client_message.split(',')[-2].split("\\")[-1]
        dest = client_message.split(',')[-1].split("\\")[-1]
        if os.path.isfile(self.server_files+src) == True:
            os.rename(self.server_files+src, self.server_files+dest)
        else:
            file = open(self.server_files+dest, "wb")
            file.close()
        print(option + " >>  " + src + " to " + dest)
        return src , dest

    def delete(self, client_message, option):
        filename = client_message.split(',')[-1].split("\\")[-1]
        if os.path.isfile(self.server_files+filename) == True:
            os.remove(self.server_files+filename)
        print(option + " >>  " + filename)
        return filename

    def increase_info(self, info, client_message, connection, filename):
        if client_message == 'Finish':
            if os.path.isfile(self.server_files+ filename) == True:
                file = open(self.server_files + filename, 'wb')
                file.write(info.encode("latin1"))
                file.close()
            info = ''
        else :
            info += client_message
        return info

    def return_options(self, option, actions_maded, filename, info, dest):
        if option == 'modified' or actions_maded[-1] == 'modified':
            return filename, info
        elif option == 'moved':
            return dest, info
        else:
             return "made", info

    def make_actions(self, option, client_message, actions_maded, filename, info, connection):
        dest = ''
        if  option == 'created':
            filename = self.create(client_message, option)
        elif  option == 'moved':
            src , dest = self.moved(client_message, option)
        elif  option == 'deleted':
            filename = self.delete(client_message, option)
        elif option == 'modified':
            filename = client_message.split(',')[-1].split("\\")[-1]
            print(option + " >>  " + filename)
        else:
            info = self.increase_info(info, client_message, connection, filename)
        return self.return_options(option, actions_maded, filename, info,dest)

    def notify_clients(self, current_connection, option, src, dest, info, msg):
        if option == 'created':
            msg = 'action,' + option + "," +src
        elif option == 'modified':
            msg = 'action,' + option + "," + src + "," + info
        elif option == 'deleted':
            msg = 'action,' + option + "," + src
        elif option == 'moved':
            msg = 'action,' + option + "," + src + "," + dest
        for connection in self.active_connections:
            if connection != current_connection:
                connection.send(msg.encode("latin1"))




            


