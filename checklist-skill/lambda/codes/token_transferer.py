import boto3


def send_token(filename):
    s3 = boto3.client("s3")
    s3.upload_file(filename, "jingle-skill-bucket", "tokens/"+filename)
