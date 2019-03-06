import PID
import time
import matplotlib.pyplot as plt
import numpy as np
import simulator
import random
#from scipy.interpolate import spline
from scipy.interpolate import BSpline, make_interp_spline #  Switched to BSpline

def test_pid(P=0.2, I=0.1, D=0.0, M=10, L=100):

    pid = PID.PID(P, I, D, M)

    pid.point = 0.0
    pid.sample_time = 0.01

    END = L
    feedback = 0

    feedback_list = []
    time_list = []
    setpoint_list = []

    for i in range(1, END):
        output = pid.update(feedback)
        if not pid.point == 0:
            feedback += simulator.func3(output - (1/i)) #+ random.uniform(-0.01, 0.01)
        #print feedback
        
        if i>9:
            pid.point = 1
        
        time.sleep(0.02)

        feedback_list.append(feedback)
        setpoint_list.append(pid.point)
        time_list.append(i)

    time_sm = np.array(time_list)
    time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)

    # feedback_smooth = spline(time_list, feedback_list, time_smooth)
    # Using make_interp_spline to create BSpline
    helper_x3 = make_interp_spline(time_list, feedback_list)
    feedback_smooth = helper_x3(time_smooth)

    plt.plot(time_smooth, feedback_smooth)
    plt.plot(time_list, setpoint_list)
    plt.xlim((0, L))
    plt.ylim((min(feedback_list)-0.5, max(feedback_list)+0.5))
    plt.xlabel('time (s)')
    plt.ylabel('PID (PV)')
    plt.title('TEST PID')

    plt.ylim((1-0.5, 1+0.5))

    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    test_pid(1.8, 0.5, 0, M=10, L=50)