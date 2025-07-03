import smtplib
import ssl
from django.core.mail.backends.smtp import EmailBackend

class NonVerifyingSMTPBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        try:
            context = ssl._create_unverified_context()
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            self.connection.local_hostname = 'localhost'  
            self.connection.starttls(context=context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False