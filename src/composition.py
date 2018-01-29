#============================================================
# composition.py
# AWS Lamdda Function
#
# CatAndCastle LLC, 2018
#============================================================
import os
import src.filters as filters
import src.resources as resources
import src.common as common

here = os.path.dirname(os.path.realpath(__file__))
FFMPEG_BIN = os.path.join(here, '../bin/ffmpeg')

class Composition:
	# Must render at a higher resolution to achieve smooth animations
	scale_factor = 3 

	def __init__(self, duration):
		self.duration = duration
		self.width = 1280*self.scale_factor
		self.height = 720*self.scale_factor

		self.inputs = ["-f lavfi -i color=white:%ix%i:d=%.2f" % (self.width, self.height, int(duration)/float(1000))]
		self.filters = ["[0]setpts=PTS-STARTPTS[v0]"]
		# self.streams = []
		# self.overlays = []

	def addResource(self, resource_data):
		resource = resources.resource(resource_data, self)

		if resource.shouldLoop:
			stream_idx = self.addInput("-loop 1 -i %s" % resource.path)
		else:
			stream_idx = self.addInput("-i %s" % resource.path)
		# stream_idx = self.addInput("-loop 1 -framerate 30 -i %s" % resource.path)
		stream_id = 10*stream_idx

		streamF, overlayF = resource.build()

		self.filters.append("[%i]%s[v%i]" % (stream_idx, streamF, stream_id+1))
		self.filters.append("[v%i][v%i]%s[v%i]" % (stream_idx-1, stream_id+1, overlayF, stream_idx))
		
	def render(self):
		# print(self.inputs)
		# print(self.streams)
		# print(self.overlays)
		video_path = '/tmp/video-' + common.randomString(10) + '.mp4'
		cmd = FFMPEG_BIN + " %s -filter_complex \"%s\" -map \"[v%i]\" -pix_fmt yuv420p -s 1280x720 -y %s" % (" ".join(self.inputs), ";".join(self.filters), len(self.inputs)-1, video_path)
		print cmd
		res = common.executeCmd(cmd)
		if res["error"] is True:
			return {
		        'statusCode': 400,
		        'error': res["body"]
		    }
		else:
			return {'statusCode': 200, 'video_path':video_path}

	def addInput(self, input_str):
		self.inputs.append(input_str)
		return len(self.inputs)-1



