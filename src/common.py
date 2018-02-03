import os, string, random, urllib2,urllib
import boto3
from botocore.exceptions import ClientError
import subprocess, json
from subprocess import call,check_output

def randomString(size=10, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def uploadS3(FILE, KEY):
	data = open(FILE, 'rb')
	s3 = boto3.resource('s3')
	s3.Bucket(os.environ['S3_BUCKET']).put_object(Key=KEY, Body=data, ACL='public-read', ContentType='video/mp4')
	return "https://s3.amazonaws.com/"+os.environ['S3_BUCKET']+"/" + KEY

def downloadFile(url, prefix, ext):
		path = '/tmp/%s-%s.%s' % (prefix, randomString(10), ext)
		urllib.urlretrieve(url, path)
		return path

def executeCmd(cmd):
	print(cmd)
	try:
		result = check_output(cmd, shell=True,stderr=subprocess.STDOUT)
		return {'error': False, result:result}
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
		table.put_item(Item=itemData)
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

