import threading

from ServerAPI import ServerAPI
from ClientController import ClientController

server_api = ServerAPI()
client_controller = ClientController()

def logic_loop():
    while True:
        command = server_api.receive_command_from_server()
        
        if command == "TURN_RIGHT" or command == "TURN_TWICE_RIGHT" or command == "TURN_LEFT":
            client_controller.turn(where=command)
            server_api.send_confirmation_to_server(message="TURN_OK")

        elif command == "DRIVE_FORWARD":
            client_controller.drive_forward()
            server_api.send_confirmation_to_server(message="DRIVE_OK")

        elif command == "SHUTDOWN":
            break

def main():
    logic_loop()

if __name__ == "__main__":
    main()