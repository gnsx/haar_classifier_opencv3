#!/usr/bin/env python

'''
Face detection using haar cascades
Reading video from FFMPEG using subprocess basedon Emanuele Ruffaldi

'''

# Python 2/3 compatibility
from __future__ import print_function

import time
import os
import Queue
import subprocess
import threading
import requests
import numpy as np
import cv2
from time import ctime

# local modules
from video import create_capture
from common import clock, draw_str

# ffmpeg piping thread
class FFmpegVideoCapture:
    # mode=gray,yuv420p,rgb24,bgr24
    def __init__(self,source,width,height,mode="gray",start_seconds=0,duration=0,verbose=False):

        x = ['ffmpeg']
        if start_seconds > 0:
            #[-][HH:]MM:SS[.m...]
            #[-]S+[.m...]
            x.append("-accurate_seek")
            x.append("-ss")
            x.append("%f" % start_seconds)
        if duration > 0:
            x.append("-t")
            x.append("%f" % duration)
        x.extend(['-i', source,"-f","rawvideo", "-pix_fmt" ,mode,"-"])        
        self.nulldev = open(os.devnull,"w") if not verbose else None
        self.ffmpeg = subprocess.Popen(x, stdout = subprocess.PIPE, stderr=subprocess.STDERR if verbose else self.nulldev)
        self.width = width
        self.height = height
        self.mode = mode
        if self.mode == "gray":
            self.fs = width*height
        elif self.mode == "yuv420p":
            self.fs = width*height*6/4
        elif self.mode == "rgb24" or self.mode == "bgr24":
            self.fs = width*height*3
        self.output = self.ffmpeg.stdout
    def read(self):
        if self.ffmpeg.poll():
            return False,None
        x = self.output.read(self.fs)
        if x == "":
            return False,None
        if self.mode == "gray":
            return True,np.frombuffer(x,dtype=np.uint8).reshape((self.height,self.width))
        elif self.mode == "yuv420p":
            # Y fullsize
            # U w/2 h/2
            # V w/2 h/2
            k = self.width*self.height
            return True,(np.frombuffer(x[0:k],dtype=np.uint8).reshape((self.height,self.width)),
                np.frombuffer(x[k:k+(k/4)],dtype=np.uint8).reshape((self.height/2,self.width/2)),
                np.frombuffer(x[k+(k/4):],dtype=np.uint8).reshape((self.height/2,self.width/2))
                    )
        elif self.mode == "bgr24" or self.mode == "rgb24": 
            return True,(np.frombuffer(x,dtype=np.uint8).reshape((self.height,self.width,3)))

def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=4.0, minNeighbors=4, minSize=(48,48),
                                     flags=cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:,2:] += rects[:,:2]
    return rects

def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

kill_timer = True
content_type = 'image/jpeg'
headers = {'content-type': content_type}

def push_to_cloud():
	print ("Entered Queue")
	previous_failed = False
	while kill_timer:
		#print ("Queue is Empty processing at " )
		while (not q.empty()) and kill_timer:
			if not previous_failed:
				temp_img = q.get()
				print ("Queue not empty " + str(q.qsize()))
			try:
				previous_failed = False
				_, img_encoded = cv2.imencode('.jpg', temp_img)
				response = requests.put("http://172.16.0.109:2777/toll/rek", data=img_encoded.tostring(), headers=headers)
				print ("REQUESTED SUBMITTED")
				print (response)
			except:
				previous_failed = True
				print ("API Cholna..retrying in 5 seconds")
				time.sleep(5)
		time.sleep(10)
	print ("Exiting push_to_cloud_thread")
	return
		
q = Queue.Queue()

def main():
	import sys, getopt
	print(__doc__)
	
	cascade = cv2.CascadeClassifier("car_cascade2.xml")
	
	while kill_timer:
		print ("Opening Stream from rtsp")
		print (ctime())
		cam = FFmpegVideoCapture("rtsp://admin:admin@172.16.20.20:554/snl/live/1/1",1920,1080,"bgr24")
		do_loop = True
		while do_loop and kill_timer:
			try:
				ret, img = cam.read()
				if not ret:
					print ("exit") 
					break
				#print(len(img))
				gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
				gray = cv2.equalizeHist(gray)
				t = clock()
				rects = detect(gray, cascade)
				#print (str(len(rects)))
				vis = img.copy()
				draw_rects(vis, rects, (0, 255, 0))
				dt = clock() - t
				draw_str(vis, (20, 20), 'time: %.1f ms' % (dt*1000))
				#print (str(1/dt)  + "fps")
				if (len(rects)) > 0 :
					#cv2.imwrite(str(i) + 'image.jpg',img)
					q.put(vis)
					print (str(len(rects)) + "	Added to Queue")
					#i+=1
				#cv2.imshow('facedetect', vis)
				if cv2.waitKey(5) == 27:
					break
			except:
				do_loop = False
				#cv2.destroyAllWindows()
				cam = None
				print ("...	...	...	...	Error Going to Open Stream Again")
				time.sleep(20)
		#cv2.destroyAllWindows()
	print ("Out of here")
		
if __name__ == '__main__':
	
	print (ctime())
	kill_timer = True
	t1 = threading.Thread(target=push_to_cloud)
	t2 = threading.Thread(target=main)
	t1.start()
	t2.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print ("attempting to close threads.")
		kill_timer = False
        
        print ("All threads close submitted")
