
response = [{'id' : '12345wflwh443434', 'time' : '1545730073', 'subject' : 'Welcome to Amazon - Manager Intro', 'sender_tag':'Amazon.com','sender_id' : 'asp-offersonboarding@amazon.com',
             'email' : 'Hi Raghavendhar, Welcome to Amazon! We are excited you will be joining '
                       'us as a Software Development Engineer Intern on 5/19/2020. We wanted to take this opportunity to introduce you '
                       'to your manager, Santosh Chandrachood, who is ccd.You may have already connected, but if not, feel free to ask questions about the team,'
                       ' projects you will be working on, and specifics related to your location. COVID-19 (2019 Novel Coronavirus) Update: Your start date is still set for 5/19/2020. The health of our employees, including those who are waiting to start, is our top priority. We are continuously'
                       ' monitoring the latest guidance from the CDC and WHO related to COVID-I9. As we have additional information to share, we will contact you.You will receive details about Day 1 from the New Hire Support team the week before you start. If you do not receive this information by 10am on the Friday before you are '
                       'scheduled to start, send a note to asp-offersonboarding@amazon.com with “URGENT – NHO Details Not Received” in the subject line.Cheers,Amazon Student Programs'},
            {'id' : '12345wflwh4434345', 'time' : '1545730073', 'subject' : 'Welcome to Amazon - Manager Intro', 'sender_tag':'Amazon' ,'sender_id' : 'asp-offersonboarding@amazon.com',
             'email' : 'Hi Raghavendhar, Welcome to Amazon! We are excited you will be joining '
                       'us as a Software Development Engineer Intern on 5/19/2020. We wanted to take this opportunity to introduce you '
                       'to your manager, Santosh Chandrachood, who is ccd.You may have already connected, but if not, feel free to ask questions about the team,'
                       ' projects you will be working on, and specifics related to your location. COVID-19 (2019 Novel Coronavirus) Update: Your start date is still set for 5/19/2020. The health of our employees, including those who are waiting to start, is our top priority. We are continuously'
                       ' monitoring the latest guidance from the CDC and WHO related to COVID-I9. As we have additional information to share, we will contact you.You will receive details about Day 1 from the New Hire Support team the week before you start. If you do not receive this information by 10am on the Friday before you are '
                       'scheduled to start, send a note to asp-offersonboarding@amazon.com with “URGENT – NHO Details Not Received” in the subject line.Cheers,Amazon Student Programs'}]

sender_tag_check = ['Amazon.com','LinkedIn','Medium Daily Digest']
sender_email_check = ['asp-offersonboarding','newhiresupport','amazon-i9','gbl-relocation-srvcs','internprogram','MyDocs-noreply','i9advantagesupport','studentprograms.amazon.com','graebel.com',
          'background-screening.panorama.hr.a2z.com','accurate.com','amazon.com']

def Textintake(response):
    for x in response:
        for key, val in x.items():
            if ((key == 'sender_tag') and (val in sender_tag_check)):
                break
            elif(key == 'sender_id'):
                value = val.split('@',1)
                if((value[0] in sender_email_check) or (value[1] in sender_email_check)):
                    print("sender id there")
                    # go to summary function
            else:
                print("ok")
                # go to summary function

Textintake(response)

import torch
import json
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config

model = T5ForConditionalGeneration.from_pretrained('t5-small')
tokenizer = T5Tokenizer.from_pretrained('t5-small')
device = torch.device('cpu')

text ="""
The US has "passed the peak" on new coronavirus cases, President Donald Trump said and predicted that some states would reopen this month.
The US has over 637,000 confirmed Covid-19 cases and over 30,826 deaths, the highest for any country in the world.
At the daily White House coronavirus briefing on Wednesday, Trump said new guidelines to reopen the country would be announced on Thursday after he speaks to governors.
"We'll be the comeback kids, all of us," he said. "We want to get our country back."
The Trump administration has previously fixed May 1 as a possible date to reopen the world's largest economy, but the president said some states may be able to return to normalcy earlier than that.
"""


preprocess_text = text.strip().replace("\n","")
t5_prepared_Text = "summarize: "+preprocess_text
print ("original text preprocessed: \n", preprocess_text)

tokenized_text = tokenizer.encode(t5_prepared_Text, return_tensors="pt").to(device)


# summmarize
summary_ids = model.generate(tokenized_text,
                             num_beams=4,
                             no_repeat_ngram_size=2,
                             min_length=30,
                             max_length=100,
                             early_stopping=True)

output = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

print ("\n\nSummarized text: \n",output)