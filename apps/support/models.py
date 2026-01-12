from django.db import models
from django.utils.translation import gettext_lazy as _

class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('General Inquiry', 'General Inquiry'),
        ('Technical Support', 'Technical Support'),
        ('Billing Question', 'Billing Question'),
        ('Report an Issue', 'Report an Issue'),
    ]

    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email Address"))
    subject = models.CharField(_("Subject"), max_length=50, choices=SUBJECT_CHOICES, default='General Inquiry')
    message = models.TextField(_("Message"))
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.email}"
