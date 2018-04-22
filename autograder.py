# autograder.py
# David Lewis
# dlewis@olivetcollege.edu

import email
import imaplib
import os
import logging
import re
import time

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from subprocess import call

# Debug Flags
#
# CRITICAL      50
# ERROR         40
# WARNING       30
# INFO          20
# DEBUG         10
# NOTSET        0

DEBUG = 0
logger = logging.getLogger('autograder')
MODE = 'UNSEEN'    # 'ALL' for debugging, 'UNSEEN' for use

USERNAME = os.environ['KEY']
PASSWORD = os.environ['VALUE']
CURRENT_DIR = os.environ['DIR']

# External aexecutable paths
PYTHON = '/home/ag/autograder/bin/python3.4'
DIFF = '/usr/bin/diff'
FLAKE = '/home/ag/autograder/bin/flake8'


def start_logging(log_level):
    hdlr = logging.FileHandler('autograder.log')
    logger.setLevel(log_level)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    hdlr.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(hdlr)


def safety_clean(file_with_path):
    try:
        os.remove(file_with_path)
        logger.debug('file deleted: {}'.format(file_with_path))
    except:
        logger.debug('file not found: {}'.format(file_with_path))


def parse_filename(filename):
    regex = '^([a-z]+)_(hw|lab|test)([0-1][0-9])\.py$'
    match = re.search(regex, filename)
    if match:
        print(match.groups())
        return match.groups()
    else:
        return ''


def cleanup(filepath):
    logger.debug('cleanup entered')
    safety_clean(filepath + 'diff_output.txt')
    safety_clean(filepath + 'sender.txt')
    safety_clean(filepath + 'student_summary.txt')
    safety_clean(filepath + 'doctest.log')
    safety_clean(filepath + 'flake8.log')


def process_file(filepath, filename, sender, subject):
    logger.debug('process_file entered')
    inputdir = filepath.replace(filename, '')
    if (test_execution(inputdir, filepath, filename, sender, subject)):
        if(test_doctest(inputdir, filepath, filename, sender, subject)):
            if(test_flake(inputdir, filepath, filename, sender, subject)):
                test_diff(inputdir, filepath, filename, sender, subject)


def test_execution(inputdir, filepath, filename, sender, subject):
    if (os.path.isfile(inputdir + 'input.txt')
            and os.path.isfile(inputdir + 'output.txt')):
        logger.debug('test_execution entered')
        command = '{0} {1} < {2}input.txt | tee {2}student_summary.txt 2> {2}sender.txt'.format(
            PYTHON,
            filepath,
            inputdir)
        print(command)
        retval = call([command], shell=True)
        logger.debug('retval:{} command:{}'.format(retval, command))
        if retval != 0:
            with open(inputdir + 'sender.txt', 'r') as file_handle:
                content = file_handle.read()
                logging.debug(content)
                comment = 'Your program has errors.\n\n'
                send_response(
                    sender,
                    '',
                    '{}: {}'.format(filename, comment),
                    content,
                    filepath,
                    filename)
                return False
        print('student_summary.txt exists: {}'.format(
            os.path.isfile('student_summary.txt')))
        return True
    else:
        comment = "We're sorry. This assignment as not been configured yet."
        send_response(
            sender,
            '',
            '{}: {}'.format(filename, comment),
            '',
            filepath,
            filename)


def test_doctest(inputdir, filepath, filename, sender, subject):
    logger.debug('test_doctest entered')
    command = '{0} -m doctest {1} -v > {2}doctest.log'.format(
        PYTHON,
        filepath,
        inputdir)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 1:
        with open(inputdir + 'doctest.log', 'r') as file_handle:
            testlog = file_handle.read()
            comment = 'Your submission failed its doctests. '
            comment += 'Please correct the errors before resubmitting.'
            send_response(
                sender,
                '',
                '{}: {}'.format(filename, comment),
                testlog,
                filepath,
                filename)
            return False
    return True


def test_flake(inputdir, filepath, filename, sender, subject):
    logger.debug('test_flake entered')
    command = '{0} {1}{2} > {1}flake8.log'.format(
        FLAKE,
        inputdir,
        filename)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 1:
        with open(inputdir + 'flake8.log', 'r') as file_handle:
            flakelog = file_handle.read()
            comment = 'Your submission is not properly formatted. Please correct the formatting before resubmitting.'
            send_response(
                sender,
                '',
                '{}: {}'.format(filename, comment),
                flakelog,
                filepath,
                filename)
            return False
    return True


