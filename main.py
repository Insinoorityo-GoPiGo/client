import threading
import asyncio

from ServerAPI import ServerAPI
from ClientController import ClientController

loop = asyncio.get_event_loop()

server_api = ServerAPI(server_address="127.0.0.1", server_port=1025)
client_controller = ClientController()

async def logic_loop():
    print("Before while")
    while True:
        print("Waiting for a message from the server.")
        command = await server_api.receive_command_from_server()
        print("Received a command from the server: ", command)
        
        if command == "ARE_YOU_READY":
            print("Is ready.")
            server_api.send_confirmation_to_server(message="I_AM_READY")
            pass

        elif command == "TURN_RIGHT" or command == "TURN_TWICE_RIGHT" or command == "TURN_LEFT":
            client_controller.turn(where=command)
            server_api.send_confirmation_to_server(message="TURN_OK")

        elif command == "DRIVE_FORWARD":
            client_controller.drive_forward()
            client_controller.next_node_reached()
            server_api.send_confirmation_to_server(message="DRIVE_OK")

        elif command == "SHUTDOWN":
            break

async def run():
    await logic_loop()

def main():
    loop.run_until_complete(future=run())

if __name__ == "__main__":
    main()