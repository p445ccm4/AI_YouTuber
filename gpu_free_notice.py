import smtplib
from email.mime.text import MIMEText
import subprocess
import time

def get_gpu_ram_available():
    """Returns the available GPU RAM in GB."""
    try:
        # subprocess.run("nvidia-smi", check=True)
        output = subprocess.check_output("nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits", shell=True)
        ram_available = int(output.decode('utf-8').strip()) / 1024  # Convert MB to GB
        return ram_available
    except Exception as e:
        print(f"Error getting GPU RAM: {e}")
        return 0

def send_email(sender_email, sender_password, receiver_email, subject, body):
    """Sends an email using the provided credentials and content."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    sender_email = "michael.ch@success-base.com"  # Replace with your email address
    sender_password = "sb@927454"  # Replace with your email password or app password
    receiver_email = "michael.ch@success-base.com"
    subject = "A100 GPU RAM Available"
    body = "The available GPU RAM on the A100 is more than 40GB."

    while True:
        available_ram = get_gpu_ram_available()
        if available_ram > 40:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"Time: {current_time} Available GPU RAM: {available_ram:.2f}GB. Sending email...", end='\r')
            send_email(sender_email, sender_password, receiver_email, subject, body)
            break  # Send the email only once
        else:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"Time: {current_time} Available GPU RAM: {available_ram:.2f}GB. Checking again in 60 seconds...", end='\r')
            time.sleep(60)  # Wait for 60 seconds before checking again