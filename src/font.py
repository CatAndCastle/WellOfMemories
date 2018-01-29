import os, urllib2, re
import src.common as common

class Font:
	def __init__(self, url):
		# print("initiate font")
		self.url = url
		# default to packaged font
		self.ttf = os.environ['LAMBDA_TASK_ROOT'] + "/assets/Bakerville.ttf"
		# try to download font
		self.download()
	def download(self):
		fontUrl = None
		try:
			data = urllib2.urlopen(self.url)
			for line in data: # files are iterable
				# print line
				m = re.search('url\((.+?)\)', line)
				if m:
					fontUrl = m.group(1)
		except urllib2.HTTPError, e:
			print('HTTPError = ' + str(e.code))
		except urllib2.URLError, e:
			print('URLError = ' + str(e.reason))
		except Exception:
			print('generic exception downloading font: ' + traceback.format_exc())
		
		# Download font file
		if fontUrl is not None:
			font_file_path = '/tmp/font-' + common.randomString(10) + '.ttf'
			response = urllib2.urlopen(fontUrl)
			f = open(font_file_path, 'w')
			f.write(response.read())
			f.close()
			self.ttf = font_file_path
