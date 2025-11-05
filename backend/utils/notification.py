import random
import smtplib
import time

def send_email(email):
    smtp_server = "smtp.gmail.com"
    sender_email = "nj323875@gmail.com"
    smtp_port = 587
    otp = generate_otp()
    content=f"Subject: Password Reset OTP\n\nYour OTP to reset password is {otp}"
    app_password=""
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, email, content)
        return otp
    except Exception as e:
        return None
    finally:
        server.quit()

otp_store={}

def generate_otp():
    return random.randint(1000,9999)

def save_otp(email):
    otp = generate_otp()
    otp_store[email]={'otp':otp, 'timestamp':time.time()}
    return otp

def is_otp_valid(email, otp, expiry_seconds=300):
    data = otp_store.get(email)
    if not data:
        return False
    if time.time() - data['timestamp'] > expiry_seconds:
        del otp_store[email]
        return False
    return str(data["otp"]) == str(otp)