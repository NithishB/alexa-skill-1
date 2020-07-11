import boto3
import json


def gather_checklist_content():
    sqs = boto3.client("sqs")
    checklist_queue = "https://sqs.us-east-1.amazonaws.com/554637451109/checklist-queue"
    response = sqs.receive_message(
        QueueUrl=checklist_queue,
        AttributeNames=['All'],
        MaxNumberOfMessages=5,
        WaitTimeSeconds=5
    )
    if 'Messages' in response:
        message = response['Messages'][0]
        handle = message['ReceiptHandle']
        checklist = json.loads(message['Body'])
        sqs.delete_message(
            QueueUrl=checklist_queue,
            ReceiptHandle=handle
        )
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