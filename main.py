from ServerAPI import ServerAPI
from ClientController import ClientController

server_api = ServerAPI(server_address="192.168.53.87", server_port=1025)
client_controller = ClientController()

def logic_loop():
    print("Before while")
    while True:
        print("Waiting for a message from the server.")
        command = server_api.receive_command_from_server()
        print("Received a command from the server: ", command)
        
        if command == "ARE_YOU_READY":
            print("Is ready.")
            server_api.send_confirmation_to_server(message="I_AM_READY")

        elif command == "TURN_RIGHT" or command == "TURN_TWICE_RIGHT" or command == "TURN_LEFT":
            client_controller.turn(where=command)
            server_api.send_confirmation_to_server(message="TURN_OK")

        elif command == "DRIVE_FORWARD":
            client_controller.start_detecting_nodes()
            client_controller.follow_line()
            server_api.send_confirmation_to_server(message="DRIVE_OK")

        elif command == "SHUTDOWN":
            break

        else:
            pass

def main():
    logic_loop()

if __name__ == "__main__":
    main()