#============================================================
#
# CatAndCastle LLC, 2018
#============================================================
import src.face_detect as FaceDetect
import json

def handler(event, context):
	img_url = event.get('queryStringParameters', {}).get('img')
	# img_url = "https://s3.amazonaws.com/wellofmemories.catandcastle.com/resources/1-babymiriam.jpg"

	roi, dimensions, focus = FaceDetect.detect(img_url)
	# if dimensions[1] > dimensions[0]:	
	# 	start_y_percent = repr(roi[1]/float(dimensions[1]))

	response = {
		'img': img_url,
		'roi': json.loads("[%i,%i,%i,%i]" % (roi[0], roi[1], roi[2], roi[3])),
		'dimensions': json.loads("[%i,%i]" % (dimensions[0], dimensions[1])),
		'focus': json.loads("[%i,%i]" % (focus[0], focus[1]))
	}
	# print json.dumps(response)
	return {
        'statusCode': 200,
        'body': json.dumps(response)
    }

# e = {"img": "https://s3.amazonaws.com/wellofmemories.catandcastle.com/resources/1-babymiriam.jpg"}
# handler(e, {})