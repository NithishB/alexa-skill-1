import boto3
import json
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config

client = boto3.client('sqs')
input_queue_url = 'https://sqs.us-east-1.amazonaws.com/554637451109/skill-1-input'
output_queue_url = 'https://sqs.us-east-1.amazonaws.com/554637451109/skill-1-output'

def run_summarizer():
    sqs = boto3.client('sqs')
    while True:
        messages = sqs.receive_message(
            QueueUrl=input_queue_url,
            AttributeNmaes=['All'],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        for message in messages:
            handle = message['ReceiptHandle']
            body = json.loads(message['Body'])
            email_body = body['body']
            try:
                model = T5ForConditionalGeneration.from_pretrained('t5-small')
                tokenizer = T5Tokenizer.from_pretrained('t5-small')

                preprocess_text = email_body.strip().replace("\n", "")
                t5_prepared_Text = "summarize: " + preprocess_text
                tokenized_text = tokenizer.encode(t5_prepared_Text, return_tensors="pt").to('cpu')
                summary_ids = model.generate(tokenized_text,
                                             num_beams=4,
                                             no_repeat_ngram_size=2,
                                             min_length=30,
                                             max_length=100,
                                             early_stopping=True)

                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            except:
                summary = ""

            body['summary'] = summary
            sqs.delete_message(
                QueueUrl=input_queue_url,
                ReceiptHandle=handle
            )

            resp = client.send_message(
                QueueUrl=output_queue_url,
                MessageBody=json.dumps(body)
            )

if __name__ == "__main__":
    run_summarizer()