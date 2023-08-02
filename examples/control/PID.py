import os
import time
import random
from datetime import datetime
import data_interface

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
print(parent_dir)



class PIDController:
    def __init__(self, P=0.2, I=0.0, D=0.0, current_time=None):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.current_time = current_time if current_time is not None else time.time()
        self.last_time = self.current_time

        self.clear()

    def clear(self):
        """Clears PID computations and coefficients"""
        self.SetPoint = 0.0

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        # Windup Guard
        self.int_error = 0.0
        self.windup_guard = 20.0

        self.output = 0.0

    def update(self, feedback_value, current_time=None):
        """Calculates PID value for given reference feedback"""
        error = self.SetPoint - feedback_value

        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if (delta_time >= 0.01):  # Ignore very small time delta
            self.PTerm = self.Kp * error
            self.ITerm += error * delta_time

            if (self.ITerm < -self.windup_guard):
                self.ITerm = -self.windup_guard
            elif (self.ITerm > self.windup_guard):
                self.ITerm = self.windup_guard

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

    def set_point(self, set_point):
        """Initiates a new set point and resets the PID controller"""
        self.SetPoint = set_point
        self.clear()

def send_data():
    print("Sending data packet")

def send_ndp(angle):
    print(f"Sending NDP with angle {angle}")

def get_snr():
    # Mock function, replace with your actual SNR acquisition method
    import random
    return random.uniform(0, 30)  # For demo purpose, returns a random SNR between 0 and 30

def main():
    target_snr = 20.0  # Define target SNR here
    pid = PIDController(P=0.2, I=0.1, D=0.01)
    pid.set_point(target_snr)

    while True:

        # test_comm = data_interface.CommData(pid.current_time, 0, 0, 0, 0, 0, 0, 0)
        test_comm = data_interface.load_comm_data(comm_log_path)
        current_snr = test_comm.snr_val
        pid.update(current_snr)
        output = pid.output

        if output >= 0: # If the output is positive, it means SNR is increasing or above target.
            packet_type = 2
            packet_size = min(300, 10*int(output)) # Size is adjusted based on PID output
        else: # If the output is negative, it means SNR is decreasing or below target.
            packet_type = 1
            packet_size = 10

        print(packet_type, packet_size)
        test_packet = data_interface.PacketData(pid.current_time, packet_type, packet_size)
        data_interface.write_packet_data(test_packet, packet_data_path)
        data_interface.write_packet_log(test_packet, packet_log_path)

        time.sleep(0.1)  # Loop delay, tune this value as you need

if __name__ == "__main__":
    main()