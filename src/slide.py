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
			comp = Composition(self.data)
			layers = self.data["layers"]
			for layer in layers:
				comp.addResource(layer)
			
			res = comp.render()
			self.processRenderResult(res)

			
		elif self.data["slideType"]=="photo":
			# comp = Composition(self.data)
			
			photo = PhotoResource(self.data, None)
			res = photo.render()
			self.processRenderResult(res)


	def processRenderResult(self, res):
		if res["statusCode"] == 200:
			url = common.uploadS3(res["video_path"], "%s/slide_%s.mp4" % (self.data['project_id'],self.data['idx']))
			self.data["renderedUrl"] = url
			common.saveToDynamo(
				{'id': self.data["project_id"],
				'item': "slide_%03d" % self.data["idx"],
				'slideData': self.data
				})
		else:
			print("ERROR Rendering sectionHeader")
			print(json.dumps(res["error"]))