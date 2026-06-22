import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_status_email(recipient_email, candidate_name, job_title, company_name, status):
    """
    Sends an email notification to the candidate regarding status updates (hired or rejected).
    Always writes a copy to a local file in 'mock_emails' for offline verification and testing.
    """
    # 1. Format the email subject and body based on the status
    if status == 'hired':
        subject = f"Congratulations! You have been hired for {job_title} at {company_name}"
        body = f"""Hi {candidate_name},

Great news! We are pleased to inform you that you have been hired for the position of {job_title} at {company_name}.

The employer will be in touch with you shortly to discuss the next steps, including your offer letter and onboarding process.

Congratulations on your new role!

Best regards,
The Phi Careers Team
"""
    elif status == 'rejected':
        subject = f"Application Update: {job_title} at {company_name}"
        body = f"""Hi {candidate_name},

Thank you for your interest in the {job_title} position at {company_name} and for taking the time to apply and go through our process.

We want to let you know that the employer has updated the status of your application. Unfortunately, they have decided to move forward with other candidates at this time.

We encourage you to keep your profile updated and apply for other opportunities that match your skillset on Phi Careers.

We wish you all the best in your job search.

Best regards,
The Phi Careers Team
"""
    else:
        # We only send emails for hired/rejected status
        return

    # 2. Write a mock email file for developer testing/inspection
    try:
        mock_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mock_emails')
        os.makedirs(mock_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        safe_email = recipient_email.replace('@', '_').replace('.', '_')
        mock_filename = f"email_{timestamp}_{safe_email}_{status}.txt"
        mock_filepath = os.path.join(mock_dir, mock_filename)
        
        with open(mock_filepath, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {time.ctime()}\n")
            f.write(f"To: {recipient_email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Content:\n{body}\n")
        print(f"[Email Helper] Mock email written to {mock_filepath}")
    except Exception as e:
        print(f"[Email Helper] Error writing mock email file: {e}")

    # 3. Send real email using smtplib if SMTP_HOST is defined in .env
    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host:
        try:
            smtp_port = int(os.getenv("SMTP_PORT", "1025"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_use_tls = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
            smtp_from = os.getenv("SMTP_FROM", "no-reply@phicareers.com")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Setup connection
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            
            server.sendmail(smtp_from, [recipient_email], msg.as_string())
            server.quit()
            print(f"[Email Helper] Real email successfully sent to {recipient_email} via SMTP.")
        except Exception as e:
            # Catch exceptions and print to keep request lifecycle from breaking
            print(f"[Email Helper] Failed to send real email via SMTP: {e}")
