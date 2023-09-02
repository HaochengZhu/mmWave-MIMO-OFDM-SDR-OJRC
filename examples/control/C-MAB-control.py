#!/usr/bin/env python
# coding: utf-8

# In[1]:


import csv
import numpy as np
import os
import time
import random
from datetime import datetime
import data_interface
#import matplotlib as plt

# In[26]:

class ContextualUCB:
    def __init__(self, n_radar_angle, n_beamforming_angle):
        # n_radar_angle: is the total number of angles which can be read from radar (depend on resolution)
        # n_beamformnig_angle: is the total number of angles which will apply to stream encoder  
        self.n_contexts = n_radar_angle
        self.n_actions = n_beamforming_angle
        self.total_plays = np.ones(n_radar_angle)
        self.context_action_counts = np.zeros((n_radar_angle, n_beamforming_angle))
        self.context_action_estimates = np.zeros((n_radar_angle, n_beamforming_angle))

    def get_ucb_value(self, radar_angle):
        ucb_value = self.context_action_estimates[radar_angle, :] + \
                        0.5* np.sqrt(2 * np.log(self.total_plays[radar_angle]) / (1 + self.context_action_counts[radar_angle, :]))
        return ucb_value
    
    def get_mean_value(self,radar_angle):
        mean_value = self.context_action_estimates[radar_angle,:]
        return mean_value

    def angle_selection(self, radar_angle):
        ucb_value = self.get_ucb_value(radar_angle)
        return np.argmax(ucb_value) - 90 # - 90 to change the range of angle to (-90,90) 

    def update(self, radar_angle, beamforming_angle, reward):
        self.total_plays[radar_angle] += 1
        self.context_action_counts[radar_angle, beamforming_angle] += 1 # increment the time of plays
        q_n = self.context_action_estimates[radar_angle, beamforming_angle] # calculate Q(t)value
        n = self.context_action_counts[radar_angle, beamforming_angle] # calculate number of times the arm is played
        self.context_action_estimates[radar_angle, beamforming_angle] += (reward - q_n) / n # update the UCB value
        
    def save_mean_info(self):
        np.savetxt("ucb_mean_info.csv",self.context_action_estimates,delimiter=',')

    def save_ucb_info(self):
        for angle in np.arange(0,self.n_contexts,1):
            if angle == 0:
                ucb_info_value = self.get_mean_value(angle)
            else:
                ucb_new = self.get_ucb_value(angle)
                ucb_info_value = np.vstack((ucb_info_value,ucb_new))
        np.savetxt("ucb_info.csv",ucb_info_value,delimiter=',')

    def save_trained_model(self):
        np.save('estimated_mean.npy',self.context_action_estimates)
        np.save('total_play.npy',self.total_plays)
        np.save('context_action_play.npy',self.context_action_counts)

    def load_trained_model(self, est_mean, total_play, context_action_play):
        self.context_action_estimates = est_mean
        self.total_plays = total_play
        self.context_action_counts = context_action_play



# Testing
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
print(parent_dir)

current_date_time2 = '22:10:39.001'
peak_power = 0.0239202
snr_est = 23
range_val = 5.10998
angle_val = -46.599
radar_log_path = os.path.join(parent_dir, 'data', 'radar_log.csv')
comm_log_path = os.path.join(parent_dir, 'data', 'comm_log.csv')
radar_data_path = os.path.join(parent_dir, 'data','radar_data.csv')
packet_log_path = os.path.join(parent_dir,'data','packet_log.csv')
packet_data_path = os.path.join(parent_dir,'data','packet_data.csv')
plot_log_path     = os.path.join(parent_dir, 'data', 'plot_log.csv')

test_radar = data_interface.RadarData(current_date_time2, peak_power, snr_est, range_val, angle_val)
test_radar_data = data_interface.RadarData(current_date_time2, peak_power, snr_est, range_val, angle_val)
test_radar = data_interface.load_radar_data(radar_log_path)
test_packet = data_interface.PacketData(current_date_time2,1,10)
print(test_radar.est_angle)

test_comm = data_interface.CommData(current_date_time2, 0, 1, snr_est, snr_est, 34.3, 2.3,0)
test_comm = data_interface.load_comm_data(comm_log_path)
print(test_comm.per_val)

data_interface.write_radar_log(test_radar,radar_log_path)


# In[27]:

# Control algorithm for C-UCB
n_radar_angle = 181 # one degree resolution
n_beamforming_angle = 181 # one degree resolution
agent = ContextualUCB(n_radar_angle,n_beamforming_angle)
pre_radar_time = 0
pre_comm_time = 0
last_packet = 1
pre_radar_angle = 0
pre_beamforming_angle = 0
curr_radar_angle = int(np.round(test_radar.est_angle))
curr_beamforming_angle = int(np.round(test_radar.est_angle))
pre_sys_time = time.time()
ucb_count = 0

