from boto3.session import Session
from os import environ as env

ACCESS_KEY = env['MYS3ACCESS']
SECRET_KEY = env['MYS3SECRET']

session = Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
s3 = session.resource('s3')
seap = s3.Bucket('dedenbangkit')

for s3_file in seap.objects.all():
    print(s3_file.key)
