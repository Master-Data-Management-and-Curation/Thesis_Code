from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import datetime

UserModel = get_user_model()


class Researcher(models.Model):
    """ Researchers' registry
    """
    # Name
    name = models.CharField(max_length=200)
    # Surname
    surname = models.CharField(max_length=200)
    # User name
    username = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ["surname", "name"]
        constraints = [
            models.UniqueConstraint(fields=['name', 'surname'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('researcher_view', 'View list of researchers'),
            ('researcher_manage', 'Manage list of researchers'),
        ]

    def __str__(self):
        return self.name + " " + self.surname

    def get_productive_hours(self, year, is_horizon_eu=False):
        if year >= 2021 and is_horizon_eu:
            return 1548
        else:
            d1 = (datetime.date(year,1,1) - self.researcherrole_set.order_by('start_date').first().start_date).days
            if d1 / 365.0 > 3:
                return 1506
            else:
                d2 = (datetime.date(year,12,31) - self.researcherrole_set.order_by('start_date').first().start_date).days
                if d2 / 365 <= 3:
                    return 1520
                else:
                    return round(1520 * (1 - (d2 / 365 - 3)) + 1506 * (d2 / 365 - 3))


class ResearcherRole(models.Model):
    """ Researcher role for each period
    """
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    # Role
    RESEARCHER_TD = "TD"
    RESEARCHER = "RI"
    SENIOR = "PR"
    DIRECTOR = "DR"
    INSTITUTE_DIRECTOR = "ID"
    FULL_PROFESSOR = "FP"
    ASSOCIATE_PROFESSOR = "AP"
    role = models.CharField(
        max_length=2,
        choices=[
            (RESEARCHER_TD, "Researcher (TD)"),
            (RESEARCHER, "Researcher"),
            (SENIOR, "Senior Researcher"),
            (DIRECTOR, "Research Director"),
            (INSTITUTE_DIRECTOR, "Institute Director"),
            (FULL_PROFESSOR, "Full Professor"),
            (ASSOCIATE_PROFESSOR, "Associate Professor"),
        ],
        default=RESEARCHER,
    )
    start_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'start_date'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["researcher", "start_date"]
        default_permissions = ()
        permissions = [
            ('role_manage_own', 'Modify own role'),
        ]

    def __str__(self):
        return "{0:s} from {1:s}".format(self.get_role_display(), self.start_date.isoformat())


class Project(models.Model):
    """ Projects' task registry
    """
    # Agency/Program
    agencies = (
        ("EU-H2020", "EU-H2020"),
        ("EU-HorizonEu", "EU-HorizonEu"),
        ("MUR", "MUR"),
        ("CNR", "CNR"),
    )
    name = models.CharField(max_length=100, db_index=True)
    agency = models.CharField(max_length=200, choices=agencies)
    reference = models.CharField(max_length=200)
    pi = models.ForeignKey(Researcher, on_delete=models.PROTECT, null=True, blank=True)
    depreciation = models.IntegerField(default=0)  # Number of years for depreciation
    sigla_id = models.IntegerField(null=True, blank=True)
    sigla_name = models.CharField(max_length=32, null=True, blank=True)
    sigla_cup = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["name", ]
        default_permissions = ()
        permissions = [
            ('project_view', 'View list of projects'),
            ('project_manage', 'Manage list of projects'),
        ]

    def __str__(self):
        return self.name + " (" + self.agency + ", " + self.reference + ")"

    def get_workpackages(self):
        return WorkPackage.objects.filter(project=self)

    workpackages = property(get_workpackages)


class WorkPackage(models.Model):
    """ Work packages in projects
        NOTE: every project have an unnamed WP that means generic work on a project
    """
    # Project
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # WP name
    name = models.CharField(max_length=100, db_index=True)
    # WP description
    desc = models.CharField(max_length=200, default="")

    def __str__(self):
        # return "{0:s} of {1!s}".format(self.name, self.project)
        return "{0:s}: {1:s}".format(self.name, self.desc)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'name'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["project__name", "name", ]
        default_permissions = ()


class ConflictOfInterest(models.Model):
    """ Handle conflict of interesets between a researcher and the current director
    """
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name="conflicts")
    director = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name="director_in_conflict")
    delegate = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name="delegate_for_conflict")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "ConflictsOfInterest"
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'director', 'start_date'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["director", "researcher", "-start_date"]
        default_permissions = ()
        permissions = [
            ('conflict_manage', 'Manage conflicts of interest'),
        ]

    def clean(self):
        # Start date should be before end date, and the two dates cannot be the same
        if self.end_date is not None and self.start_date >= self.end_date:
            raise ValidationError('Start date should be before end date, and the two dates cannot be the same')
