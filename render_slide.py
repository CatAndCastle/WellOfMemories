#============================================================
# render_slide.py
# AWS Lamdda Function
#
# CatAndCastle LLC, 2018
#============================================================
import sys,os,json,urllib,decimal
import boto3
from botocore.exceptions import ClientError
from src.slide import Slide
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')
COUNTER_TABLE = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

here = os.path.dirname(os.path.realpath(__file__))
IMG_PATH = "/tmp/img.jpg"
VIDEO_PATH = "/tmp/slide.mp4"

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
		return super(DecimalEncoder, self).default(o)

def handler(event, context):
	log.debug("Received event {}".format(json.dumps(event)))
	message = json.loads(event['Records'][0]['Sns']['Message'])
	log.debug("Parsed message {}".format(message))

	proj_id = message["project_id"]

	s = Slide(message)
	s.render()
	
	# UPDATE COUNTER
	numSlidesLeft = updateCounter(proj_id)
	if numSlidesLeft == 0:
		# TODO: Send SNS to combine slides
		print("DONE WITH SLIDES ----> ")
		print("TODO: send to combine queue")

	return {
        'statusCode': 200,
        'body': json.dumps({"message": "OK"})
    }

def updateCounter(proj_id):
	current = readCounter(proj_id)

	print("Attempting conditional update...")
	try:
		response = COUNTER_TABLE.update_item(
			Key={
				'id': proj_id
			},
			UpdateExpression="SET numSlides = numSlides - :incr",
			ConditionExpression="numSlides = :current",
			ExpressionAttributeValues={
				':incr': decimal.Decimal(1),
				':current': current
			},
			ReturnValues="UPDATED_NEW"
		)
	except ClientError as e:
		print("UpdateItem failed:")
		# print(json.dumps(e.response, indent=4, cls=DecimalEncoder))
		if e.response['Error']['Code'] == "ConditionalCheckFailedException":
			print(e.response['Error']['Message'])
			# Retry
			return updateCounter(proj_id)
		else:
			raise
	else:
		print("UpdateItem succeeded:")
		print(json.dumps(response, indent=4, cls=DecimalEncoder))
		return response["Attributes"]["numSlides"]

def readCounter(proj_id):
	try:
		response = COUNTER_TABLE.get_item(
			Key={
				'id': proj_id
			}
		)
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		item = response['Item']
		print("GetItem succeeded:")
		print(json.dumps(item, indent=4, cls=DecimalEncoder))
		return item['numSlides']

# event = 
# {
# "id": "FirstSNSVideo"
# "resourceUrl": "https://s3.amazonaws.com/wellofmemories.catandcastle.com/resources/1-babymiriam.jpg",
# "duration": 5
# }
# res = handler(event, {})
# print res