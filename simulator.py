import random
import time
import math

# some functions for simulation
def func1(x):
	if x >= 0:
		y = min(math.log(x + 1), 3)
	else:
		y = 0
	return y

def func2(x):
	if x >= 0:
		return min(1 / (3*x - 1) / (2*x - 1), 3)
	else:
		return 1

def func3(x):
	if x >= 0:
		return math.log(x + 1)
	return -math.log(-x + 1)