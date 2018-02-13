#============================================================
# composition.py
# Composition may contain multiple resources (layers)
#
# CatAndCastle LLC, 2018
#============================================================
import os
import src.filters as filters
import src.resources as resources
import src.common as common


class Composition:
	# Must render at a higher resolution to achieve smooth animations
	scale_factor = 4 

	def __init__(self, data):
		self.duration = data["duration"]
		self.data = data
		self.width = 1280*self.scale_factor
		self.height = 720*self.scale_factor

		self.inputs = ["-f lavfi -i color=white:%ix%i:d=%.2f" % (self.width, self.height, data["duration"])]
		self.filters = ["[0]setpts=PTS-STARTPTS[comp]"]

	def addResource(self, resource_data):
		resource = resources.resource(resource_data, self)

		if resource.shouldLoop:
			stream_idx = self.addInput("-loop 1 -i %s" % resource.path)
		else:
			stream_idx = self.addInput("-i %s" % resource.path)
		stream_id = 10*stream_idx

		streamF, overlayF = resource.build()

		self.filters.append("[%i]%s[v%i]" % (stream_idx, streamF, stream_id+1))
		self.filters.append("[comp][v%i]%s[comp]" % (stream_id+1, overlayF))
		
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
			self.filters.append("[comp]%s[comp]" % ",".join(transiton_filters))

	def render(self):
		self.addEffects()
		
		video_path = '/tmp/video-' + common.randomString(10) + '.mp4'
		# cmd = FFMPEG_BIN + " %s -filter_complex \"%s\" -map \"[v%i]\" -pix_fmt yuv420p -s 1280x720 -y %s" % (" ".join(self.inputs), ";".join(self.filters), len(self.inputs)-1, video_path)
		cmd = [
			common.FFMPEG_BIN,
			" ".join(self.inputs),
			"-filter_complex \"%s\"" % ";".join(self.filters),
			"-map \"[comp]\"",
			"-pix_fmt yuv420p -s 1280x720 -y %s" % video_path
		]
		
		res = common.executeCmd(" ".join(cmd))
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

# class ConcatenateComposition:
# 	def __init__(self, size):
# 		self.inputs = []
# 		self.filters = []
# 		self.concat = ["[v001]"]
# 		self.idx = 0
# 		self.size = size
# 		self.duration = 0

# 	def appendSegment(self, data):
# 		# Get segment duration and transition duration
# 		# (Default to a 2 second transition between segments)
# 		SLIDE_T = int(data['duration'])/float(1000)
# 		if 'transitionOutDuration' in data:
# 			TRANSITION_T = int(data['transitionOutDuration'])/float(1000)
# 		else:
# 			TRANSITION_T = 2.0

# 		if 'transitionInStart' not in data:
# 			data['transitionInStart'] = 0
# 		if 'transitionOutStart' not in data:
# 			data['transitionOutStart'] = data['duration'] - data['transitionOutDuration']

# 		self.inputs.append("-i %s" % data["renderedUrl"])

# 		#
# 		# Take care of fadeIn/Out transitions
# 		#
# 		transitionInFilter = ""
# 		transitionOutFilter = ""
# 		if "transitionIn" in data and (data["transitionIn"]=="fadeIn" or data["transitionIn"]=="fadeFromColor"):
# 			 transitionInFilter = ","+filters.fadeInFromColor(int(data['transitionInStart'])/float(1000), int(data['transitionInDuration'])/float(1000), data['transitionInColor'])
# 		if "transitionOut" in data and (data["transitionOut"]=="fadeOut" or data["transitionOut"]=="fadeToColor"):
# 			 transitionOutFilter = ","+filters.fadeOutToColor(int(data['transitionOutStart'])/float(1000), int(data['transitionOutDuration'])/float(1000), data['transitionOutColor'])
		
# 		#
# 		# Here we are splitting up each segment into 2 parts:
# 		# part_1: t = 0 -> (duration - transition_duration)
# 		# part_2: t = (end - transition_duration) -> end
# 		# We apply a transition effect o part_2, combined with part_1 of the next segment, and then concatenate all the parts together
# 		#
# 		self.filters.append("[%i:v]scale=1280:720%s%s[v%i];[v%i]split[v%i00][v%i10];" % (self.idx,transitionInFilter,transitionOutFilter,self.idx,self.idx,self.idx,self.idx))
# 		self.filters.append("[v%i00]trim=0:%.2f[v%i01];[v%i10]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v%i11t];" 
# 			% (self.idx,SLIDE_T-TRANSITION_T,self.idx,self.idx,SLIDE_T-TRANSITION_T,SLIDE_T,self.idx))
		
# 		#
# 		# Applying crossfade transitions.
# 		# Check here for transition options:
# 		# https://github.com/transitive-bullshit/ffmpeg-gl-transition
# 		#
# 		if "transitionOut" in data and data["transitionOut"]=="fadeOutOverNext":
# 			self.duration += SLIDE_T-TRANSITION_T
			
# 			# self.filters.append("[v%i11][v%i01]gltransition=duration=%.2f[vt%i];" % (self.idx,self.idx+1,TRANSITION_T,self.idx))
# 			self.filters.append("[v%i11t]fade=out:st=0:d=%.2f:alpha=1[v%i11];" % (self.idx,TRANSITION_T,self.idx))
# 			self.filters.append("[v%i01][v%i11]overlay=x=0:y=0:eof_action=pass[vt%i];" % (self.idx+1,self.idx,self.idx))
# 			self.concat.append("[vt%i]" % self.idx)
# 		else:
# 			# Default to 'immediate' transition between segments
# 			self.duration += SLIDE_T
# 			if(self.idx < self.size-1):
# 				self.filters.append("[v%i11t][v%i01]concat=n=2[vt%i];" % (self.idx,self.idx+1,self.idx))
# 				self.concat.append("[vt%i]" % self.idx)
# 			else:
# 				self.concat.append("[v%i11t]" % self.idx)

# 		self.idx += 1

# 	def render(self, destination):
# 		self.concat.append("concat=n=%i[outv]" % (self.size+1))
# 		self.video = destination
# 		cmd = [
# 			FFMPEG_BIN,
# 			" ".join(self.inputs),
# 			"-filter_complex \"" + "".join(self.filters) + "".join(self.concat) + "\"",
# 			"-map \"[outv]\"",
# 			"-c:v libx264 -profile:v baseline -preset slow -movflags faststart -pix_fmt yuv420p",
# 			"-y " + destination
# 		]
# 		print " ".join(cmd)
# 		return common.executeCmd(" ".join(cmd))

# 	def addAudio(self, audio_file, destination):
# 		cmd = "%s -i %s -i %s -c:v copy -c:a aac -t %.2f -y %s" % (FFMPEG_BIN, self.video, audio_file, self.duration, destination)
# 		print cmd
# 		return common.executeCmd(cmd)


