import boto3
import json
import pickle


def gather_checklist_content(user_id):
    sqs = boto3.client("sqs")
    s3 = boto3.client("s3")
    checklist_queue = "https://sqs.us-east-1.amazonaws.com/554637451109/checklist-queue"
    bucket_name = "jingle-skill-bucket"
    response = sqs.receive_message(
        QueueUrl=checklist_queue,
        AttributeNames=['All'],
        MaxNumberOfMessages=1
    )
    if 'Messages' in response:
        message = response['Messages'][0]
        handle = message['ReceiptHandle']
        message_object = json.loads(message['Body'])
        if message_object['user_id'] == user_id or message_object['user_id'] == 'tmp':
            sqs.delete_message(
                QueueUrl=checklist_queue,
                ReceiptHandle=handle
            )
            s3.download_file(bucket_name, message_object['s3_file'], "/tmp/"+message_object['s3_file'].split("/")[1])
            s3.delete_object(
                Bucket=bucket_name,
                Key=message_object['s3_file']
            )
            checklist = pickle.load(open("/tmp/"+message_object['s3_file'].split("/")[1], "rb"))

            return checklist
    else:
        return []


def convert_checklist_to_speech_text(checklist):
    speech_text = "Found the following tasks,"
    for item in checklist:
        speech_text += " "+item['task_name']
        if len(item['end_date'])>0:
            speech_text += " due in "+item['rem_days']+", "
        else:
            speech_text += ", "
    return speech_text[:-2]