def test_diff(inputdir, filepath, filename, sender, subject):
    logger.debug('test_diff entered')
    cmd = '{0} {1}output.txt {1}student_summary.txt > {1}diff_output.txt'
    command = cmd.format(DIFF, inputdir)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 0:
        comment = 'Your submission has been accepted for grading\n\n'
        send_response(
            sender,
            'david.lewis@cs.olivetcollege.edu',
            filename + ': ' + comment,
            comment,
            filepath,
            filename)
        return True
    elif retval == 1:
        with open(inputdir + 'student_summary.txt', 'r') as file_handle:
            content = file_handle.read()
            comment = 'Your output is incorrect\n\n'
            send_response(
                sender,
                '',
                '{}: {}'.format(filename, comment),
                content,
                filepath,
                filename)
        return False
    elif retval == 2:
        comment = 'Your submission did not generate a student_summary.txt file. Your instructor has been notified.\n\n'
        send_response(
            sender,
            'dlewis@olivetcollege.edu',
            filename + ': ' + comment,
            comment,
            filepath,
            filename)
        return False
    else:
        logging.error('Unknown return value for diff')


def send_response(sender, cc, subject, comments, filepath, filename):
    logging.debug('Sender: {}'.format(sender))
    logging.debug('CC: {}'.format(cc))
    logging.debug('Subject: {}'.format(subject))
    logging.debug('Comments: {}'.format(comments))

    msg = MIMEMultipart()
    msg["Subject"] = 'Re:' + subject
    msg["From"] = USERNAME
    msg["To"] = sender
    msg["Cc"] = cc
    body = MIMEText(comments)
    msg.attach(body)
    if filepath != '':
        with open(filepath, 'r') as file_handle:
            attachment = file_handle.read()
        a = MIMEText(attachment)
        a.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(a)

    server = smtplib.SMTP_SSL('smtp.gmail.com:465')
    server.login(USERNAME, PASSWORD)
    server.sendmail(
        msg['From'],
        msg['To'].split(',') + msg['Cc'].split(','),
        msg.as_string())
    server.quit()

    cleanup(filepath.replace(filename, ''))


def get_files_to_process(directory):
    imap_session = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    typ, accountDetails = imap_session.login(USERNAME, PASSWORD)
    if typ != 'OK':
        print('Not able to sign in!')
        raise

    imap_session.select(directory)
    typ, data = imap_session.search(None, MODE)
    if typ != 'OK':
        print('Error searching Inbox.')
        raise

    for msgId in data[0].split():
        typ, messageParts = imap_session.fetch(msgId, '(RFC822)')

        if typ != 'OK':
            print('Error fetching mail.')
            raise

        email_body = messageParts[0][1]

        mail = email.message_from_string(email_body.decode("utf-8"))

        sender = mail['From']
        sender = sender[sender.find('<') + 1:sender.find('>')]
        date = mail['Date']
        subject = mail['Subject']
        to = mail['To']
        message_id = mail['Message-ID']

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()

            parsed_name = parse_filename(file_name)
            if not parsed_name:
                send_response(
                    sender,
                    'dlewis@olivetcollege.edu',
                    'Your filename is malformed: {}'.format(file_name),
                    'Please rename the file using this pattern: <user id>_<assignment>.py',
                    '',
                    '')
                continue
            else:
                file_name = '{}_{}{}_{}.py'.format(
                    parsed_name[0],
                    parsed_name[1],
                    parsed_name[2],
                    int(time.time()))
                hw = '{}{}'.format(parsed_name[1], parsed_name[2])

            file_path = os.path.join(CURRENT_DIR, directory, hw, file_name)
            with open(file_path, 'wb') as fp:
                fp.write(part.get_payload(decode=True))

            with open('autograder.log', 'a+') as log:
                w = "From:{}, Date:{}, Subject:{}, To:{}, Message-ID:{}\n"
                log.write(w.format(
                    sender,
                    date,
                    subject,
                    to,
                    message_id,
                    file_name))

            process_file(file_path, file_name, sender, subject)

        # For future: label and move processed emails to their class/assignment folder.
        imap_session.store(msgId, '+FLAGS', 'SEEN')

    imap_session.close()
    imap_session.logout()

if __name__ == '__main__':
    start_logging(DEBUG)
    get_files_to_process('CS240')
    get_files_to_process('CS340')
