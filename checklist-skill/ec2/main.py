# check for token in s3
# if yes, try use it to get emails, except pickle approach
# if not pickle approach
# use summarizer code to get summaries
# get checklist created and pushed into sqs

import json
import os

import boto3
import pickle
import httplib2
from gmail_reader import get_emails
from featureUpdates import get_mail_end_date
from checklist_creator import get_checklist_objects
from googleapiclient.discovery import build
from oauth2client.client import AccessTokenCredentials
from transformers import T5Tokenizer, T5ForConditionalGeneration


def get_tokens_from_s3():
    bucket_name = "jingle-skill-bucket"
    s3 = boto3.client("s3")
    response = s3.list_objects(
        Bucket=bucket_name,
        MaxKeys=100,
        Prefix="tokens"
    )
    if 'Contents' in response:
        cnt = 0
        for content in response['Contents']:
            name = content['Key']
            try:
                s3.download_file(bucket_name, name, 'tokens/'+name)
                cnt += 1
            except:
                pass
        if cnt > 0:
            return True
        else:
            return False


def get_pickle_email(last_seen_id):
    if last_seen_id is None:
        last_seen_id = 1
        all_emails = pickle.load(open("mailObjectPickle_" + str(last_seen_id) + ".pkl", "rb"))
        return last_seen_id, all_emails
    elif last_seen_id == 1:
        last_seen_id += 1
        all_emails = pickle.load(open("mailObjectPickle_" + str(last_seen_id) + ".pkl", "rb"))
        return last_seen_id, all_emails
    else:
        return last_seen_id, []


def summarize_body(all_emails):
    for i in range(len(all_emails)):
        try:
            model = T5ForConditionalGeneration.from_pretrained('t5-small')
            tokenizer = T5Tokenizer.from_pretrained('t5-small')

            preprocess_text = all_emails[i]['body'].strip().replace("\n", "")
            t5_prepared_text = "summarize: " + preprocess_text
            tokenized_text = tokenizer.encode(t5_prepared_text, return_tensors="pt").to('cpu')
            summary_ids = model.generate(tokenized_text,
                                         num_beams=4,
                                         no_repeat_ngram_size=2,
                                         min_length=30,
                                         max_length=100,
                                         early_stopping=True)

            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        except:
            summary = ""

        all_emails[i]['summary'] = summary

    return all_emails


def end_date_getter(all_emails):
    for mail in all_emails:
        date, days = get_mail_end_date(mail['body'])
        if date is not None:
            mail['end_date'] = str(date)
            mail['rem_days'] = str(days)
        else:
            mail['end_date'] = ""
            mail['rem_days'] = ""

    return all_emails


def email_getter(last_seen_id):
    if get_tokens_from_s3():
        for file in os.listdir("tokens"):
            try:
                access_token = pickle.load(open(file, "rb"))
                credentials = AccessTokenCredentials(access_token, 'alexa-skill/1.0')
                http = credentials.authorize(httplib2.Http())
                service = build('gmail', 'v1', http=http)
                last_seen_id, all_emails = get_emails(last_seen_id, service)
            except:
                pass
    else:
        last_seen_id, all_emails = get_pickle_email(last_seen_id)

    all_emails = summarize_body(all_emails)
    print(all_mails)
    all_emails = end_date_getter(all_emails)

    return last_seen_id, all_emails


def write_checklist(checklist):
    if len(checklist) > 0:
        sqs = boto3.client("sqs")
        checklist_queue = "https://sqs.us-east-1.amazonaws.com/554637451109/checklist-queue"
        resp = sqs.send_message(
            QueueUrl=checklist_queue,
            MessageBody=json.dumps(checklist)
        )


if __name__ == "__main__":
    last_id = None
    while True:
        print("Getting emails if any")
        last_id, all_mails = email_getter(last_id)
        print("Converting to checklist")
        checklist = get_checklist_objects(all_mails)
        print("Writing to queue")
        write_checklist(checklist)
