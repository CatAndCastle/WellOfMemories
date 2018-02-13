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
	
	def __init__(self, resource):
		self.filters = []
		self.comp = resource.comp
		self.data = {}
		self.duration = resource.comp.duration

		for key, value in resource.data.iteritems():
			self.set(key,value)

		# Bug Fix: fadeOut transitionOut needs to finish ~100ms before the end of the segment.
		# Else the element doesn't fade out completely
		if self.data["transitionOut"]=="fadeOut" and self.duration-self.data["transitionOutStart"]-self.data["transitionOutDuration"] < 0.1:
			self.data["transitionOutStart"] = max(0, self.data["transitionOutStart"]-0.1)

		self.buildStream()

	def set(self, key, value):
		# if key=="transitionInStart" or key=="transitionInDuration" or key=="transitionOutStart" or key=="transitionOutDuration":
		# 	self.data[key] = int(value)/float(1000)
		# elif key=="top" or key=="left" or key=="topStart" or key=="leftStart":
		# 	self.data[key] = int(value.strip('%'))/float(100)
		if key=="width":
			# or key=="left" or key=="leftStart":
			val = int(self.comp.width * value)
			# dimension must be divisible by 2 for ffmpeg
			val = math.floor(val/2) * 2
			self.data[key] = val
		elif key=="height":
			# or key=="top" or key=="topStart":
			val = int(self.comp.height * value)
			# dimension must be divisible by 2 for ffmpeg
			val = math.floor(val/2) * 2
			self.data[key] = val
		else:
			self.data[key] = value
	def buildStream(self):
		# resize resource
		if "width" in self.data and "height" in self.data:
			self.filters.append("scale=w='if(gte(iw,ih),%i,oh*a)':h='if(gt(ih,iw),%i,ow/a)'" % (self.data["width"], self.data["height"]) )
		elif "width" in self.data:
			self.filters.append("scale=w=%i:h=ow/a" % self.data["width"])
		elif "height" in self.data:
			self.filters.append("scale=h=%i:w=oh*a" % self.data["height"])

		# transition In
		if self.data["transitionIn"]=="fadeIn":
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
		self.filters.append("fade=in:st=%.2f:d=%.2f:alpha=1" % (0, self.data["transitionInDuration"]))
	def bloom(self):
		# bloom is a fade in with a moving overlay
		self.filters.append("fade=in:st=%.2f:d=%.2f:alpha=1" % (0, self.data["transitionInDuration"]))
	def fadeOut(self):
		self.filters.append("fade=out:st=%.2f:d=%.2f:alpha=1" % (self.data["transitionOutStart"]-self.data["transitionInStart"], self.data["transitionOutDuration"]))

def fadeInFromColor(start, duration, color):
	return "fade=in:st=%.2f:d=%.2f:c=%s" % (start, duration, color)

def fadeOutToColor(start, duration, color):
	return "fade=out:st=%.2f:d=%.2f:c=%s" % (start, duration, color)

def photoPanDown(start_y, duration):
	FRAME_RATE = 25
	filters = [
		"loop=%i:1:0,setpts=N/%i/TB[tmp]" % (duration*FRAME_RATE, FRAME_RATE),
		"[tmp]crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[tmp]",
		"[tmp]scale=-1:4000,crop=w=iw:h='min(iw*9/16,ih)':x=0:y='max((ih-oh)/6,%.2f*ih-((ih-oh)/6))+((t/%.2f)*(ih-oh)/6)',trim=duration=%.2f[tmp1]" % (start_y, duration, duration),
		"[tmp1]zoompan=z='min(pzoom+0.0005,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1"
	]
	# filters = [
	# 	"crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[tmp]",
	# 	"[tmp]zoompan=z='min(pzoom+0.0005,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1,trim=duration=%.2f" % duration
	# ]
	return ";".join(filters)

def photoPanUp(start_y, duration):
	FRAME_RATE = 25
	filters = [
		"loop=%i:1:0,setpts=N/%i/TB[tmp]" % (duration*FRAME_RATE, FRAME_RATE),
		"[tmp]crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[tmp]",
		"[tmp]scale=-1:4000,crop=w=iw:h='min(iw*9/16,ih)':x=0:y='%.2f*ih-((t/%.2f)*min(%.2f*ih,(ih-oh)/6))',trim=duration=%.2f[tmp1]" % (start_y, duration,start_y, duration),
		"[tmp1]zoompan=z='if(lte(pzoom,1.0),1.15,max(1.0,pzoom-0.0005))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1"
	]
	# filters = [
	# 	"crop=h=ih:w='if(gt(a,16/9),ih*16/9,iw)':y=0:x='if(gt(a,16/9),(ow-iw)/2,0)'[tmp]",
	# 	"[tmp]zoompan=z='if(lte(pzoom,1.0),1.15,max(1.0,pzoom-0.0005))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,setsar=sar=1:1,trim=duration=%.2f" % duration
	# ]
	return ";".join(filters)