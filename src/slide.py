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

class SlideRenderDurationError(Exception):
    pass
class SlideRenderError(Exception):
    pass

class Slide:

	def __init__(self, data):
		self.data = data
		self.error = False

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
			duration = common.checkVideoDuration(res["video_path"])
			print "Slide duration = %i" % duration
			url = common.uploadS3(res["video_path"], "%s/slide_%s.mp4" % (self.data['project_id'],self.data['idx']))
			self.data["renderedUrl"] = url

			# Handling Lambda bug.
			# Sometimes lambda does not render the full video. This is inconsistent Lambda behavior
			if duration == self.data["duration"]:
				common.saveToDynamo(
					{'id': self.data["project_id"],
					'item': "slide_%03d" % self.data["idx"],
					'slideData': self.data
					})
			else:
				# record error
				self.error = True
				self.data["duration_rendered"] = duration
				common.saveToDynamo(
					{'id': self.data["project_id"],
					'item': "error_%03d" % self.data["idx"],
					'slideData': self.data,
					'msg': "could not render full slide"
					})

				raise SlideRenderDurationError({"rendered_duration":duration})

		else:
			# record error
			self.error = True
			self.data["duration_rendered"] = duration
			common.saveToDynamo(
				{'id': self.data["project_id"],
				'item': "error_%03d" % self.data["idx"],
				'slideData': self.data,
				'msg': "error rendering slide"
				})

			raise SlideRenderError(res["error"])