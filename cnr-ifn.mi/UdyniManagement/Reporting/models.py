import calendar
import datetime
from django.db import models
from django.core.exceptions import ValidationError
from Projects import models as PrjModels


# Financial reporting models
# ==========================

class BankHoliday(models.Model):
    """ List of bank holidays
    """
    name = models.CharField(max_length=200)
    day = models.PositiveIntegerField()

    MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    month = models.PositiveIntegerField(choices=[(i + 1, m) for i, m in enumerate(MONTHS)])
    year = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['year', 'month', 'day', ], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["year", "month", "day"]
        default_permissions = ()
        permissions = [
            ('holiday_view', 'View list of bank holidays'),
            ('holiday_manage', 'Manage list of bank holidays'),
        ]

    def __str__(self):
        if self.year != 0:
            return self.name + " on {0:02d}/{1:02d}/{2:04d}".format(self.day, self.month, self.year)
        else:
            return self.name + " on {0!s} {1:d}".format(self.get_month_display(), self.day)


class EpasCode(models.Model):
    """ EPAS absence codes
    """
    code = models.CharField(max_length=32, unique=True, db_index=True)
    NONE = ""
    HOLIDAYS = "HO"
    MISSION = "MI"
    ILLNESS = "IL"
    CHOICES = [
        (NONE, "None"),
        (HOLIDAYS, "Holidays"),
        (MISSION, "Mission"),
        (ILLNESS, "Illness"),
    ]
    ts_code = models.CharField(
        max_length=2,
        choices=CHOICES,
        default=NONE,
    )
    description = models.CharField(max_length=256)

    def __str__(self):
        return "Code {0:s}: {1:s} (TS: {2:s})".format(self.code, self.description, self.get_ts_code_display())

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', ], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["code", ]
        default_permissions = ()
        permissions = [
            ('epas_view', 'View list of EPAS codes'),
            ('epas_manage', 'Manage list of EPAS codes'),
        ]


