import os,json

defaults_file = os.environ['LAMBDA_TASK_ROOT']+'/assets/defaults.json'
defaults = json.load(open(defaults_file))

def parse(event):
	validate(event, defaults["event"])
	# print(json.dumps(event, indent=4))

def validate(data, paramsDict):
	parsed = data
	for key, obj in paramsDict.iteritems():
		# missing parameter
		if key not in data and not obj["optional"]:
			raise ValueError({"msg": "Missing input parameter '%s'" % key, "data":data})
		# invalid parameter
		if key in data and 'allowed' in obj and data[key] not in obj['allowed']:
			raise ValueError({"msg": "Invalid value for '%s'." % key, "expected_values":obj['allowed'], "data":data})
		elif key in data and 'allowed' in obj and data[key] in obj:
			# print "validating {}".format(data[key])
			validate(data, obj[data[key]])

		# unable to parse parameter
		if key in data and 'eval' in obj:
			try:
				parsed[key] = eval(obj['eval'].format(data[key]))
			except TypeError as e:
				# print e
				raise ValueError({"msg": "Invalid value for '%s'. %s" % (key,obj['description']), "data":data})
			except ValueError as e:
				# print e
				raise ValueError({"msg": "Invalid value for '%s'. %s" % (key,obj['description']), "data":data})
		
		elif key in data:
			parsed[key] = data[key]

		elif key not in data and 'default' in obj:
			parsed[key] = obj['default']

	if 'slides' in data:
		for slide in data['slides']:
			if 'parsed' not in slide:
				validate(slide, defaults["slides"])
	if 'layers' in data:
		for layer in data['layers']:
			if 'parsed' not in layer:
				validate(layer, defaults["layers"])

	parsed['parsed'] = True
	return parsed
		