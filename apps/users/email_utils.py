import random
from django.core.mail import send_mail
from django.conf import settings


def generate_otp():
    """Generate a random 4-digit OTP code."""
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])


def send_otp_email(email, otp):
    """
    Send OTP verification email to user.
    Uses Django's send_mail which will output to console when using console backend.
    """
    subject = 'Eagerly - Verify Your Email'
    message = f"""
Hello!

Your verification code for Eagerly is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
The Eagerly Team
    """.strip()
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #00b4d8;">Verify Your Email</h2>
        <p>Hello!</p>
        <p>Your verification code for Eagerly is:</p>
        <div style="background: linear-gradient(135deg, #00b4d8, #0077b6); 
                    color: white; 
                    font-size: 32px; 
                    font-weight: bold; 
                    padding: 20px 40px; 
                    border-radius: 10px; 
                    display: inline-block;
                    letter-spacing: 8px;">
            {otp}
        </div>
        <p style="color: #666; margin-top: 20px;">This code will expire in 10 minutes.</p>
        <p style="color: #999; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #00b4d8;">Best regards,<br>The Eagerly Team</p>
    </body>
    </html>
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@eagerly.com',
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