class PersonnelCost(models.Model):
    """ Registry of personnel cost by year
    """
    researcher = models.ForeignKey(PrjModels.Researcher, on_delete=models.CASCADE, related_name="costs")
    year = models.PositiveIntegerField(db_index=True)
    cost = models.FloatField()

    def __str__(self):
        return "{0!s} cost of {1:d}: {2:.2f}".format(self.researcher, self.year, self.cost)

    class Meta:
        ordering = ["year", "researcher"]
        constraints = [
            models.UniqueConstraint(fields=['year', 'researcher'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('costs_view', 'View personnel costs'),
            ('costs_manage', 'Manage personnel costs'),
        ]

    def get_hourly_rate(self):
        return round(self.cost / self.researcher.get_productive_hours(self.year) * 100.0) / 100.0


class PresenceData(models.Model):
    """ Presence data; hours, TS hours, absences, missions, ecc.
    """
    # Reserarcher
    researcher = models.ForeignKey(PrjModels.Researcher, on_delete=models.CASCADE, related_name="presences")
    # Working day
    day = models.DateField(db_index=True)
    # Actual worked hours (from accounting system)
    hours = models.FloatField()
    # Abscence code
    code = models.ForeignKey(EpasCode, on_delete=models.PROTECT, null=True, blank=True)
    # Absence code for ts
    ts_code = models.CharField(max_length=2, choices=EpasCode.CHOICES, default=EpasCode.NONE)

    def __str__(self):
        if self.code is None or self.code.ts_code == EpasCode.NONE:
            return "{0!s} on {1!s} worked for {2:.1f} hours".format(self.researcher, self.day, self.hours)
        else:
            return "{0!s} on {1!s} was absent for {2!s}".format(self.researcher, self.day, self.code.get_ts_code_display())

    class Meta:
        ordering = ["researcher", "day"]
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'day'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('presences_view', 'View presences'),
            ('presences_view_own', 'View own presences'),
            ('presences_manage', 'Manage presences'),
            ('presences_manage_own', 'Manage own presences'),
        ]


class ReportingPeriod(models.Model):
    """ Reporting period for a project
    """
    # Project
    project = models.ForeignKey(PrjModels.Project, on_delete=models.CASCADE, related_name="reporting_periods")
    # Start date
    rp_start = models.DateField(db_index=True)
    # End date
    rp_end = models.DateField(db_index=True)

    def __str__(self):
        return "{0:s}: from {1!s} to {2!s}".format(self.project.name, self.rp_start, self.rp_end)

    class Meta:
        ordering = ["project", "rp_start"]
        constraints = [
            models.UniqueConstraint(fields=['project', 'rp_start'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('reporting_view', 'View reporting periods'),
            ('reporting_manage', 'Manage reporting periods'),
            ('reporting_manage_own', 'Manage reporting periods of own projects'),
        ]

    def clean(self):
        # Start date should be before end date, and the two dates cannot be the same
        print(self.rp_start, self.rp_end)
        if self.rp_start >= self.rp_end:
            raise ValidationError('Start date should be before end date, and the two dates cannot be the same')
        # Check that the period does not overlap with other periods for the same project
        for rp in ReportingPeriod.objects.filter(project=self.project):
            if self.pk is not None and self.pk == rp.pk:
                # Skip self
                continue
            if self.rp_start >= rp.rp_start and self.rp_start <= rp.rp_end:
                raise ValidationError({'rp_start': ValidationError("The start date of the reporting period overlaps with another period for the same project/wp")})
            if self.rp_end >= rp.rp_start and self.rp_end <= rp.rp_end:
                raise ValidationError({'rp_end': ValidationError("The end date of the reporting period overlaps with another period for the same project/wp")})


class ReportedWork(models.Model):
    """ Reported hours of work for a researcher in a reporting period for a given month
    """
    # Reporting period
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name='reported_work')
    # Researcher
    researcher = models.ForeignKey(PrjModels.Researcher, on_delete=models.CASCADE, related_name='reported_work')
    # Year
    year = models.IntegerField()
    # Month
    month = models.IntegerField()
    # Reported hours
    hours = models.FloatField()

    def __str__(self):
        return "Reported work on {0:s} for {1!s} period {2:d}/{3:d}: {4:.1f} hours".format(self.period.project.name, self.researcher, self.month, self.year, self.hours)

    class Meta:
        ordering = ["period", "year", "month", "researcher"]
        constraints = [
            models.UniqueConstraint(fields=['period', 'researcher', 'year', 'month'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('rp_work_view', 'View reported work'),
            ('rp_work_view_own', 'View own reported work'),
            ('rp_work_manage', 'Manage reported work'),
            ('rp_work_manage_own', 'Manage own reported work'),
        ]

    def clean(self):
        ndays = calendar.monthrange(self.year, self.month)[1]
        if not (self.period.rp_start < datetime.date(year=self.year, month=self.month, day=ndays) or self.period.rp_end > datetime.date(year=self.year, month=self.month, day=1)):
            raise ValidationError('Reported work should be within start and end date of the period')


class ReportedMission(models.Model):
    """ Mission day to be reported in a project
    """
    # Reporting period
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name='reported_missions')
    # Workpackage (optional)
    workpackage = models.ForeignKey(PrjModels.WorkPackage, on_delete=models.PROTECT, null=True, blank=True, related_name='reported_missions')
    # Mission day
    day = models.ForeignKey(PresenceData, on_delete=models.PROTECT, related_name='reported_missions')

    def __str__(self):
        return "Reported mission on {0:s} for {1!s}: {2!s}".format(self.period.project.name, self.day.researcher, self.day.day)

    class Meta:
        ordering = ["period", "day__researcher", "day__day"]
        constraints = [
            models.UniqueConstraint(fields=['period', 'day'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('rp_mission_view', 'View reported missions'),
            ('rp_mission_view_own', 'View own reported missions'),
            ('rp_mission_manage', 'Manage reported missions'),
            ('rp_mission_manage_own', 'Manage own reported missions'),
        ]

    def clean(self):
        # Day must be within period
        if self.day.day < self.period.rp_start or self.day.day > self.period.rp_end:
            raise ValidationError('Reported mission day should be within start and end date of the period')


class ReportedWorkWorkpackage(models.Model):
    """ Split on workpackages of the hours worked on a period
    """
    report = models.ForeignKey(ReportedWork, on_delete=models.CASCADE, related_name='workpackages')
    workpackage = models.ForeignKey(PrjModels.WorkPackage, on_delete=models.CASCADE, related_name='reported_work')
    fraction = models.FloatField()
    # NOTE: the fraction can be any number, even the actual hours. The hours of the period will be split normalizing at the sum

    def __str__(self):
        return "Reported work on {0:s} for {1!s} period {2:d}/{3:d} splitted on {4:s}".format(self.report.period.project.name, self.report.researcher, self.report.month, self.report.year, self.workpackage.name)

    class Meta:
        ordering = ["report", "workpackage"]
        constraints = [
            models.UniqueConstraint(fields=['report', 'workpackage'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()

    def clean(self):
        # Check that the workpackage belongs to the project
        if self.workpackage.project != self.report.period.project:
            raise ValidationError('Workpackages should belongs to the project referred by the reporting period')


class TimesheetHours(models.Model):
    """ Hours recorded on timesheets for each day
    """
    report = models.ForeignKey(ReportedWork, on_delete=models.CASCADE, related_name='ts_hours')
    report_wp = models.ForeignKey(ReportedWorkWorkpackage, on_delete=models.CASCADE, null=True, blank=True, related_name='ts_hours')
    day = models.DateField()
    hours = models.FloatField()

    def __str__(self):
        if self.report_wp is not None:
            return "Hours worked by {0!s} on {1:s}/{2:s}, day {3!s}, {4:.1f} hours".format(self.report.researcher, self.report.period.project.name, self.report_wp.workpackage.name, self.day, self.hours)
        else:
            return "Hours worked by {0!s} on {1:s}, day {2!s}, {3:.1f} hours".format(self.report.researcher, self.report.period.project.name, self.day, self.hours)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['report', 'report_wp', 'day'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('timesheet_view', 'View timesheets'),
            ('timesheet_view_own', 'View own timesheets'),
            ('timesheet_manage', 'Manage timesheets'),
            ('timesheet_manage_own', 'Manage own timesheets'),
        ]
