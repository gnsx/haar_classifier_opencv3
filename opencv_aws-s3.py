#!/usr/bin/env python

'''
face detection using haar cascades

USAGE:
    facedetect.py [--cascade <cascade_fn>] [--nested-cascade <cascade_fn>] [<video_source>]
'''

# Python 2/3 compatibility
from __future__ import print_function

import time
import Queue
import threading
import requests
import numpy as np
import cv2

# local modules
from video import create_capture
from common import clock, draw_str


def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=4.0, minNeighbors=8, minSize=(48, 48),
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
	while kill_timer:
		print ("Size of Queue : " + str(q.qsize()))
		while not q.empty():
			temp_img = q.get()
			_, img_encoded = cv2.imencode('.jpg', temp_img)
			response = requests.post("http://172.16.0.109:2777/toll/rek", data=img_encoded.tostring(), headers=headers)
			print ("sent data out data")
			print (response)
		time.sleep(1)
	print ("Exiting push_to_cloud_thread")
	return
		
q = Queue.Queue()
		
def main():
	import sys, getopt
	print(__doc__)
	
	args, video_src = getopt.getopt(sys.argv[1:], '', ['cascade=', 'nested-cascade='])
	try:
		video_src = video_src["rtsp://admin:admin@172.16.20.20:554/snl/live/1/1"]
	except:
		video_src = 0
	args = dict(args)
	cascade_fn = args.get('--cascade', "car_cascade.xml")
		
	cascade = cv2.CascadeClassifier(cascade_fn)
	while kill_timer:
		print ("Opening Stream from rtsp")
		cam = cv2.VideoCapture("rtsp://admin:admin@172.16.20.20:554/snl/live/1/1")
		i = 0
		do_loop = True
		while do_loop and kill_timer:
			ret, img = cam.read()
			try:
				gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
				gray = cv2.equalizeHist(gray)
				t = clock()
				rects = detect(gray, cascade)
				#print (str(len(rects)))
				vis = img.copy()
				draw_rects(vis, rects, (0, 255, 0))
				dt = clock() - t
				draw_str(vis, (20, 20), 'time: %.1f ms' % (dt*1000))
				#print (str(1/dt) + ' ' + str(i) + 'box')
				if (len(rects)) > 0 :
					cv2.imwrite(str(i) + 'image.jpg',img)
					q.put(img)
					i+=1
				#cv2.imshow('facedetect', vis)
				if cv2.waitKey(5) == 27:
					break
			except:
				do_loop = False
				cv2.destroyAllWindows()
				cam = None
				print ("Error")
				
	cv2.destroyAllWindows()
	print ("Out of here")
		
if __name__ == '__main__':
	
	kill_timer = True
	t1 = threading.Thread(target=push_to_cloud)
	t2 = threading.Thread(target=main)
	t1.start()
	t2.start()
	try:
		while True:
			time.sleep(.1)
	except KeyboardInterrupt:
		print ("attempting to close threads.")
		kill_timer = False
        
        print ("threads successfully closed")
