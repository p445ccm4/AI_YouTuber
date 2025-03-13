import os
import traceback
import text2YTShorts_single
import logging
# import argparse # Remove argparse
import smtplib
from email.mime.text import MIMEText
import datetime
import time

def text2YTShorts_batch_func(topic_file, send_email=False): # Define function, remove argparse
    output_string = "" # Capture output in a string
    with open(topic_file, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    for line_idx, line in enumerate(lines):
        if not line or line.strip().startswith("#"):
            continue
        line = line.split()
        topic = line[0]
        indices_to_process = [int(i) for i in line[1:]] if len(line) > 1 else None # None if no indices provided

        json_file = f"inputs/proposals/{topic}.json"
        topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
        working_dir = f"outputs/{topic_file_name}_{topic}"
        log_file = os.path.join(working_dir, f"{topic}.log")

        start_time = time.time()
        os.makedirs(working_dir, exist_ok=True)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        logger = logging.getLogger(topic)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.info(f"Starting processing for {topic}")

        status = "Failed"
        try:
            shorts_maker = text2YTShorts_single.YTShortsMaker(
                json_file,
                working_dir,
                indices_to_process,
                logger=logger
            )
            shorts_maker.run()
            status = "Successfully"
            trace = None
            logger.info(f"Finished processing {topic} successfully")
        except Exception as e:
            trace = traceback.format_exc() or "probably keyboard interruption"
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

                formatted_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = MIMEText(f"Topic: {topic}\n\n"
                                f"Status: {status}\n\n"
                                f"Finish Time: {formatted_time}\n\n"
                                f"Processing Time: {int(processing_time // 60)} minutes {int(processing_time % 60)} seconds\n\n"
                                f"Traceback:\n{trace}\n\n"
                                f"Remaining Topics: {len(lines) - line_idx - 1}")
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
        output_string += f"Processing topic: {topic}, Status: {status}\n" # Capture output for gradio
    return output_string # Return the output string


# if __name__ == "__main__": # Remove this block
#     parser = argparse.ArgumentParser(description="Process topics from a file.")
#     parser.add_argument("topic_file", help="Path to the topic file.")
#     parser.add_argument("--email", action="store_true", help="Send email notification when finish processing each video.")
#     args = parser.parse_args()
#
#     text2YTShorts_batch(args.topic_file, args.email)