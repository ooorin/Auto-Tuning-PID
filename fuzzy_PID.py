from __future__ import division
import PID
import time
import matplotlib.pyplot as plt
import numpy as np
import simulator
import random
from scipy.interpolate import BSpline, make_interp_spline

# fuzzy set
NB = 0 # negative big
NM = 1 # negative mid
NS = 2 # negative small
ZE = 3 # zero
PS = 4 # positive small
PM = 5 # positive mid
PB = 6 # positive big

# scale of P, I, D, err, d_err
scale_P = 2 / 3
scale_I = 2 / 3
scale_D = 1 / 3
scale_err = 1
scale_d_err = 1 / 3

# rules, 7x7 matrix, err and d_err -> P, I, D
# row: err [NB, NM, NS, ZE, PS, PM, PB]T
# col: d_err [NB, NM, NS, ZE, PS, PM, PB]
rules_P = [
	[PB, PB, PM, PM, PS, ZE, ZE],
	[PB, PB, PM, PS, PS, ZE, ZE],
	[PM, PM, PM, PS, ZE, NS, NS],
	[PM, PM, PS, ZE, NS, NM, NM],
	[PS, PS, ZE, NS, NS, NM, NM],
	[PS, ZE, NS, NM, NM, NM, NB],
	[ZE, ZE, NM, NM, NM, NB, NB]
]
rules_I = [
	[PS, NS, NB, NB, NB, NM, PS],
	[PS, NS, NB, NM, NM, NS, ZE],
	[ZE, NS, NM, NM, NS, NS, ZE],
	[ZE, NS, NS, NS, NS, NS, ZE],
	[ZE, ZE, ZE, ZE, ZE, ZE, ZE],
	[PB, NS, PS, PS, PS, PS, PB],
	[PB, PM, PM, PM, PS, PS, PB]
]
rules_D = [
	[NB, NB, NM, NM, NS, ZE, ZE],
	[NB, NB, NM, NS, NS, ZE, ZE],
	[NB, NM, NS, NS, ZE, PS, PS],
	[NM, NM, NS, ZE, PS, PM, PM],
	[NM, NS, ZE, PS, PS, PM, PB],
	[ZE, ZE, PS, PS, PM, PB, PB],
	[ZE, ZE, PS, PM, PM, PB, PB]
]

#membership function 1
def fuzzy1(x):
	# input must be rescaled
	# output is a list of membership
	# [NB, NM, NS, ZE, PS, PM, PB]
	membership = [0, 0, 0, 0, 0, 0, 0]
	# NB
	if x <= -3:
		membership[0] = 1
	elif -3 < x and x <= -1:
		membership[0] = (-1 - x) / 2
	# NM
	if -3 <= x and x <= -2:
		membership[1] = x + 3
	elif -2 < x and x<= 0:
		membership[1] = (0 - x) / 2
	# NS
	if -3 <= x and x <= -1:
		membership[2] = (x + 3) / 2
	elif -1 < x and x <= 1:
		membership[2] = (1 - x) / 2
	# ZE
	if -2 <= x and x <= 0:
		membership[3] = (x + 2) / 2
	elif 0 < x and x <= 2:
		membership[3] = (2 - x) / 2
	# PS
	if -1 <= x and x <= 1:
		membership[4] = (x + 1) / 2
	elif 1 < x and x <= 3:
		membership[4] = (3 - x) / 2
	# PM
	if 0 <= x and x <= 2:
		membership[5] = (x - 0) / 2
	elif 2 < x and x <= 3:
		membership[5] = 3 - x
	# PB
	if 1 <= x and x < 3:
		membership[6] = (x - 1) / 2
	elif 3 <= x:
		membership[6] = 1

	return membership

# membership function 2
def fuzzy2(x):
	# input must be rescaled
	# output is a list of membership
	# [NB, NM, NS, ZE, PS, PM, PB]
	membership = [0, 0, 0, 0, 0, 0, 0]
	# NB
	if x <= -3:
		membership[0] = 1
	elif -3 < x and x <= -2:
		membership[0] = (-2 - x) / 1
	# NM
	if -3 <= x and x <= -2:
		membership[1] = x + 3
	elif -2 < x and x<= -1:
		membership[1] = (-1 - x) / 1
	# NS
	if -2 <= x and x <= -1:
		membership[2] = (x + 2) / 1
	elif -1 < x and x <= 0:
		membership[2] = (0 - x) / 1
	# ZE
	if -1 <= x and x <= 0:
		membership[3] = (x + 1) / 1
	elif 0 < x and x <= 1:
		membership[3] = (1 - x) / 1
	# PS
	if 0 <= x and x <= 1:
		membership[4] = (x - 0) / 1
	elif 1 < x and x <= 2:
		membership[4] = (2 - x) / 1
	# PM
	if 1 <= x and x <= 2:
		membership[5] = (x - 1) / 1
	elif 2 < x and x <= 3:
		membership[5] = 3 - x
	# PB
	if 2 <= x and x < 3:
		membership[6] = (x - 2) / 1
	elif 3 <= x:
		membership[6] = 1

	return membership

