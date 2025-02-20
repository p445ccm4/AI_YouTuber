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
parser.add_argument("--email", action="store_true", help="Send email notification when finish processing each video.")
args = parser.parse_args()
topic_file = args.topic_file
send_email = args.email

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

    json_file = f"inputs/proposals/{topic}.json"
    topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
    working_dir = f"outputs/{topic_file_name}_{topic}"
    music_path = f"inputs/music/{music}.m4a" if music else None
    log_file = os.path.join(working_dir, f"{topic}.log")

    start_time = time.time()
    os.makedirs(working_dir, exist_ok=True)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)
    logger = logging.getLogger(topic)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info(f"Starting processing for {topic}")

    try:
        shorts_maker = text2YTShorts_single_moreAI.YTShortsMaker(
            json_file,
            working_dir, 
            music_path, 
            indices_to_process,
            logger=logger
        )
        shorts_maker.run()
        status = "Successfully"
        trace = None
        logger.info(f"Finished processing {topic} successfully")
    except Exception as e:
        status = "Failed"
        trace = traceback.format_exc()
        logger.error(f"Error processing {topic}: \n{trace}")
    finally:
        end_time = time.time()
        processing_time = end_time - start_time
        if send_email:
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
                logger.info("Email sent successfully")
            except Exception as e:
                logger.info(f"Email sending failed: {e}")
