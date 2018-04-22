# AGSubmission.py
# David Lewis
# dlewis@olivetcollege.edu

import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class AGSubmission(object):

    def __init__(self, savedpath, mail):
        path = os.path.split(savedpath)
        self.filepath = savedpath
        self.directory = path[0]
        self.filename = path[1]
        self.assignment_directory = os.path.split(self.working_directory)[1]

        sender = mail['From']
        self.sender = sender[sender.find('<') + 1:sender.find('>')]
        self.date = mail['Date']
        self.cc = ''
        self.subject = mail['Subject']
        self.to = mail['To']
        self.message_id = mail['Message-ID']

    def log_submission(self):
        with open('autograder.log', 'a+') as log:
            w = "From:{}, Date:{}, Subject:{}, To:{}, Message-ID:{}," \
                "Filename:{}, Working Directory:{}, Assignment Directory:{}\n"
            log.write(w.format(
                self.sender,
                self.date,
                self.subject,
                self.to,
                self.message_id,
                self.filename,
                self.working_directory,
                self.assignment_directory))

    def safety_clean(self, path):
        try:
            os.remove(path)
        except:
            pass

    def cleanup(self):
        self.safety_clean(os.path.join(self.working_directory,
                          'diff_output.txt'))
        self.safety_clean(os.path.join(self.working_directory,
                          'sender.txt'))
        self.safety_clean(os.path.join(self.working_directory,
                          'student_summary.txt'))
        self.safety_clean(os.path.join(self.working_directory,
                          'doctest.log'))
        self.safety_clean(os.path.join(self.working_directory,
                          'flake8.log'))

    def send_response(self, comment):
        print(self.filename, comment)
        self.msg = MIMEMultipart()
        self.msg["Subject"] = 'Re:' + self.subject
        self.msg["From"] = 'dlewis@olivetcollege.edu'
        self.msg["To"] = self.sender
        self.msg["Cc"] = self.cc
        self.body = MIMEText(comment)
        self.msg.attach(self.body)
        with open(os.path.join(self.directory, self.filename), 'r') as handle:
            attachment = handle.read()
        a = MIMEText(attachment)
        a.add_header(
            'Content-Disposition', 'attachment', filename=self.filename)
        self.msg.attach(a)

        server = smtplib.SMTP_SSL('smtp.gmail.com:465')
        server.login('ag@cs.olivetcollege.edu', '3v1lD4v3')
        server.sendmail(
            self.msg['From'],
            self.msg['To'].split(',') + self.msg['Cc'].split(','),
            self.msg.as_string())
        server.quit()
        self.cleanup()
