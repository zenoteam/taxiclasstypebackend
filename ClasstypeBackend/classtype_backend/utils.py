import os
import codecs
from pathlib import Path
from classtype_backend.task import send_email, send_sms


def format_string(text, data):
    message = text.format(**data)
    return message


def html_to_string(location, data):
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    loc = dir_path / location

    file = codecs.open(loc, 'r', "utf-8")
    template = file.read()
    message = format_string(template, data)
    return message


def send_notification(data, email_msg, sms_msg):
    email_data = {
        'emailAddress': data['email'],
        'mail': email_msg,
        'subject': data['subject'],
        'typeEmail': data['typeMessage']
    }
    sms_data = {
        'phoneNumber': data['phoneNumber'],
        'message': sms_msg,
        'typeMessage': data['typeMessage']
    }
    header = {'Authorization': data['Authorization']}

    send_sms.delay(sms_data, header)
    send_email.delay(email_data, header)
