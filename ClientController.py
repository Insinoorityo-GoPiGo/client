import time
import easygopigo3 as easy
from di_sensors.easy_line_follower import EasyLineFollower
from mfrc522 import SimpleMFRC522

class ClientController:
    def __init__(self):
        self.gpg = easy.EasyGoPiGo3()
        self.line_follower = EasyLineFollower()
        self.rfid_reader = SimpleMFRC522()

        self.base_speed = 100
        self.turn_speed = 140

    def detect_rfid_node(self):
        try:
            node_id, _ = self.rfid_reader.read()  # Read the tag
            
            # Check if this node was already read
            if hasattr(self, "last_rfid_id") and node_id == self.last_rfid_id:
                #print(f"Duplicate RFID detected: {node_id}, ignoring...")
                return False  # Ignore duplicate reads
            
            # Store the last detected RFID tag
            self.last_rfid_id = node_id
            #print(f"RFID Tag detected: {node_id}")
            return True
    
        except Exception as e:
            #print(f"RFID error: {e}")
            return False

    def follow_line(self):
        try: 
            while True:

                self.line_follower = EasyLineFollower()
                time.sleep(0.2)
                position = self.line_follower.read_position()

                if position == "center":
                    left_speed = self.base_speed
                    right_speed = self.base_speed
                elif position == "left":
                    left_speed = self.base_speed - (self.turn_speed // 2)
                    right_speed = self.base_speed + (self.turn_speed // 2)
                elif position == "right":
                    left_speed = self.base_speed + (self.turn_speed // 2)
                    right_speed = self.base_speed - (self.turn_speed // 2)
                elif position == "black":
                    left_speed = self.base_speed
                    right_speed = self.base_speed
                elif position == "white":
                    left_speed = -50
                    right_speed = -50
                else:
                    print(f"Unexpected position reading: {position}, stopping bot...")
                    left_speed = 0
                    right_speed = 0

                self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, left_speed)
                self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, right_speed)

                # Debug Output
                print(f"Pos: {position}, L-Speed: {left_speed}, R-Speed: {right_speed}")

                detected = self.detect_rfid_node()

                if detected:  
                    print("Stopping at node!")
                    self.gpg.stop()
                    time.sleep(0.5)
                    break
                

        except KeyboardInterrupt:
            self.gpg.stop()
            exit(0)

    def turn(self, where):
        turn = None

        if where == "TURN_RIGHT":
            turn = 95
        elif where == "TURN_TWICE_RIGHT":
            turn = 190
        elif where == "TURN_LEFT":
            turn = -95

        self.gpg.stop()
        time.sleep(0.5)
        self.gpg.turn_degrees(turn)
        time.sleep(0.5)

