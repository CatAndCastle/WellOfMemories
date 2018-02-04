import os,string,random,urllib2,urllib,decimal
import boto3
from botocore.exceptions import ClientError
import subprocess, json
from subprocess import call,check_output
from decimal import *

dynamodb = boto3.resource('dynamodb')
TABLE = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
		return super(DecimalEncoder, self).default(o)

def replace_decimals(obj):
	if isinstance(obj, list):
		for i in xrange(len(obj)):
			obj[i] = replace_decimals(obj[i])
		return obj
	elif isinstance(obj, dict):
	    for k in obj.iterkeys():
	        obj[k] = replace_decimals(obj[k])
	    return obj
	elif isinstance(obj, float):
		return Decimal("{}".format(obj))
	else:
	    return obj


def randomString(size=10, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def uploadS3(FILE, KEY):
	data = open(FILE, 'rb')
	s3 = boto3.resource('s3')
	s3.Bucket(os.environ['S3_BUCKET']).put_object(Key=KEY, Body=data, ACL='public-read', ContentType='video/mp4')
	return "https://s3.amazonaws.com/"+os.environ['S3_BUCKET']+"/" + KEY

def deleteFromS3(prefix):
	s3 = boto3.resource('s3')
	bucket = s3.Bucket(os.environ['S3_BUCKET'])

	objects_to_delete = []
	for obj in bucket.objects.filter(Prefix=prefix):
	    objects_to_delete.append({'Key': obj.key})

	bucket.delete_objects(
	    Delete={
	        'Objects': objects_to_delete
	    }
	)

def downloadFile(url, prefix, ext):
		path = '/tmp/%s-%s.%s' % (prefix, randomString(10), ext)
		urllib.urlretrieve(url, path)
		return path

def executeCmd(cmd):
	print(cmd)
	try:
		result = check_output(cmd, shell=True,stderr=subprocess.STDOUT)
		return {'error': False, 'result':result}
	except subprocess.CalledProcessError as e:
		print('Error executing subprocess command')
		print(json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output}))
		return {
	        'error': True,
	        'body': e
	        # 'body': json.dumps({'command': e.cmd, "code":e.returncode, "error_output":e.output})
	    }

def saveToDynamo(itemData):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

	try:
		table.put_item(Item=replace_decimals(itemData))
		return {"error":False}
	except ClientError as e:
		print("saveSlideToDynamo failed:")
		print(json.dumps(e.response))
		return {"error":True, "body":e.response}

def invokeLambda(function_name, payload):
	lambda_client = boto3.client('lambda')
	response = lambda_client.invoke(
	    FunctionName=function_name,
	    InvocationType='Event', 
	    Payload=json.dumps(payload),
	)

def cleanup():
	call('rm -rf /tmp/*', shell=True)

def decrementCounter(project_id, item):
	
	current = readCounter(project_id, item)

	print("Attempting conditional update...")
	try:
		response = TABLE.update_item(
			Key={
				'id': project_id,
				'item':item
			},
			UpdateExpression="SET num = num - :incr",
			ConditionExpression="num = :current",
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
			return decrementCounter(project_id, item)
		else:
			raise
	else:
		print("UpdateItem succeeded:")
		print(json.dumps(response, indent=4, cls=DecimalEncoder))
		return response["Attributes"]["num"]

def readCounter(project_id, item):
	try:
		response = TABLE.get_item(
			Key={
				'id': project_id,
				'item':item
			}
		)
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		item = response['Item']
		print("GetItem succeeded:")
		print(json.dumps(item, indent=4, cls=DecimalEncoder))
		return item['num']
