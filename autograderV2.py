# autograder.py -version
# 2.0
# David Lewis
# dlewis@olivetcollege.edu

import email
import imaplib
import os
import logging
import re
import time

from subprocess import call

from AGSubmission import AGSubmission

# Debug Flags
#
# CRITICAL      50
# ERROR         40
# WARNING       30
# INFO          20
# DEBUG         10
# NOTSET        0

DEBUG = 10
MODE = 'UNSEEN'    # 'ALL' for debugging, 'UNSEEN' for use

USERNAME = os.environ['KEY']
PASSWORD = os.environ['VALUE']
CURRENT_DIR = os.environ['DIR']

# External aexecutable paths
PYTHON = '/home/ag/autograder/bin/python3.4'
DIFF = '/usr/bin/diff'
FLAKE = '/home/ag/autograder/bin/flake8'

logger = logging.getLogger('autograder')


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


def test_execution(submission):
    if (os.path.isfile(os.path.join(submission.directory, 'input.txt'))
            and os.path.isfile(os.path.join(
                submission.directory, 'solution.txt'))):
        logger.debug('test_execution entered')
        command = '{0} {1} < {2}/input.txt &> {2}/sender.txt'.format(
            PYTHON,
            submission.filepath,
            submission.working_directory)
        retval = call([command], shell=True)
        logger.debug('retval:{} command:{}'.format(retval, command))
        if retval != 0:
            filehandle = os.path.join(submission.directory, 'sender.txt')
            with open(filehandle, 'r') as handle:
                content = handle.read()
                logging.debug(content)
                comment = 'Your program has errors.\n\n'
                submission.send_response('{}\n\n{}'.format(comment, content))
                return False
        return True
    else:
        comment = "We're sorry. This assignment as not been configured yet."
        submission.send_response(comment)


def test_doctest(submission):
    logger.debug('test_doctest entered')
    command = '{0} -m doctest {1} -v > {2}/doctest.log'.format(
        PYTHON,
        submission.filepath,
        submission.working_directory)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 1:
        filehandle = os.path.join(submission.working_directory, 'testlog.txt')
        with open(filehandle, 'r') as file_handle:
            testlog = file_handle.read()
            comment = 'Your submission failed its doctests. '
            comment += 'Please correct the errors before resubmitting.'
            submission.send_response('{}\n\n{}'.format(comment, testlog))
            return False
    return True


def test_flake(submission):
    logger.debug('test_flake entered')
    command = '{0} {1} > {2}/flake8.log'.format(
        FLAKE,
        submission.filepath,
        submission.working_directory)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 1:
        filehandle = os.path.join(submission.working_directory, 'flake8.log')
        with open(filehandle, 'r') as file_handle:
            flakelog = file_handle.read()
            comment = 'Your submission is not properly formatted. '
            comment += 'Please correct the formatting before resubmitting.'
            submission.send_response('{}\n\n{}'.format(comment, flakelog))
            return False
    return True


def test_diff(submission):
    logger.debug('test_diff entered')
    cmd = '{0} {1}/solution.txt {1}/student_summary.txt > {1}/diff_output.txt'
    command = cmd.format(DIFF, submission.working_directory)
    retval = call([command], shell=True)
    logger.debug('retval:{} command:{}'.format(retval, command))
    if retval == 0:
        comment = 'Your submission has been accepted for grading\n\n'
        submission.send_response(comment)
        return True
    elif retval == 1:
        filehandle = os.path.join(submission.directory, 'output.txt')
        with open(filehandle, 'r') as handle:
            content = handle.read()
            comment = 'Your output is incorrect\n\n'
            submission.send_response('{}\n\n{}'.format(comment, content))
        return False
    elif retval == 2:
        comment = 'Your submission did not generate a student_summary.txt'
        comment += ' file. Your instructor has been notified.\n\n'
        submission.send_response(comment)
        return False
    else:
        logging.error('Unknown return value for diff')


def process_file(submission):
    if (test_execution(submission)):
        if(test_doctest(submission)):
            if(test_flake(submission)):
                test_diff(submission)


def get_files_to_process(directory):
    imap_session = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    typ, accountDetails = imap_session.login(USERNAME, PASSWORD)
    if typ != 'OK':
        print('Not able to sign in!')
        raise

    imap_session.select(directory)
    hw = ''
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

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()

            regex = '^([a-z]+)_(hw|lab|test)([0-1][0-9])\.py$'
            match = re.search(regex, file_name)
            if match:
                file_name = '{}_{}{}_{}.py'.format(
                    match.groups()[0],
                    match.groups()[1],
                    match.groups()[2],
                    int(time.time()))
                hw = '{}{}'.format(match.groups()[1], match.groups()[2])

            file_path = os.path.join(CURRENT_DIR, directory, hw, file_name)
            with open(file_path, 'wb') as fp:
                fp.write(part.get_payload(decode=True))

            submission = AGSubmission(file_path, mail)
            process_file(submission)

        imap_session.store(msgId, '+FLAGS', 'SEEN')

        mail_tag = os.path.join(directory, hw)
        result = imap_session.copy(msgId, mail_tag)

        if result[0] == 'OK':
            result = imap_session.store(msgId, '+FLAGS', '(\Deleted)')
            imap_session.expunge()

    imap_session.close()
    imap_session.logout()

if __name__ == '__main__':
    # start_logging(DEBUG)
    get_files_to_process('CS240')
    get_files_to_process('CS340')
