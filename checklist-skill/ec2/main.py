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
from multiprocessing import Pool

'''
    Helper function that returns all the uuids (folders corresponding to each user that are named based on the uuids) present in the jingle-skill-bucket.
'''
def get_uuids_from_s3():
    bucket_name = "jingle-skill-bucket"
    s3 = boto3.client("s3")
    response = s3.list_objects(
        Bucket=bucket_name,
        MaxKeys=100,
        Prefix="data"   # Name of a folder in the bucket. All keys will have this as a prefix.
    )
    if 'Contents' in response:
        # Collect all the objects as a list.
        nameList = []
        # A JSON object.
        for content in response['Contents']:
            # This is the name of an object.
            # TODO: Refactor later?
            name = content['Key'].split('/')[1] # everything is listed as an object.
            nameList.append( name )
        
        print (nameList)
        return nameList

'''
    Helper function for pool workers.
'''
def executor (userId):
    bucket_name = "jingle-skill-bucket"
    s3 = boto3.client('s3')

    try:
        # Download the token.
        s3.download_file(bucket_name, 'data/'+str(userId)+'/token.pkl', "/tmp/"+str(userId)+'_token.pkl')

        # Read-in the access token.
        access_token = pickle.load(open("/tmp/"+str(userId)+'_token.pkl', "rb"))
        credentials = AccessTokenCredentials(access_token, 'alexa-skill/1.0')
        http = credentials.authorize(httplib2.Http())
        service = build('gmail', 'v1', http=http)

        try:       
            # Download the existing all_mails object and last_mail_id from the bucket if available.
            s3.download_file(bucket_name, 'data/'+str(userId)+'/all_mails.pkl', "/tmp/"+str(userId)+'_all_mails.pkl')
            s3.download_file(bucket_name, 'data/'+str(userId)+'/last_mail_id.pkl', "/tmp/"+str(userId)+'_last_mail_id.pkl')

            # Read-in both the files.
            all_mails = pickle.load(open("/tmp/"+str(userId)+'_all_mails.pkl', "rb"))
            last_mail_id = pickle.load(open("/tmp/"+str(userId)+'_last_mail_id.pkl', "rb"))
        except:
            # Read-in both the files.
            all_mails = None
            last_mail_id = None

        last_mail_id, all_mails = get_emails(last_mail_id, all_mails, service)

        checklist = []
        # Get the required information.    
        for i in all_mails:
            # Construct the summary for each mail object.
            all_mails[i] = summarize_body(all_mails[i])

            # Get the dates for the mail as well.
            all_mails[i] = end_date_getter(all_mails[i])

            # It keeps appending the new checklist tasks to the existing set of checklist tasks across all the sender_email tags.
            checklist = get_checklist_objects(all_mails[i], checklist)
        

        # Write items into the bucket, and notify SQS.
        write_checklist(checklist, last_mail_id, all_mails, userId)

        return 'Success!'
        
    except:
        return 'Failue!'

# def get_pickle_email(last_mail_id):
#     if last_mail_id is None:
#         last_mail_id = 1
#         all_emails = pickle.load(open("mailObjectPickle_" + str(last_mail_id) + ".pkl", "rb"))
#         return last_mail_id, all_emails
#     elif last_mail_id == 1:
#         last_mail_id += 1
#         all_emails = pickle.load(open("mailObjectPickle_" + str(last_mail_id) + ".pkl", "rb"))
#         return last_mail_id, all_emails
#     else:
#         return last_mail_id, []


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
    # all_emails : List ob.
    for mail in all_emails:
        deadline = get_mail_end_date(mail['body'])
        mail['end_date'] = str(deadline['date'])
        mail['rem_days'] = str(deadline['days'])

    return all_emails


# def email_getter(last_mail_id):
#     if get_tokens_from_s3():
#         for file in os.listdir("tokens"):
#             try:
#                 user_id = file.split("_")[0]
#                 access_token = pickle.load(open(file, "rb"))
#                 credentials = AccessTokenCredentials(access_token, 'alexa-skill/1.0')
#                 http = credentials.authorize(httplib2.Http())
#                 service = build('gmail', 'v1', http=http)
#                 last_mail_id, all_emails = get_emails(last_mail_id, service)
#             except:
#                 pass
#     else:
#         user_id = "tmp"
#         last_mail_id, all_emails = get_pickle_email(last_mail_id)

#     all_emails = summarize_body(all_emails)
#     all_emails = end_date_getter(all_emails)

#     return last_mail_id, all_emails, user_id


'''
    Write 3 things : CheckList, all_mails, last_mail_id, into the S3.
'''
def write_checklist(checklist, last_mail_id, all_mails, user_id):
    if len(checklist) > 0:
        sqs = boto3.client("sqs")
        s3 = boto3.client('s3')
        checklist_queue = "https://sqs.us-east-1.amazonaws.com/554637451109/checklist-queue"
        bucket_name = "jingle-skill-bucket"

        # local directory filename.
        filename = '/tmp/'+ user_id + "_checklist.pkl"
        pickle.dump(checklist, open(filename, "wb"))
        s3.upload_file(filename, bucket_name, "data/"+ user_id + "/checklist.pkl")

        # Message responsible for notifiying the SQS queue immediately after writing the checklist.
        message = {'user_id': user_id, 's3_file': "data/"+ user_id + "/checklist.pkl"}
        resp = sqs.send_message(
            QueueUrl=checklist_queue,
            MessageBody=json.dumps(message)
        )


        # For all_mails.
        filename = '/tmp/'+ user_id + "_all_mails.pkl"
        pickle.dump(all_mails, open(filename, "wb"))
        s3.upload_file(filename, bucket_name, "data/"+ user_id + "/all_mails.pkl")


        # For last_mail_id.
        filename = '/tmp/'+ user_id + "_last_mail_id.pkl"
        pickle.dump(last_mail_id, open(filename, "wb"))
        s3.upload_file(filename, bucket_name, "data/"+ user_id + "/last_mail_id.pkl")



if __name__ == "__main__":
    last_id = None

    # Get the name list.
    nameList = get_uuids_from_s3()
    
    # Create the pool worker(s).
    pool = Pool(len(nameList))
    asyncResult = [pool.apply_async(executor, (userId, ) ) for userId in nameList]
    pool.close()
    pool.join()

    # Get from async results.
    results = [res.get() for res in asyncResult]

    print (results)