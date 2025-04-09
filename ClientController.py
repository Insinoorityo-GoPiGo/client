import time
import easygopigo3 as easy
from di_sensors.easy_line_follower import EasyLineFollower
from mfrc522 import SimpleMFRC522
import threading
import traceback

class ClientController:
    def __init__(self):
        self.gpg = easy.EasyGoPiGo3()
        self.line_follower = EasyLineFollower()
        self.rfid_reader = SimpleMFRC522()

        self.base_speed = 100
        self.turn_speed = 140

        self.node_detected_event = threading.Event()

    def detect_rfid_node(self):
        try:
            result = self.rfid_reader.read()  # Read the tag
            print("Resutl: ", result)

            if isinstance(result, tuple):
                node_id = result[0]
            else:
                node_id = result
            
            # Check if this node was already read
            if hasattr(self, "last_rfid_id") and node_id == self.last_rfid_id:
                #print(f"Duplicate RFID detected: {node_id}, ignoring...")
                return False  # Ignore duplicate reads
            
            # Store the last detected RFID tag
            self.last_rfid_id = node_id
            print(f"RFID Tag detected: {node_id}")
            return True
    
        except OSError as e:
            print(f"RFID OSError IN detect_rfid_node: {e}")
            time.sleep(1)  # cooldown before next attempt
            return False

        except Exception as e:
            print(f"RFID GENERAL ERROR IN detect_rfid_node: {e}")
            return False
        
    def safe_read_position(self, retries=3, delay=0.1):
        for attempt in range(retries):
            try:
                return self.line_follower.read_position()
            except TypeError as e:
                print(f"[Line Follower Error] TypeError (attempt {attempt+1}): {e}")
            except OSError as e:
                print(f"[Line Follower Error] OSError (attempt {attempt+1}): {e}")
            except Exception as e:
                print(f"[Line Follower Error] Unexpected error (attempt {attempt+1}): {e}")
            time.sleep(delay)
        print("[Line Follower Error] All attempts failed. Defaulting to 'white'.")
        return "white"  # Safe fallback



    def follow_line(self):

        def stop_gopigo():
            self.node_detected_event.clear()
            print("Stopping at node!")
            self.gpg.stop()
            time.sleep(0.5)        

        try: 
            while self.node_detected_event.is_set() is not True:

                left_speed = 0
                right_speed = 0

                #if self.node_detected_event.is_set():
                #    stop_gopigo()
                #    break
                
                position = self.safe_read_position()

                #if self.node_detected_event.is_set():
                #    stop_gopigo()
                #    break

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

                #if self.node_detected_event.is_set():
                #    stop_gopigo()
                #    break

                self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, left_speed)
                self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, right_speed)

                # Debug Output
                #print(f"Pos: {position}, L-Speed: {left_speed}, R-Speed: {right_speed}")

                #if self.detect_rfid_node()

                #if self.node_detected_event.is_set():
                #    stop_gopigo()
                #    break

            stop_gopigo()
                    
        except KeyboardInterrupt:
            self.gpg.stop()
            exit(0)
        
        except Exception as e:
            print("An exception has occured: ")
            traceback.print_exc()
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

    def start_detecting_nodes(self):
        def node_detecting_logic():
            while True:
                if self.detect_rfid_node():
                    self.node_detected_event.set()
                    break
                else:
                    time.sleep(0.25)

        threading.Thread(target=node_detecting_logic, daemon=True).start()