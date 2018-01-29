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
import src.animate as Animate


def resource(data, composition):
	if data["resourceType"] == "graphic":
		return GraphicResource(data, composition)
	elif data["resourceType"] == "text":
		return TextResource(data, composition)

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
		self.path = '/tmp/text-' + common.randomString(10) + '.jpg'
		label_cmd = "./render_label.sh \"%s\" \"%s\" \"%s\" \"%s\" %i \"%s\"" % (self.data['text'], f.ttf, self.data['color'], int(self.data['fontSize'].strip('px'))*self.comp.scale_factor, self.data['kerning'], self.path)
		
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
				resource_cmd = "./render_wipe.sh \"%s\" \"%.2f\" \"%.2f\" \"%s\"" % (self.path, self.data['transitionInDuration']/float(1000), self.comp.duration/float(1000), self.new_path)
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

class PhotoResource:
	def __init__(self, data):
		self.data = data
	def render(self):
		# DOWNLOAD IMAGE
		self.path = '/tmp/photo-' + common.randomString(10)
		urllib.urlretrieve(self.data["resourceUrl"], self.path)

		res = Animate.animatePhoto(self.path, self.data["animation"], int(self.data["duration"])/float(1000));
		return res
