from __future__ import division
import shlex
import subprocess
import sys
import threading
import os
from flask import Flask,jsonify,request,render_template
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

app = Flask(__name__)
timelist = []
ave_timelist = []
host_amt_list = []
work_load_list = []
lock = threading.Lock()

fig = plt.figure()
ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)

def scale(process_name, thread_num):
	cmd = 'sudo docker service scale '+process_name+'='+str(thread_num)
	args = shlex.split(cmd)
	p = subprocess.run(args,stdout=subprocess.PIPE)
	result = p.stdout
	print(result)

def check_result(result, process_name, thread_num):
	if type(result)== bytes:
			result = result.decode().strip('\n')
	expected_result = process_name +' scaled to '+thread_num

	return result == expected_result

def plot_three_figures(k):
	interval = [5*i for i in range(0,len(host_amt_list))]
	x = np.array(interval)
	
	y1 = np.array(ave_timelist)
	ax1.clear()
	ax1.set_ylabel('average response time')
	ax1.set_title('response time vs. real time')
	try:
		ax1.plot(x,y1)
	except ValueError:
		x = np.array([5*i for i in range(0,len(y1))])
		ax1.plot(x,y1)
	
	y2 = np.array(host_amt_list)
	ax2.clear()
	ax2.set_ylabel('host amount')
	ax2.set_title('host amount vs. real time')
	try:
		ax2.plot(x,y2)
	except ValueError:
		x = np.array([5*i for i in range(0,len(y2))])
		ax2.plot(x,y2)
	
	y3 = np.array(work_load_list)
	ax3.clear()
	ax3.set_ylabel('request/sec')
	ax3.set_title('workload vs. real time')
	try:
		ax3.plot(x,y3)
	except ValueError:
		x = np.array([5*i for i in range(0,len(y3))])
		ax3.plot(x,y3)
	
	dir_path = os.path.dirname(os.path.realpath( __file__ ))+'/static/images/timeplots.png'
	fig.savefig(dir_path)

def update (upper_bound, lower_bound, host_amt = 1):
	lock.acquire()
	
	if (len(timelist) > 0):
			tmp = []
			ave = 0
			for i in range(0,len(timelist)):
				if timelist[i]<5*5:
					tmp.append(timelist[i])
			#if len(tmp) > len(timelist) / 2:
			#	ave = sum(tmp) / len(tmp)				
			#else:
			#	ave = sum(timelist) / len(timelist)
			if (len(tmp) != 0):
				ave = sum(tmp) / len(tmp)
			else:
				ave = sum(timelist) / len(timelist)
			ave_timelist.append(ave)
			print(ave_timelist)
			print(timelist)
			request_per_second = len(timelist)/5
			work_load_list.append(request_per_second)
			
			del timelist[:]
			lock.release()
			if (doScaling == "1" and len(ave_timelist)>=2):
				if (ave > upper_bound and ave_timelist[-2]>upper_bound):
						host_amt = host_amt + int(ave/upper_bound)
						print("up")
						scale('app_web', host_amt) # dummy name, see actual case
				elif (ave < lower_bound and ave_timelist[-2]<lower_bound):
						host_amt = host_amt - 2*int(lower_bound/ave)
						if (host_amt<=0):
							host_amt = 1
						print("down")
						scale('app_web', host_amt) # dummy name, see actual case
				else:
						pass
	else:
			if (host_amt > 1):
				host_amt -= 1
				print("down")
				scale('app_web', host_amt) # dummy name, see actual case
				
			ave_timelist.append(0)
			work_load_list.append(0)
			lock.release()
	host_amt_list.append(host_amt)
	t = threading.Timer(5, update, args = (upper_bound, lower_bound, host_amt)) # hardcoded wait time
	t.start();

def est_host():
	print("Client communication thread on.")
	app.run(host="0.0.0.0", port=8001, debug=False)


@app.route('/',methods=['GET','POST'])
def hello():
	if request.method == "POST":
			try:
					input_json = request.get_json(force=True)
					lock.acquire()
					timelist.append(input_json)
					lock.release()
			except ValueError:
					print ("failed")
	return render_template('base.html')

if __name__ == "__main__":
	try:
		doScaling = sys.argv[1]
		upper_bound = int(sys.argv[2])
		lower_bound = int(sys.argv[3])
	except Exception:
		print("missing necessary variables, scale set to true, upper set to 7, lower set to 4")
		doScaling = "1"
		upper_bound = 7
		lower_bound = 4
	
	scale('app_web', 1)
	update(upper_bound, lower_bound)
	thread = threading.Thread(target = est_host);
	thread.start();
	ani = animation.FuncAnimation(fig,plot_three_figures,interval = 1000)
	plt.show()

