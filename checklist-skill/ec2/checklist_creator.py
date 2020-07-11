class Checklist:
    def __init__(self, mail_object):
        self.task_name = mail_object['subject']
        self.sender_tag = mail_object['sender_tag']
        self.sender_email = mail_object['sender_email']
        self.id = mail_object['id']
        self.description = mail_object['summary']
        self.end_date = mail_object['end_date']
        self.status = "Incomplete"


def get_checklist_objects(all_mails):
    checklist = []
    for mail in all_mails:
        checkItem = Checklist(mail)
        print("EndDate ", mail['end_date'])
        checklist.append(checkItem.__dict__)
    return checklist
