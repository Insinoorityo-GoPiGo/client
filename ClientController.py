import time
import easygopigo3 as easy
from di_sensors.easy_line_follower import EasyLineFollower
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
import threading
import traceback
from multiprocessing import Process, Event, Value, Queue

class ClientController:
    def __init__(self):
        self.gpg = easy.EasyGoPiGo3()
        self.line_follower = EasyLineFollower()
        self.rfid_reader = SimpleMFRC522()
        self.camera = PiCamera()

        self.base_speed = 100
        self.turn_speed = 140

        self.node_detected_event = threading.Event()
        self.obstacle_detected_event = Event()
        self.image_capture_queue = Queue()

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
            #self.node_detected_event.clear()
            print("Stopping at node!")
            self.gpg.stop()
            time.sleep(0.5)        

        try: 
            while True:
                if self.obstacle_detected_event.is_set():
                    stop_gopigo()
                    continue
                if self.node_detected_event.is_set():
                    stop_gopigo()
                    self.node_detected_event.clear()
                    break

                left_speed = 0
                right_speed = 0
                    
                position = self.safe_read_position()
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
            #stop_gopigo()
            time.sleep(0.5)
                    
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
            time.sleep(1.5)
            while True:
                if self.detect_rfid_node():
                    self.node_detected_event.set()
                    break
                else:
                    time.sleep(0.25)

        threading.Thread(target=node_detecting_logic, daemon=True).start()
    
    def start_distance_monitoring(self):
        def distance_monitor(obstacle_event, capture_queue):
            from easygopigo3 import EasyGoPiGo3
            #from picamera import PiCamera
            import time

            gpg = EasyGoPiGo3()
            distance_sensor = gpg.init_distance_sensor()
            #camera = PiCamera()

            print("[Distance Process] Started")

            while True:
                try:
                    distance = distance_sensor.read_mm() / 10.0
                    print(f"[Distance] {distance:.1f} cm")

                    if distance <= 20 and not obstacle_event.is_set():
                        obstacle_event.set()
                        print("Object detected within 20 cm. Stopping and capturing image.")
                        capture_queue.put("TAKE_PICTURE")
                        gpg.stop()
                        print("Image captured. Waiting 10 seconds...")
                        time.sleep(10)
                        obstacle_event.clear()
                        print("Resuming.")

                    time.sleep(0.2)

                except Exception as e:
                    print(f"[Distance Sensor Error] {e}")
                    time.sleep(0.5)

        # Start the process
        distance_process = Process(target=distance_monitor, args=(self.obstacle_detected_event, self.image_capture_queue))
        distance_process.daemon = True
        distance_process.start()

    def start_camera_thread(self):
        def camera_worker():

            print("[Camera Thread] Started")

            while True:
                msg = self.image_capture_queue.get()
                if msg == "TAKE_PICTURE":
                    print("[Camera Thread] Taking picture...")
                    try:
                        #self.camera.start_preview()
                        time.sleep(2)
                        self.camera.capture('/home/pi/Desktop/captured_image.jpg')
                        #self.camera.stop_preview()
                        print("Image captured.")
                    except Exception as e:
                        print(f"[Camera Error] {e}")

        threading.Thread(target=camera_worker, daemon=True).start()