# Load trained model if needed
#trained_model = np.load('estimated_mean.npy')
#trained_total_play = np.load('total_play.npy')
#trained_action_play = np.load('context_action_play.npy')
#agent.load_trained_model(trained_model, trained_total_play, trained_action_play)


while True:
        time.sleep(0.001)
        current_sys_time = time.time()
        if current_sys_time - pre_sys_time >= 2: # regular NDP packet
            # Send out NDP
            test_packet.packet_type = 1
            test_packet.packet_size = 7
            current_time = datetime.now()
            test_packet.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3]
            data_interface.write_packet_data(test_packet, packet_data_path)
            data_interface.write_packet_log(test_packet,packet_log_path)
            pre_sys_time = current_sys_time
            last_packet = 1
            print('regular NDP')
            continue

        pre_test_radar = test_radar
        pre_test_comm = test_comm
        test_radar = data_interface.load_radar_data(radar_log_path) # update radar info
        test_comm = data_interface.load_comm_data(comm_log_path) # update comm info
        if test_radar == None:
            test_radar = pre_test_radar
        else:
            pre_test_radar = test_radar

        if test_comm == None:
            test_comm = pre_test_comm
        else:
            pre_test_comm = test_comm

        current_time = datetime.now() # test
        test_radar.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3] #test if no change, send NDP
       
        if pre_radar_time != test_radar.timestamp: # and pre_comm_time != test_comm.timestamp: #new radar and comm information updated     
            # udpate PER throughput reward data
            curr_comm_reward = test_comm.reward_val
            curr_comm_per = test_comm.per_val
            curr_comm_throughput = test_comm.throughput
            curr_comm_snr = test_comm.data_snr
            reward = curr_comm_reward * curr_comm_snr/20
            #print(f"reward: {reward}")
            if last_packet == 2: # update only for data packet
                agent.update(curr_radar_angle+90,curr_beamforming_angle+90,reward) # update reward for last decision
                ucb_count += 1
            
            pre_comm_time = test_comm.timestamp
            pre_radar_time = test_radar.timestamp
            
            if ucb_count == 100: # save ucb every 1000 round
                agent.save_ucb_info()
                agent.save_mean_info()
                agent.save_trained_model()
                ucb_count = 0
                
            
            if curr_comm_per >= 30: # send NDP if higher than threshold
                test_packet.packet_type = 1
                test_packet.packet_size = 7
                last_packet = 1
                current_time = datetime.now()
                test_packet.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3]
                data_interface.write_packet_data(test_packet, packet_data_path)
                data_interface.write_packet_log(test_packet,packet_log_path)
                #print("Higher PER, send NDP")
                continue
            
            # Send data
            curr_radar_angle = int(np.round(test_radar.est_angle)) #angle input for C-MAB
            curr_beamforming_angle = int(agent.angle_selection(curr_radar_angle + 90)) # beamforming angle decision from MAB
            print(f"radar angle: {curr_radar_angle}")
            print(f"beamforming angle by C-UCB:{curr_beamforming_angle}")
            # Write to interface
            test_radar_data.est_angle = curr_beamforming_angle
            current_time = datetime.now()
            test_packet.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3]
            test_radar_data.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3]
            test_packet.packet_type = 2
            test_packet.packet_size = 400
            last_packet = 2
            data_interface.write_packet_data(test_packet, packet_data_path)
            data_interface.write_packet_log(test_packet,packet_log_path)
            data_interface.write_radar_data(test_radar_data, radar_data_path)
            data_interface.write_radar_log(test_radar, radar_log_path)

            data_interface.write_plot_log(test_comm.packet_type, pre_radar_angle, pre_beamforming_angle, test_comm.data_snr, test_comm.CRC, test_comm.throughput, plot_log_path)
            pre_radar_angle = curr_radar_angle
            pre_beamforming_angle = curr_beamforming_angle
        #else: # repeat previous decision, no radar-aided beamforming
            #current_time = datetime.now()
            #test_packet.timestamp = current_time.strftime("%H:%M:%S") + ':'+current_time.strftime("%f")[:3]
            #data_interface.write_packet_data(test_packet, packet_data_path)
            #data_interface.write_packet_log(test_packet,packet_log_path)
            #print('repeat previous setting')



# In[29]:

ucb_info = np.loadtxt("ucb_info.csv", delimiter=",")
context_values = np.arange(-90,90,20)
for context in context_values:
    ucb_estimates = ucb_info[context,:]
    plt.plot(range(-90, 91), ucb_estimates, label=f'radar angle{context}')

plt.xlabel('Beamforming angle')
plt.ylabel('UCB Estimate')
plt.title('UCB Estimates for Different Radar angle')
plt.legend()
plt.show()
