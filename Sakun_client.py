from string import ascii_letters
import os
import time
import easygopigo3 as easy
from di_sensors.easy_line_follower import EasyLineFollower
from mfrc522 import SimpleMFRC522

class ClientControl:
    def __init__(self, path, default_direction="east"):
        self.path = path
        self.gpg = easy.EasyGoPiGo3()
        self.line_follower = EasyLineFollower()
        self.rfid_reader = SimpleMFRC522()

        self.current_node_marker = 0
        self.next_node_marker = self.current_node_marker + 1

        self.current_node = self.path[self.current_node_marker]
        self.next_node = self.path[self.next_node_marker]

        self.cardinal_directions = ["north", "east", "south", "west"]
        self.gopigo_direction = default_direction


        self.base_speed = 100
        self.turn_speed = 140

    def check_next_node(self):
        current_letter = self.current_node[0]
        current_number = self.current_node[1]

        next_letter = self.next_node[0]
        next_number = self.next_node[1]

        if current_number != next_number:
            if current_number < next_number:
                return "east"
            else:
                return "west"
        else:
            if ascii_letters.index(current_letter) < ascii_letters.index(next_letter):
                return "south"
            else:
                return "north"

    def turn_gopigo(self, where_from, to_where):
        if where_from == to_where:
            return
        
        turns = {
        ("north", "east"): 95, ("north", "south"): 190, ("north", "west"): -95,
        ("east", "north"): -95, ("east", "south"): 95, ("east", "west"): 190,
        ("south", "east"): -95, ("south", "west"): 95, ("south", "north"): 190,
        ("west", "north"): 95, ("west", "east"): 190, ("west", "south"): -95
    }
        if (where_from, to_where) in turns:
            print(f"Turning from {where_from} to {to_where}")
            self.gpg.stop()  #Stop before turning
            time.sleep(0.5)
            self.gpg.turn_degrees(turns[(where_from, to_where)])
            time.sleep(0.5)  #Wait for stability
        
        self.gopigo_direction = to_where  # Update GoPiGo's direction after turning
    
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
                    self.handle_node_reached()
                    break
                

        except KeyboardInterrupt:
            self.gpg.stop()
            exit(0)

    def handle_node_reached(self):
        try:
            print(f"Reached a node at marker {self.current_node_marker}")
            #self.current_node_marker += 1

            if self.current_node_marker >= len(self.path) - 1:
                print("Destination reached!")
                self.gpg.stop()
                return
            
            self.turn_to_next_node()    
            
            self.current_node_marker += 1
            self.next_node_marker = self.current_node_marker + 1

            self.current_node = self.path[self.current_node_marker]
            if self.next_node_marker < len(self.path):
                self.next_node = self.path[self.next_node_marker]
            else:
                self.next_node = None
            
            if self.next_node is not None:
                self.follow_line()

        except KeyboardInterrupt:
            self.gpg.stop()
            exit(0)

    def turn_to_next_node(self):
        next_direction = self.check_next_node()
        if self.gopigo_direction != next_direction:
            self.turn_gopigo(self.gopigo_direction, next_direction)
    
    def drive_back(self):
        print("Reversing path...")
        
        # Reverse the path
        self.path.reverse()
        print("Reversed path:", self.path)

        # Reset navigation markers
        self.current_node_marker = 0
        self.next_node_marker = self.current_node_marker + 1

        self.current_node = self.path[self.current_node_marker]
        self.next_node = self.path[self.next_node_marker] if self.next_node_marker < len(self.path) else None

        # Ensure the bot follows the reversed path correctly
        self.drive_path()

    def drive_path(self):
        self.follow_line()
        self.handle_node_reached()
        

    def logic(self):        
        self.drive_path()
        self.drive_back()
        self.gpg.stop()