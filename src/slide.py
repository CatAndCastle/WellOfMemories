#============================================================
# slide.py
#
# CatAndCastle LLC, 2018
#============================================================
import json,os
from src.resources import PhotoResource
import src.common as common
from src.composition import Composition
import boto3
from botocore.exceptions import ClientError

class Slide:
	def __init__(self, data):
		self.data = data

	def render(self):
		if self.data["slideType"]=="sectionHeader":
			comp = Composition(self.data["duration"])
			layers = self.data["layers"]
			for layer in layers:
				comp.addResource(layer)
			
			res = comp.render()

			# Upload file to s3
			if res["statusCode"] == 200:
				self.upload(res["video_path"])
			else:
				print("ERROR Rendering sectionHeader")
				print(json.dumps(res["error"]))
		
		elif self.data["slideType"]=="photo":
			photo = PhotoResource(self.data)
			res = photo.render()

			# Upload file to s3
			if res["statusCode"] == 200:
				self.upload(res["video_path"])
			else:
				print("ERROR Rendering Slide")
				print(json.dumps(res["error"]))

	def upload(self, FILE):
		KEY = 'renders/'+self.data['id']+'.mp4'
		data = open(FILE, 'rb')
		s3 = boto3.resource('s3')
		s3.Bucket(os.environ['S3_BUCKET']).put_object(Key=KEY, Body=data, ACL='public-read', ContentType='video/mp4')
		return "https://s3.amazonaws.com/"+os.environ['S3_BUCKET']+"/" + KEY

	def savetoDynamo(self):
		# Save slide transition info with slide mp4 url string
		print("save slide data to dynamodb")