def inv_fuzzy(membership):
	# Sugeno-style
	# input is a list of membership
	# [NB, NM, NS, ZE, PS, PM, PB]
	# output must be rescaled
	numerator = 0
	denominator = 0
	if sum(membership) == 0:
		return 0
	for i in range(7):
		numerator += membership[i] * (i - 3)
		denominator += membership[i]
	return numerator / denominator

def fuzzy_and(typ, x, y):
	# two types
	if typ == 0:
		return min(x, y)
	else:
		return x * y

def fuzzy_or(typ, x, y):
	if typ == 0:
		return max(x, y)
	else:
		return x + y - x * y

if __name__ == "__main__":
	pid = PID.PID(1, 1, 0.5, 10)
	
	pid.point = 1
	pid.sample_time = 0.01
	pid.windup = 5

	feedback = 0
	feedback_list = []
	time_list = []
	setpoint_list = []

	fuzzy_P = [0, 0, 0, 0, 0, 0, 0]
	fuzzy_I = [0, 0, 0, 0, 0, 0, 0]
	fuzzy_D = [0, 0, 0, 0, 0, 0, 0]

	L = 100
	output = 0
	for i in range(1, L):
		output += pid.update(feedback)

		feedback = simulator.func1(output + 1 / i)
		
		err = pid.point - feedback
		d_err = err - pid.last_error
		
		print 'output of PID contoller is: ', output
		print 'error is: ', err
		print 'delta error is: ', d_err
		
		fuzzy_err = fuzzy2(err / scale_err) # get membership vector
		fuzzy_d_err = fuzzy2(d_err / scale_d_err) # get membership vector
		
		feedback_list.append(feedback)
		setpoint_list.append(pid.point)
		time_list.append(i)

		time.sleep(0.01)

		# rule-based reasoning
		fuzzy_P = [0, 0, 0, 0, 0, 0, 0]
		fuzzy_I = [0, 0, 0, 0, 0, 0, 0]
		fuzzy_D = [0, 0, 0, 0, 0, 0, 0]
		typ = 0
		for i in range(7):
			for j in range(7):
				fuzzy_P[rules_P[i][j]] = max(fuzzy_and(typ, fuzzy_err[i], fuzzy_d_err[j]), fuzzy_P[rules_P[i][j]])
				fuzzy_I[rules_I[i][j]] = max(fuzzy_and(typ, fuzzy_err[i], fuzzy_d_err[j]), fuzzy_I[rules_I[i][j]])
				fuzzy_D[rules_D[i][j]] = max(fuzzy_and(typ, fuzzy_err[i], fuzzy_d_err[j]), fuzzy_I[rules_I[i][j]])

		dP = inv_fuzzy(fuzzy_P) * scale_P
		dI = inv_fuzzy(fuzzy_I) * scale_I
		dD = inv_fuzzy(fuzzy_D) * scale_D

		print 'membership vector of error is: ', fuzzy_err
		print 'membership vector of delta error is: ', fuzzy_d_err
		print 'membership vector of Kp is: ', fuzzy_P
		print 'membership vector of Ki is: ', fuzzy_I
		print 'membership vector of Kd is: ', fuzzy_D

		# make sure Kp/i/d are in the domain
		pid.Kp = min(max(0, pid.Kp + dP), 3 * scale_P)
		pid.Ki = min(max(0, pid.Ki + dI), 3 * scale_I)
		pid.Kd = min(max(0, pid.Kd + dD), 3 * scale_D)

		print 'delta Kp is: ', dP
		print 'delta Ki is: ', dI
		print 'delta Kd is: ', dD
		print 'Kp is: ', pid.Kp
		print 'Ki is: ', pid.Ki
		print 'Kd is: ', pid.Kd
		print '\n'
		
	time_sm = np.array(time_list)
	time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)
	helper_x3 = make_interp_spline(time_list, feedback_list)
	feedback_smooth = helper_x3(time_smooth)

	# draw the response curve
	plt.plot(time_smooth, feedback_smooth)
	plt.plot(time_list, setpoint_list)
	plt.xlim((0, L))
	plt.ylim((min(feedback_list)-0.5, max(feedback_list)+0.5))
	plt.xlabel('time (s)')
	plt.ylabel('PID (PV)')
	plt.title('FUZZY PID')

	plt.ylim((1-0.5, 1+0.5))

	plt.grid(True)
	plt.show()