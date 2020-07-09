from __future__ import print_function
import re
import boto3
import json
import math
import base64
from bs4 import BeautifulSoup
import dateutil.parser as parser

class GmailAccessor:

    def __init__(self, service, last_seen_id=None, all_mail_data=[]):
        self.service = service
        self.all_mail_data = all_mail_data
        self.last_seen_id = last_seen_id

    def read_email(self, num_emails):

        self.current_mails = []
        self.first_email = True
        self.end = False

        num_repeats = math.ceil(num_emails / 10)
        msg_api = self.service.users().messages()
        list_param = {'userId': 'me', 'maxResults': 10}
        msg_request = msg_api.list(**list_param)
        for _ in range(num_repeats):
            mail_list = msg_request.execute()
            batch = self.service.new_batch_http_request(callback=self.collect_details)
            for msg in mail_list['messages']:
                if self.last_seen_id is not None:
                    if msg['id'] == self.last_seen_id:
                        self.end = True
                        break
                    else:
                        get_param = {
                            'userId': 'me',
                            'id': msg['id'],
                            'format': 'full'
                        }
                        batch.add(self.service.users().messages().get(**get_param), request_id=msg['id'])
                else:
                    get_param = {
                        'userId': 'me',
                        'id': msg['id'],
                        'format': 'full'
                    }
                    batch.add(self.service.users().messages().get(**get_param), request_id=msg['id'])

            batch.execute()
            if self.end:
                break
            else:
                msg_request = msg_api.list_next(msg_request, mail_list)

        self.all_mail_data = self.current_mails + self.all_mail_data
        return self.last_seen_id, self.all_mail_data

    def collect_multi_level_part(self, part):
        full_body = ""
        for p in part['parts']:
            data = p['body']['data'].replace('-', '+').replace('_', '/')
            clean_data = str(base64.urlsafe_b64decode(bytes(data, 'UTF-8')))
            soup = BeautifulSoup(clean_data, "lxml")
            text = soup.body()[0].text[2:-1]
            del soup
            full_body += str(text)
        return full_body

    def collect_single_level_part(self, part):
        data = part['body']['data'].replace('-', '+').replace('_', '/')
        clean_data = str(base64.b64decode(bytes(data, 'utf-8')))
        soup = BeautifulSoup(clean_data, "lxml")
        text = soup.body()[0].text[2:-1]
        del soup
        return str(text)

    def post_process(self, text):
        text = re.sub("<[^>]*>", "", text)
        text = re.sub("\\\\[a-z0-9]{3}", "", text)
        text = text.replace("\\r", "").replace("\\n", "").replace("[", "").replace("]", "").replace("\\", "")
        return text

    def collect_details(self, request_id, message, exception):
        if exception is not None:
            print('messages.get failed for message id {}: {}'.format(request_id, exception))
        else:
            tmp = {}
            if self.first_email:
                self.last_seen_id = message['id']
                self.first_email = False

            tmp['id'] = message['id']
            payld = message['payload']
            headr = payld['headers']

            for one in headr:
                if one['name'] == 'Subject':
                    tmp['subject'] = one['value']
                else:
                    pass

            for two in headr:
                if two['name'] == 'Date':
                    msg_date = two['value']
                    date_parse = (parser.parse(msg_date))
                    m_date = (date_parse.date())
                    tmp['date'] = str(m_date)
                else:
                    pass

            for three in headr:
                if three['name'] == 'From':
                    msg_from = three['value']
                    if len(msg_from.split('<')) > 1:
                        tag = msg_from.split('<')[0].strip()
                        email = msg_from.split('<')[1].replace('>', '').strip()
                    else:
                        tag = msg_from.split('@')[0]
                        email = msg_from
                    tmp['sender_tag'] = tag
                    tmp['sender_email'] = email
                else:
                    pass

            tmp['snippet'] = message['snippet']  # fetching message snippet

            # Fetching message body
            if 'multipart' in payld['mimeType']:
                part = payld['parts'][0]
                if part['body']['size'] == 0 and "parts" in part.keys():
                    full_body = self.collect_multi_level_part(part)
                else:
                    full_body = self.collect_single_level_part(part)
            else:
                full_body = self.collect_single_level_part(payld)

            tmp['body'] = self.post_process(full_body)
            self.current_mails.append(tmp)


def filter_relevant_email(response):
    required_mails = []
    sender_email_check = ['asp-offersonboarding', 'newhiresupport', 'amazon-i9', 'gbl-relocation-srvcs',
                          'internprogram', 'MyDocs-noreply', 'i9advantagesupport', 'studentprograms.amazon.com',
                          'graebel.com', 'background-screening.panorama.hr.a2z.com', 'accurate.com', 'amazon.com']

    for x in response:
        for key, val in x.items():
            if (key == 'sender_email'):
                value = val.split('@', 1)
                if ((value[0] in sender_email_check) or (value[1] in sender_email_check)):
                    required_mails.append(x)

    return required_mails

def get_summarized_email(service, last_id):
    input_queue_url = 'https://sqs.us-east-1.amazonaws.com/554637451109/skill-1-input'
    output_queue_url = 'https://sqs.us-east-1.amazonaws.com/554637451109/skill-1-output'
    sqs = boto3.client('sqs')
    accessor = GmailAccessor(service, last_id, [])
    last_seen_id, all_mails = accessor.read_email(1000)
    all_mails = filter_relevant_email(all_mails)
    for mail in all_mails:
        sqs.send_message(
            QueueUrl=input_queue_url,
            MessageBody=json.dumps(mail)
        )
    received_cnt = 0
    new_all_mails = []
    while len(new_all_mails) < len(all_mails):
        messages = sqs.receive_message(
            QueueUrl=output_queue_url,
            AttributeNmaes=['All'],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        for message in messages:
            handle = message['ReceiptHandle']
            body = json.loads(message['Body'])
            sqs.delete_message(
                QueueUrl=output_queue_url,
                ReceiptHandle=handle
            )
            new_all_mails.append(body)
    return last_seen_id, new_all_mails