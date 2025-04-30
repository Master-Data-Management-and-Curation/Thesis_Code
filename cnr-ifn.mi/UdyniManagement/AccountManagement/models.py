import datetime
from django.db import models


class RegistrationRequest(models.Model):
    # Name
    name = models.CharField(max_length=64)

    # Surname
    surname = models.CharField(max_length=64)

    # Email address
    email = models.EmailField(unique=True)

    # LDAP hash (SSHA)
    ldap_hash = models.CharField(max_length=38)

    # Samba hash
    samba_hash = models.CharField(max_length=32)

    # UUID for the request
    uuid = models.CharField(max_length=32, unique=True)

    # Status of the request
    SUBMITTED = 'S'
    VERIFIED = 'V'
    ACCEPTED = 'A'
    REJECTED = 'R'
    status = models.CharField(max_length=1, choices=[(SUBMITTED, 'Submitted'), (VERIFIED, 'Verified'), (ACCEPTED, 'Accepted'), (REJECTED, 'Rejected')])

    # Submit date
    submit_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'surname'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ['surname', 'name']
        default_permissions = ()
        permissions = [
            ('registration_manage', 'Manage registration requests'),
        ]

    def __str__(self):
        return f"Request from {self.name} {self.surname} is {self.get_status_display()}"

    @classmethod
    def PurgeOldRequests(cls):
        th_date = datetime.datetime.now() - datetime.timedelta(days=15)
        cls.objects.filter(models.Q(submit_timestamp__lt=th_date)).delete()
