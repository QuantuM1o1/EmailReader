import imaplib
import email
from email.header import decode_header
import configparser
import json
import psycopg2


config = configparser.ConfigParser()
config.read('config.ini')
email_address = config.get('Email', 'email_address')
password = config.get('Email', 'password')
imap_provider = config.get('Email', 'imap_provider')
db_host = config.get('PostgreSQL', 'host')
db_port = config.get('PostgreSQL', 'port')
db_name = config.get('PostgreSQL', 'dbname')
db_user = config.get('PostgreSQL', 'user')
db_password = config.get('PostgreSQL', 'password')
allowed_senders = [config.get('AllowedSenders', sender) for sender in config.options('AllowedSenders')]
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_password
)
cur = conn.cursor()
mail = imaplib.IMAP4_SSL(imap_provider)
mail.login(email_address, password)
mail.select("inbox")
status, messages = mail.search(None, "ALL")
message_ids = messages[0].split()
for msg_id in message_ids:
    status, msg_data = mail.fetch(msg_id, "(RFC822)")
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)
    sender = msg.get("From")
    if any(allowed_sender in sender for allowed_sender in allowed_senders):
        subject, encoding = decode_header(msg.get("Subject"))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8").strip()
                try:
                    json_data = json.loads(body)
                    if len(json_data) == 6:
                        print("Valid JSON:")
                        for key, value in json_data.items():
                            print(f"{key}: {value}")
                        cur.execute("SELECT * FROM responsibilities WHERE responsible = %s AND dep = %s",
                                    (json_data["responsible"], json_data["dep"]))
                        result = cur.fetchall()
                        if result:
                            print("Match found in the responsibilities table.")
                            cur.execute("INSERT INTO table_employee (name, sex, department, date_of_birth) "
                                        "VALUES (%s, %s, %s, %s)",
                                        (json_data["name"], json_data["sex"], json_data["department"],
                                         json_data["date_of_birth"]))

                            print("New row inserted into table_employee.")
                        else:
                            print("No match found in the responsibilities table.")
                    else:
                        print("Invalid JSON")
                except json.JSONDecodeError:
                    print("Invalid JSON: Could not decode")
conn.commit()
conn.close()
mail.logout()
