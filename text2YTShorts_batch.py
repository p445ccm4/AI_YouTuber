import os
import traceback
import text2YTShorts_single_moreAI
import logging
import argparse
import smtplib
from email.mime.text import MIMEText
import datetime
import time

parser = argparse.ArgumentParser(description="Process topics from a file.")
parser.add_argument("topic_file", help="Path to the topic file.")
args = parser.parse_args()
topic_file = args.topic_file
with open(topic_file, 'r') as f:
    lines = f.readlines()

for line_idx, line in enumerate(lines):
    line = line.strip()
    if line.startswith("#") or not line:
        continue
    line = line.split()
    topic = line[0]
    music = line[1] if len(line) > 1 and line[1] != "None" else None
    indices_to_process = [int(i) for i in line[2:]] if len(line) > 2 else None # None if no indices provided

    print(f"Starting processing for {topic}")
    start_time = time.time()
    json_file = f"inputs/proposals/{topic}.json"
    topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
    working_dir = f"outputs/{topic_file_name}_{topic}"
    music_path = f"inputs/music/{music}.m4a" if music else None
    log_file = os.path.join(working_dir, f"{topic}.log")

    os.makedirs(working_dir, exist_ok=True)
    open(log_file, 'a').close()
    #BUG: cannot log to file
    logging.basicConfig(filename=log_file, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        shorts_maker = text2YTShorts_single_moreAI.YTShortsMaker(
            json_file,
            working_dir, 
            music_path, 
            indices_to_process,
            logger=logging.getLogger(topic)
        )
        shorts_maker.run()
        status = "Successfully"
        trace = None
        print(f"Finished processing {topic} successfully")
    except Exception as e:
        status = "Failed"
        trace = traceback.format_exc()
        print(f"Error processing {topic}: \n{trace}")
    finally:
        end_time = time.time()
        processing_time = end_time - start_time
        # Email sending
        with open("inputs/email_config.txt", "r") as f:
            sender_email = f.readline().strip()
            sender_password = f.readline().strip()
        receiver_email = "michael.ch@success-base.com"

        processing_time_minutes = int(processing_time // 60)
        processing_time_seconds = int(processing_time % 60)
        message = MIMEText(f"Topic: {topic}\nStatus: {status}\nFinish Time: {datetime.datetime.now()}\nProcessing Time: {processing_time_minutes} minutes {processing_time_seconds} seconds\nTraceback:\n{trace}\nRemaining Topics: {len(lines) - line_idx - 1}")
        message['Subject'] = f"Topic {topic} Processing Report: {status}"
        message['From'] = sender_email
        message['To'] = receiver_email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email sent successfully")
        except Exception as e:
            print(f"Email sending failed: {e}")

