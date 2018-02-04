#============================================================
# resources.py
# 
#
# CatAndCastle LLC, 2018
#============================================================

import urllib, os, json
from src.font import Font
import src.common as common
import boto3
import subprocess
from subprocess import call,check_output
from src.filters import ComplexFilter
import src.filters as filters
import src.face_detect as FaceDetect

FFMPEG_BIN = os.environ['LAMBDA_TASK_ROOT']+'/bin/ffmpeg'
# FFMPEG_BIN = "ffmpeg"

def resource(data, composition):
	if 'resourceType' in data and data["resourceType"] == "graphic":
		return GraphicResource(data, composition)
	elif 'resourceType' in data and data["resourceType"] == "text":
		return TextResource(data, composition)
	elif 'slideType' in data and data["slideType"] == "photo":
		return PhotoResource(data, composition)

class Resource:
	def __init__(self, data, composition):
		self.data = data
		self.comp = composition
		self.shouldLoop = True

	def build(self):
		f = ComplexFilter(self)
		return f.stream(), f.overlay()

class GraphicResource(Resource):
	def __init__(self, data, composition):
		Resource.__init__(self, data, composition)
		self.create()
	def create(self):
		# DOWNLOAD IMAGE
		print("downloading image from " + self.data['resourceUrl'])
		self.download()
		print("downloaded to " + self.path)

	def download(self):
		self.path = '/tmp/graphic-' + common.randomString(10)
		urllib.urlretrieve(self.data['resourceUrl'], self.path)
	
	def upload(self):
		data = open(self.path, 'rb')
		s3 = boto3.resource('s3')
		s3.Bucket(os.environ['S3_BUCKET']).put_object(Key="graphicResourceTest", Body=data, ACL='public-read', ContentType='image/png')

class TextResource(Resource):
	def __init__(self, data, composition):
		Resource.__init__(self, data, composition)
		self.create()
	def create(self):
		# DOWNLOAD FONT
		f = Font(self.data['resourceUrl'])
		
		# RENDER TEXT JPG WITH IMAGICK
		self.path = '/tmp/text-' + common.randomString(10) + '.png'
		label_cmd = "./render_label.sh \"%s\" \"%s\" \"%s\" \"%s\" %i \"%s\"" % (self.data['text'], f.ttf, self.data['color'], self.data['fontSize']*self.comp.scale_factor, self.data['kerning'], self.path)
		
		res = common.executeCmd(label_cmd)
		if res["error"] is True:
			print('Error running IMAGEMAGIK')
			print(json.dumps({'command': res["body"].cmd, "code":res["body"].returncode, "error_output":res["body"].output}))
			# return {
		 #        'statusCode': 400,
		 #        'error': res["body"]
		 #    }
		else:
			if self.data['transitionIn']=='wipeLeftToRight':
				self.new_path = '/tmp/resource-' + common.randomString(10) + '.mp4'
				resource_cmd = "./render_wipe.sh \"%s\" \"%.2f\" \"%.2f\" \"%s\"" % (self.path, self.data['transitionInDuration'], self.comp.duration, self.new_path)
				common.executeCmd(resource_cmd)

				self.path = self.new_path
				self.data["transitionIn"] = "immediate"
				self.data["transitionInDuration"] = 0
				self.shouldLoop = False
			

			# return {'statusCode': 200, 'video_path':video_path}

	def upload(self):
		data = open(self.path, 'rb')
		s3 = boto3.resource('s3')
		s3.Bucket(os.environ['S3_BUCKET']).put_object(Key="textResourceTest", Body=data, ACL='public-read', ContentType='image/jpg')

class PhotoResource(Resource):
	def __init__(self, data, composition):
		Resource.__init__(self, data, composition)
		self.create()
		self.vf = []
	# def __init__(self, data):
	# 	self.data = data
	def create(self):
		# DOWNLOAD IMAGE
		self.path = '/tmp/photo-' + common.randomString(10)
		urllib.urlretrieve(self.data["resourceUrl"], self.path)

		# convert to jpg - need this step to make sure the images are encoded correctrly
		# Without this step getting glitches in the rendered videos
		encode="%s -i %s -pix_fmt yuvj420p -y %s" % (FFMPEG_BIN, self.path, self.path+'.jpg')
		res = common.executeCmd(encode)
		self.path = self.path+'.jpg'

	def addEffects(self):
		transiton_filters = [];
		if "transitionIn" in self.data:
			if self.data["transitionIn"]=="fadeIn":
				transiton_filters.append(filters.fadeInFromColor(self.data["transitionInStart"], self.data["transitionInDuration"], 'black'))
			elif self.data["transitionIn"]=="fadeFromColor":
				transiton_filters.append(filters.fadeInFromColor(self.data["transitionInStart"], self.data["transitionInDuration"], self.data["transitionInColor"]))
		if "transitionOut" in self.data:
			if self.data["transitionOut"]=="fadeOut":
				transiton_filters.append(filters.fadeOutToColor(self.data["transitionOutStart"], self.data["transitionOutDuration"], 'black'))
			elif self.data["transitionOut"]=="fadeToColor":
				transiton_filters.append(filters.fadeOutToColor(self.data["transitionOutStart"], self.data["transitionOutDuration"], self.data["transitionOutColor"]))

		if len(transiton_filters)>0:
			self.vf.append("[animated]%s[animated]" % ",".join(transiton_filters))

	def render(self):
		# FACE DETECTION
		roi, dimensions, focus = FaceDetect.detect(self.path)
		start_y_percent = 0.00
		if dimensions[1] > dimensions[0]:
			start_y_percent = roi[1]/float(dimensions[1])
		# start_y_percent = 0.50

		# Animate Photo
		vf = []
		if self.data["animation"] == "panup":
			f = filters.photoPanUp(start_y_percent, self.data["duration"])
			self.vf.append("[0:v]%s[animated]" % f)
		elif self.data["animation"] == "pandown":
			f = filters.photoPanDown(start_y_percent, self.data["duration"])
			self.vf.append("[0:v]%s[animated]" % f)

		self.addEffects()

		video_path = '/tmp/video-' + common.randomString(10) + '.mp4'
		cmd = [
			FFMPEG_BIN,
			"-y -loop 1 -i %s" % self.path,
			"-filter_complex \"%s\"" % ";".join(self.vf),
			"-map \"[animated]\"",
			"-pix_fmt yuv420p -s 1280x720 -y %s" % video_path
		]
		
		res = common.executeCmd(" ".join(cmd))
		if res["error"] is True:
			return {'statusCode': 400,'error': res["body"]}
		else:
			return {'statusCode': 200, 'video_path':video_path}


		# res = Animate.animatePhoto(self.path, self.data["animation"], self.data["duration"]);
		# return res
