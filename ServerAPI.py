import socket
import json

class ServerAPI:
    def __init__(self, server_address, server_port):
        self.SERVER_ADDRESS = server_address
        self.SERVER_PORT = server_port

        self.server_info = (self.SERVER_ADDRESS, self.SERVER_PORT)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_info)

    async def receive_command_from_server(self):
        data = await self.client_socket.recv(1024)
        data = json.loads(data) 
        return data["command"]


    def send_confirmation_to_server(self, message):
        if message == "I_AM_READY" or message == "DRIVE_OK" or message == "TURN_OK":
            pass
        else:
            message = "INVALID_CONFIRMATION"
            
        self.client_socket.send(message)