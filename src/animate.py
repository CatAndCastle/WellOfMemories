#============================================================
# animate.py
#
# CatAndCastle LLC, 2018
#============================================================
import sys,os,json,urllib,decimal
import subprocess
from subprocess import call,check_output
import src.face_detect as FaceDetect
import src.common as common

here = os.path.dirname(os.path.realpath(__file__))
FFMPEG_BIN = os.path.join(here, '../bin/ffmpeg')

def animatePhoto(img, animation, duration):
	# ANIMATE
	if animation == "panup":
		return PhotoPanUp(img, duration)
	elif animation == "pandown":
		return PhotoPanDown(img, duration)


def PhotoPanUp(img, d):
	# FACE DETECTION
	roi, dimensions, focus = FaceDetect.detect(img)
	start_y_percent = 0.00
	if dimensions[1] > dimensions[0]:
		start_y_percent = roi[1]/float(dimensions[1])

	video_path = '/tmp/video-' + common.randomString(10) + '.mp4'

	cmd = FFMPEG_BIN + " -y -loop 1 -loglevel panic -i %s \
	-c:v libx264 -pix_fmt yuv420p \
	-filter_complex \
	\"[0:v]crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[v01]; \
	[v01]scale=-1:4000,crop=w=iw:h='min(iw*9/16,ih)':x=0:y='%.2f*ih-((t/%.2f)*min(%.2f*ih,(ih-oh)/6))',trim=duration=%.2f[v02]; \
	[v02]zoompan=z='if(lte(pzoom,1.0),1.15,max(1.0,pzoom-0.0005))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1[v]\" \
	-map \"[v]\" -s \"1280x720\" %s" % (img, start_y_percent, d, start_y_percent, d, video_path)

	# TESTING
	# cmd = FFMPEG_BIN + " -y -loop 1 -loglevel panic -i %s \
	# -filter_complex \
	# \"[0]zoompan=z='min(zoom+0.0015,1.5)':d=%.2f:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)[v]\" \
	# -map \"[v]\" -c:v libx264 -pix_fmt yuv420p -s \"1280x720\" %s" % (img, d, video_path)
	
	try:
		result = check_output(cmd, shell=True,stderr=subprocess.STDOUT)
		return {'statusCode': 200, 'video_path':video_path}
	except subprocess.CalledProcessError as e:
		print('Error running FFMPEG')
		print(json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output}))
		return {
	        'statusCode': 400,
	        'error': e
	        # 'body': json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output})
	    }

def PhotoPanDown(img, d):
	# FACE DETECTION
	roi, dimensions, focus = FaceDetect.detect(img)
	start_y_percent = 0.00
	if dimensions[1] > dimensions[0]:
		start_y_percent = roi[1]/float(dimensions[1])

	video_path = '/tmp/video-' + common.randomString(10) + '.mp4'

	cmd = FFMPEG_BIN + " -y -loop 1 -loglevel panic -i %s \
	-c:v libx264 -pix_fmt yuv420p \
	-filter_complex \
	\"[0:v]crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[v01]; \
	[v01]scale=-1:4000,crop=w=iw:h='min(iw*9/16,ih)':x=0:y='max((ih-oh)/6,%.2f*ih-((ih-oh)/6))+((t/%.2f)*(ih-oh)/6)',trim=duration=%.2f[v02]; \
	[v02]zoompan=z='min(pzoom+0.0005,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1[v]\" \
	-map \"[v]\" -s \"1280x720\" %s" % (img, start_y_percent, d, d, video_path)

	# TESTING
	# cmd = FFMPEG_BIN + " -y -loop 1 -loglevel panic -i %s \
	# -filter_complex \
	# \"[0]zoompan=z='min(zoom+0.0015,1.5)':d=%.2f:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)[v]\" \
	# -map \"[v]\" -c:v libx264 -pix_fmt yuv420p -s \"1280x720\" %s" % (img, d, video_path)
	
	try:
		result = check_output(cmd, shell=True,stderr=subprocess.STDOUT)
		return {'statusCode': 200, 'video_path':video_path}
	except subprocess.CalledProcessError as e:
		print('Error running FFMPEG')
		print(json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output}))
		return {
	        'statusCode': 400,
	        'error': e
	        # 'body': json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output})
	    }