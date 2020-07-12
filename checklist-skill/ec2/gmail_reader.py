from __future__ import print_function

import base64
import math
import re

import dateutil.parser as parser
from bs4 import BeautifulSoup


class GmailAccessor:
    
    def __init__(self, service, last_mail_id, mail_contents):
        self.service = service
        self.mail_contents = mail_contents
        self.last_mail_id = last_mail_id
        
        # List of emails that we need.
        self.sender_mail_check = [
                                      'asp-offersonboarding@amazon.com',
                                      'newhiresupport@amazon.com',
                                      'amazon-i9@i9advantage.com',
                                      '(@graebel.com) -GraebelNotifications'
                                      'MyDocs-noreply@onbaseonline.com',
                                      'i9advantagesupport@amazon.com Action Needed',
                                      '(@accurate.com)  Amazon Background ',
                                      'noreply@qemailserver.com RESPONSE NEEDED ',
                                      'noreply@qemailserver.com equipment '        
                                 ]
        
        # Only init when these values are not present.
        if (not last_mail_id and not mail_contents):
            # Maintain the last seen id for each of these email ids.
            self.last_mail_id = {}
            self.mail_contents = {}
            for email in self.sender_mail_check:
                self.last_mail_id[email] = ''
                self.mail_contents[email] = []
            
    
    def read_email(self, num_emails):
        
        self.current_mails = []
        self.first_email = True
        self.end = False
        
        msg_api = self.service.users().messages()
        
        for sender_mail_id in self.sender_mail_check:
            
            msg_request = msg_api.list( **{ 'userId': 'me', 
                                           'labelIds': ['INBOX'], 
                                           'maxResults': num_emails, 
                                           'q': "from:" + sender_mail_id + " after:2020/02/1 before:2020/7/12"
                                          } ).execute()
            
            # print (sender_mail_id, ' : \n', msg_request)
            
            
            if 'messages' in msg_request:
                
                print ('Before : ', len(msg_request['messages']))
                
                flag = False
                # Use the last seen mail id to filter the mails that we're fetching.
                for idx in range(len(msg_request['messages'])):
                    # If we see a mail id with the last mail id for this particular email, then we break.
                    if ( self.last_mail_id[sender_mail_id] == msg_request['messages'][idx]['id'] ):
                        flag = True
                        break
                
                # Take all the mails till idx as being valid mails.
                if (flag):
                    msg_request['messages'] = msg_request['messages'][:idx]
            
                print ('After : ', len(msg_request['messages']))
                
                for msg in msg_request['messages']:
                    get_param = {
                                    'userId': 'me',
                                    'id': msg['id'],
                                    'format': 'full'
                                }
                    self.collect_details( self.service.users().messages().get(**get_param).execute(), sender_mail_id)
                                    
                # Set the last mail id for each mail id.
                self.last_mail_id[sender_mail_id] = self.mail_contents[sender_mail_id][0]['id']
        
        return self.last_mail_id, self.mail_contents  
                
    def collect_multi_level_part(self, part):
        full_body = ""
        for p in part['parts']:
            data = p['body']['data'].replace('-','+').replace('_','/')
            clean_data = str(base64.urlsafe_b64decode(bytes(data,'UTF-8')))
            soup = BeautifulSoup(clean_data, "html")
            text = soup.body()[0].text[2:-1]
            del soup
            full_body+=str(text)
        return full_body
    
    def collect_single_level_part(self, part):
        data = part['body']['data'].replace('-','+').replace('_','/')
        clean_data = str(base64.b64decode(bytes(data,'utf-8')))
        soup = BeautifulSoup(clean_data, "lxml")
        text = soup.body()[0].text[2:-1]
        del soup
        return str(text)
    
    def post_process(self, text):
        text = re.sub("<[^>]*>","",text)
        text = re.sub("\\\\[a-z0-9]{3}","",text)
        text = text.replace("\\r","").replace("\\n","").replace("[","").replace("]","").replace("\\","")
        return text

    def collect_details(self, message, sender_mail_id):
            tmp = {}
            tmp['id'] = message['id']
            payld = message['payload']
            headr = payld['headers']
            
            for three in headr:
                
                if three['name'] == 'From':
                    msg_from = three['value']
                    if len(msg_from.split('<')) > 1:
                        tag = msg_from.split('<')[0].strip()
                        email = msg_from.split('<')[1].replace('>','').strip()
                    else:
                        tag = msg_from.split('@')[0]
                        email = msg_from
                    tmp['sender_tag'] = tag
                    tmp['sender_email'] = email
                    
                elif three['name'] == 'Subject':
                    tmp['subject'] = three['value']
                    
                elif three['name'] == 'Date':
                            msg_date = three['value']
                            date_parse = (parser.parse(msg_date))
                            m_date = (date_parse.date())
                            tmp['date'] = str(m_date)
            
            try:        
                    tmp['snippet'] = message['snippet'] # fetching message snippet

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
                    self.mail_contents[sender_mail_id].append(tmp)
            except:
                    tmp['body'] = 'Not Available' # Skipping over mail that does not have a body.
                    self.mail_contents[sender_mail_id].append(tmp)
                    

def get_emails(last_id, all_mails, service):
    accessor = GmailAccessor(service, last_id, all_mails)
    last_id, all_mails = accessor.read_email(50)
    # Return Value : Dict of ids, and Dict of mails.
    return last_id, all_mails
