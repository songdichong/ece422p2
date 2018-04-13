"""
HTTP client simulator. It simulate a number of concurrent users and calculate the response time for each request.
"""
import requests
import time
import threading
import sys

delay = 1;

if len(sys.argv) < 4:
	print('To few arguments; you need to specify 3 arguments.')
	print('Default values will be used for server_ip, no of users and think time.\n')
	swarm_master_ip = '10.2.10.9'  # ip address of the Swarm master node
	no_users = 1  # number of concurrent users sending request to the server
	think_time = 1  # the user think time (seconds) in between consequent requests
else:
	print('Default values have be overwritten.')
	swarm_master_ip = sys.argv[1]
	no_users = int(sys.argv[2])
	think_time = float(sys.argv[3])


class MyThread(threading.Thread):
	def __init__(self, name, counter):
		threading.Thread.__init__(self)
		self.threadID = counter
		self.name = name
		self.counter = counter
		self.avetime = 0
		self.stop_flag = 0

	def run(self):
		print("Starting " + self.name + str(self.counter))
		while (self.stop_flag == 0):
			workload(self.name + str(self.counter), self.stop_flag)


def workload(user, stop):
	done = 0;
	#temp solution for Exception in thread User
	#exception occurs due to scaling\
	while (done == 0):
		try:
			t0 = time.time()
			requests.get('http://' + swarm_master_ip + ':8000/')
			t1 = time.time()
			time.sleep(think_time)
			done = 1
		#retry
		except Exception:
			print("Disconnected retry: process " + user);
			done = 0

	print("Response Time for " + user + " = " + str(t1 - t0))
	try:
		if (stop == 0): # atomic probably need not lock
			res = requests.post("http://" + swarm_master_ip + ":" + str(8001) + "/", json = (t1 - t0)) # harcoded portnumber
	except Exception:
		pass

def launch_thread(i = 0):
	MyThread("Users", i).start();
	i += 1
	t = threading.Timer(delay, launch_thread, args = (i,)) # hardcoded wait time
	t.start();

if __name__ == "__main__":
	threads = []
	for i in range(no_users):
		threads.append(MyThread("User", i))
	for i in range(no_users):
		threads[i].start()

	while(True):
		try:
			thread_num = int(input("Num thread can be changed at any time by typing in proper value: \n"));
			if (thread_num != no_users):
				print("Change num thread.")
				for i in range(no_users):
					threads[i].stop_flag = 1 # atomic, probarbly need not lock
				for i in range(no_users):
					threads[i].join()

				no_users = thread_num
				del threads[:]
				print("Restarting...")
				for i in range(no_users):
					threads.append(MyThread("User", i))
				for i in range(no_users):
					threads[i].start()
		except:
			print("Bad input, try again");


