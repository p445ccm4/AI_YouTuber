import os
import traceback
import text2YTVideos_single
import logging
import argparse
import smtplib
from email.mime.text import MIMEText
import datetime
import time
import tqdm

def text2YTVideos_batch(topic_file_path:str, send_email=False, make_shorts=True, ollama_model="qwen3:32b", logger=None): 
    with open(topic_file_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]

    for line_idx, line in enumerate(tqdm.tqdm(lines, unit="topics")):
        line = lines[line_idx].split()
        topic = line[0]
        indices_to_process = [int(i) for i in line[1:]] if len(line) > 1 else None # None if no indices provided

        json_file = f"inputs/proposals/{topic}.json"
        topic_file_name = os.path.splitext(os.path.basename(topic_file_path))[0]
        working_dir = f"outputs/{topic_file_name}_{topic}"
        log_file = os.path.join(working_dir, f"{topic}.log")

        start_time = time.time()
        os.makedirs(working_dir, exist_ok=True)
        if not logger:
            logger = logging.getLogger(topic)
            logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Starting processing for {topic}")

        status = "Failed"
        try:
            videos_maker = text2YTVideos_single.YTVideosMaker(
                json_file,
                working_dir,
                indices_to_process,
                make_shorts,
                ollama_model=ollama_model,
                logger=logger
            )
            for _ in videos_maker.run():
                yield
            status = "Successful"
            trace = None
            logger.info(f"Finished processing {topic} successfully")
        except Exception as e:
            trace = traceback.format_exc() or "probably keyboard interruption"
            logger.error(f"Error processing {topic}: \n{trace}")
        finally:
            if send_email:
                # Email sending
                end_time = time.time()
                processing_time = end_time - start_time
                
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
            logger.removeHandler(file_handler)
            yield
    return
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process topics from a file.")
    parser.add_argument("topic_file_path", help="Path to the topic file.")
    parser.add_argument("--email", action="store_true", help="Send email notification when finish processing each video.")
    args = parser.parse_args()

    text2YTVideos_batch(args.topic_file_path, args.email)