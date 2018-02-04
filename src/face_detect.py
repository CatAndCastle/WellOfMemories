import cv2
import os, urllib
import numpy as np

def get_work_dir(imagePath):
	filename, file_extension = os.path.splitext(os.path.basename(imagePath))
	dirname = os.path.dirname(imagePath) + "/analysis/"
	if not os.path.isdir(dirname):
		os.mkdir(dirname)
	return dirname

def detect(imagePath):

	# cascPath = os.path.join(here, '../assets/haarcascade_frontalface_default.xml')
	cascPath = os.environ['LAMBDA_TASK_ROOT']+'/assets/haarcascade_frontalface_default.xml'
	filename, file_extension = os.path.splitext(os.path.basename(imagePath))

	# Create the haar cascade
	faceCascade = cv2.CascadeClassifier(cascPath)

	# Read the image
	# req = urllib.urlopen(imagePath)
	# arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
	# image = cv2.imdecode(arr,-1) # 'load it as it is'
	image = cv2.imread(imagePath)
	ih,iw,ich = image.shape
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# Detect faces in the image
	faces = faceCascade.detectMultiScale(
	    gray,
	    scaleFactor=1.1,
	    minNeighbors=5,
	    minSize=(30, 30),
	    flags = cv2.CASCADE_SCALE_IMAGE #cv2.cv.CV_HAAR_SCALE_IMAGE
	)

	# print("Found {0} faces!".format(len(faces)))
	# print("Keeping {0} faces!".format(len(faces)))

	# Find dace bounding box
	center = [int(iw/2), int(ih/2)]
	bbox = [0,0,iw,ih]
	if len(faces) > 0:
		faces = reject_outliers(faces)
		bbox, center = getCenterPoint(faces)
	# x,y,w,h = getROI(iw,ih,center)
	# print [x,y,w,h]
	# animation_type = get_animation_type(len(faces), iw, ih)

	# save resized image on disk - we dont have to fetch it again in the next step
	# resized = get_work_dir(imagePath) + filename + file_extension
	# cv2.imwrite(resized, image)

	# ======================================================== 
	# DEBUG FACE DETECTION

	# Draw a rectangle around the faces
	# for (fx, fy, fw, fh) in faces:
	    # cv2.rectangle(image, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 2)
	
	# outline faces 
	# cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (255, 0, 0), 2)
	# outline ROI
	# cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
	# cv2.circle(image, (center[0], center[1]), 10, (255, 0, 0), 2)
	# cv2.putText(image,animation_type, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

	# DEV: show results
	# cv2.imshow(" %i Faces found" % len(faces), image)
	# cv2.waitKey(0)

	# cropped_image = image[y:y+h, x:x+w]
	# DEV: label focus point
	# cv2.circle(cropped_image, (center[0], center[1]), 10, (255, 0, 0), 2)
	# cv2.imshow("Cropped Image", cropped_image)
	# cv2.waitKey(0)
	
	# Save annotated image
	# destination = get_work_dir(imagePath) + filename + '_detection' + file_extension
	# cv2.imwrite(destination, image)

	# ======================================================== 

	# return (resized, [x,y,w,h], [iw,ih], center, animation_type)
	return (bbox, [iw,ih], center)

def getCenterPoint(faces):

	min_x = faces[0][0]
	min_y = faces[0][1]
	max_x = faces[0][0] + faces[0][2]
	max_y = faces[0][1] + faces[0][3]
	
	for (x, y, w, h) in faces:
		if x < min_x:
			min_x = x
		if y < min_y:
			min_y = y
		if x+w > max_x:
			max_x = x+w
		if y+h > max_y:
			max_y = y+h

	rect = [min_x, min_y, max_x-min_x, max_y-min_y]
	center = [(min_x+max_x)/2, (min_y+max_y)/2]

	return (rect, center)


# Sometimes face detection makes mistakes. Removing unlikely faces here.
def reject_outliers(faces, m=2):
	area = []
	for (x, y, w, h) in faces:
		area.append(w*h)
	# return faces[abs(area - np.mean(area)) < m * np.std(area)]
	faces = faces[(area / np.mean(area)) > 0.3]
	return faces
	# area = area[(area / np.mean(area)) > 0.3]
	# return faces[(area / np.mean(area)) < 1.7]

