import time

class PID:

    def __init__(self, P, I, D, M):

        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.max = M

        self.sample_time = 0.01
        self.current_time = time.time()
        self.last_time = self.current_time

        self.clear()

    def clear(self):
        self.point = 0.0

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        self.windup = 0

        self.output = 0

    def update(self, feedback):
        error = self.point - feedback

        self.current_time = time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if (delta_time >= self.sample_time):
            self.PTerm = error
            self.ITerm += error * delta_time

            if (self.ITerm < -self.windup):
                self.ITerm = -self.windup
            elif (self.ITerm > self.windup):
                self.ITerm = self.windup

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            self.last_time = self.current_time
            self.last_error = error

            self.output = (self.Kp * self.PTerm) + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

            if self.output < (-1 * self.max):
                return -1 * self.max
            elif self.output > self.max:
                return self.max
            else:
                return self.output
        return 0
