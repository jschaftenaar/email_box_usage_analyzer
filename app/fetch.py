import imaplib
import pickle
import os
import hashlib

data_directory = 'data'

def md5(message_to_encode):
    hash_object = hashlib.md5(message_to_encode.encode())
    return hash_object.hexdigest()    

def retrieve_messages_from_mail_box(imap_server, mailbox_name):
    try:
        print(f'checking email box {mailbox_name}')
        imap_server.select(mailbox_name)
        status, messages = imap_server.search(None, 'ALL')
        message_ids = messages[0].split()
        print(status)
        print(f'found {len(message_ids)} messages in the email box {mailbox_name}')
        return message_ids
    except imaplib.IMAP4.error as ex:
        # we silently ignore this on :D 
        pass
    return []

def retrieve_emails_by_ids(imap_server, mail_box_name, message_ids, page_size=500, page=1):
    md5_hash=md5(f'mail_box_name_{page}')
    mail_data_file_name = f'{data_directory}/{md5_hash}.bin'
    if os.path.isfile(mail_data_file_name):
        with open(mail_data_file_name, 'rb') as mail_box_contents_file:
            emails = pickle.load(mail_box_contents_file)
        return emails

    emails=[]
    counter = 0
    imap_server.select(mail_box_name)
    for message_id in message_ids:
        print(f'attempting to download message {message_id.decode()}')
        status, msg_data = imap_server.fetch(message_id.decode(), '(RFC822)')
        print(f'{counter} of {len(message_ids)} is status: {status}')
        emails.append(msg_data)
        counter+=1

    with open(mail_data_file_name, 'wb') as mail_box_contents_file:
        pickle.dump(emails, mail_box_contents_file)  
    return emails

def retrieve_mail_box_ids(imap_server):
    mail_box_file_name = f'{data_directory}/mail_box_ids.bin'

    if os.path.isfile(mail_box_file_name):
        with open(mail_box_file_name, 'rb') as mail_box_ids_file:
            mail_boxes = pickle.load(mail_box_ids_file)
        return mail_boxes

    status, mail_box_list = imap_server.list()
    print(status)
    mail_boxes = {}

    for mailbox in mail_box_list:
        # Decode the mailbox name from bytes to string
        mailbox_name = mailbox.decode('utf-8').split('"/"')[1].strip()
        messages = retrieve_messages_from_mail_box(imap_server, mailbox_name)
        if messages:
            mail_boxes[mailbox_name] = messages

    # Close the connection to the IMAP server
    imap_server.close()
    imap_server.logout()

    with open(mail_box_file_name, 'wb') as mail_box_ids_file:
        pickle.dump(mail_boxes, mail_box_ids_file)
    
    return mail_boxes

def main():
    imap_server=imaplib.IMAP4_SSL(os.getenv('EBUA_IMAP_SERVER'))
    imap_server.login(os.getenv('EBUA_IMAP_USERNAME'), os.getenv('EBUA_IMAP_PASSWORD'))

    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    mail_box_ids = retrieve_mail_box_ids(imap_server)

    mails = {}

    print(mail_box_ids.keys())

    for mail_box_name in mail_box_ids.keys():
        print(mail_box_ids[mail_box_name])
        mails[mail_box_name] = retrieve_emails_by_ids(imap_server, mail_box_name, mail_box_ids[mail_box_name])



main()