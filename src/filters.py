#============================================================
# filters.py
# 
# Transition types:
# bloom, wipeLeftToRight, fadeIn
#
# duration and delay expected in milliseconds
# color: #hex, or "black", "white", etc
#
# CatAndCastle LLC, 2018
#============================================================
import math

class ComplexFilter:
	defaults={
		"transitionIn": "immediate",
		"transitionInStart": 0,
		"transitionInDuration": 300,
		"transitionOut": "immediate",
		"transitionOutStart": 1000,
		"transitionOutDuration": 300,
		"top": "50%",
		"left": "50%",
		"topStart":"50%",
		"leftStart":"50%"
	}
	def __init__(self, resource):
		self.filters = []
		self.comp = resource.comp
		self.data = {}
		for key, value in self.defaults.iteritems():
			self.set(key,value)
		self.set("transitionOutStart",resource.comp.duration) #default to being onscreen for the whole duration
		self.duration = int(resource.comp.duration)/float(1000)
		# print "DURATION = %f" % self.duration
		# print "INPUT DURATION = %i" % resource.comp.duration
		for key, value in resource.data.iteritems():
			self.set(key,value)

		# Bug Fix: fadeOut transitionOut needs to finish ~100ms before the end of the segment.
		# Else the element doesn't fade out completely
		if self.data["transitionOut"]=="fadeOut" and self.duration-self.data["transitionOutStart"]-self.data["transitionOutDuration"] < 0.1:
			self.data["transitionOutStart"] = max(0, self.data["transitionOutStart"]-0.1)

		self.buildStream()

	def set(self, key, value):
		if key=="transitionInStart" or key=="transitionInDuration" or key=="transitionOutStart" or key=="transitionOutDuration":
			self.data[key] = int(value)/float(1000)
		elif key=="top" or key=="left" or key=="topStart" or key=="leftStart":
			self.data[key] = int(value.strip('%'))/float(100)
		elif key=="width" or key=="left" or key=="leftStart":
			val = int(self.comp.width * int(value.strip('%'))/float(100))
			# must be divisible by 2 for ffmpeg
			val = math.floor(val/2) * 2
			self.data[key] = val
		elif key=="height" or key=="top" or key=="topStart":
			val = int(self.comp.height * int(value.strip('%'))/float(100))
			# must be divisible by 2 for ffmpeg
			val = math.floor(val/2) * 2
			self.data[key] = val
		else:
			self.data[key] = value
	def buildStream(self):
		# size
		if "width" in self.data and "height" in self.data:
			self.filters.append("scale=w='if(gte(iw,ih),%i,oh*a)':h='if(gt(ih,iw),%i,ow/a)'" % (self.data["width"], self.data["height"]) )
		elif "width" in self.data:
			self.filters.append("scale=w=%i:h=ow/a" % self.data["width"])
		elif "height" in self.data:
			self.filters.append("scale=h=%i:w=oh*a" % self.data["height"])

		# transition In
		if self.data["transitionIn"]=="fadeIn" or self.data["transitionIn"]=="immediate":
			self.fadeIn()
		elif self.data["transitionIn"]=="bloom":
			self.bloom()

		# transition Out
		if self.data["transitionOut"]=="fadeOut":
			self.fadeOut()

		# final filters
		self.filters.append("trim=duration=%.2f" % self.duration )
		if self.data["transitionInStart"] < 1:
			self.filters.append("setpts=PTS-STARTPTS")
		else:
			self.filters.append("setpts=PTS+%i/TB" % math.floor(self.data["transitionInStart"]))
			
		

	def stream(self):
		return ",".join(self.filters)

	# FILTERS
	def overlay(self):
		if self.data["transitionIn"]=="bloom":
			xpos = "if(gte(t,%.2f),W*%.2f-w/2,(-w/2)+%.2f*W+((t-%.2f)/%.2f)*W*%.2f)" % (self.data["transitionInStart"]+self.data["transitionInDuration"], self.data["left"], self.data["leftStart"], self.data["transitionInStart"], self.data["transitionInDuration"], self.data["left"]-self.data["leftStart"])
			ypos = "if(gte(t,%.2f),H*%.2f-h/2,(-h/2)+H*%.2f+((t-%.2f)/%.2f)*H*%.2f)" % (self.data["transitionInStart"]+self.data["transitionInDuration"], self.data["top"], self.data["topStart"], self.data["transitionInStart"], self.data["transitionInDuration"], self.data["top"]-self.data["topStart"])
			return "overlay=x='%s':y='%s':format=yuv444:shortest=1:eof_action=pass" % (xpos, ypos)
		else:
			return "overlay=x='W*%.2f-w/2':y='H*%.2f-h/2':shortest=1:eof_action=pass,trim=duration=%.2f" % (self.data["left"], self.data["top"], self.duration)
	def fadeIn(self):
		self.filters.append("fade=in:st=%.2f:d=%.2f:c=%s" % (0, self.data["transitionInDuration"], "white"))
	def bloom(self):
		# bloom is a fade in with a moving overlay
		self.filters.append("fade=in:st=%.2f:d=%.2f:c=%s" % (0, self.data["transitionInDuration"], "white"))
		# return "fade=in:st=%.2f:d=%.2f:c=" % (start/float(1000), duration/float(1000), color)
	def fadeOut(self):
		self.filters.append("fade=out:st=%.2f:d=%.2f:c=%s" % (self.data["transitionOutStart"]-self.data["transitionInStart"], self.data["transitionOutDuration"], "white"))
	# def wipeLeftToRight(self):
		# fade in 
		# sid = common.randomString(3)
		# self.filters.append("fade=in:st=%.2f:d=%.2f:c=%s[%s]" % (0, 300, "white", sid))
		# and wipe
# ffmpeg -loop 1 -i /tmp/text-5QZQQI2LG0.jpg -i assets/white_mask.png \
# -filter_complex "\
# [0]scale=w=trunc(iw/2)*2:h=trunc(ih/2)*2[v];\
# [1][v]scale2ref[c1][v1];\
# [v1][c1]overlay=x='(t/3)*W':y='(H-h)/2',trim=duration=5,setpts=PTS-STARTPTS[vf]" \
# -map "[vf]" -pix_fmt yuv420p -y wipe.mp4
	# def wipeLeftToRight(self):

# ffmpeg -loop 1 -i title.jpg -filter_complex "fade=in:st=1:d=1:c=white,fade=out:st=3:d=1:c=white,trim=duration=5,setpts=PTS-STARTPTS" -pix_fmt yuv420p -y loop.mp4