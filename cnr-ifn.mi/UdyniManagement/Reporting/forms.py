import re
import pandas as pd

from django import forms
from django.db.models import Q
from django.db.models.functions import ExtractYear
from django.core.exceptions import ValidationError

from Projects.models import Researcher, WorkPackage
from Reporting.models import EpasCode, PresenceData, ReportedWork, ReportedMission, ReportedWorkWorkpackage
from Reporting.utils import ConvertApostrophe2Accent


class EpasCodeUpdateForm(forms.Form):

    file = forms.FileField()

    def clean_file(self):
        # File should contain only an HTML table with EPAS codes
        file = self.cleaned_data['file']
        try:
            from lxml import etree
            etree.HTML(file.read()).find("body/table/tbody")
            file.seek(0)
        except Exception as e:
            print(e)
            raise ValidationError("File is not a valid table of EPAS codes (Error: {0!s})".format(e))


class PresenceInputForm(forms.Form):
    researcher = forms.ModelChoiceField(queryset=Researcher.objects.all())
    file = forms.FileField()

    def __init__(self, researcher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if researcher is not None:
            self.fields['researcher'].widget = forms.HiddenInput()
            self.fields['researcher'].initial = researcher

    def clean_file(self):
        file = self.cleaned_data['file']
        try:
            name = f"{self.cleaned_data['researcher'].surname} {self.cleaned_data['researcher'].name}"
            xls = pd.ExcelFile(file)
            good_sheets = 0
            # Check if is an old format file
            if 'Riassunto RF' in xls.sheet_names:
                # TODO: any check for old files?
                pass
            else:
                # Check that the file matches the selected researcher
                for n in xls.sheet_names:
                    m = re.match(r"([a-zA-Z \']+)_([a-z]+)(\d+)", n)
                    if m is not None:
                        if ConvertApostrophe2Accent(m.groups()[0]) == name:
                            good_sheets += 1
                if good_sheets == 0:
                    raise ValidationError("Excel file does not contain data for the selected researcher")

            return self.cleaned_data['file']

        except ValueError:
            raise ValidationError("File is not a valid Excel file")


class ReportedWorkForm(forms.ModelForm):

    class Meta:
        model = ReportedWork
        fields = ['hours', ]

    def __init__(self, *args, **kwargs):
        researcher = kwargs.pop('researcher')
        period = kwargs.pop('period')
        year = kwargs.pop('year', None)
        month = kwargs.pop('month', None)
        available_months = kwargs.pop('available_months', [])

        # Call parent constructor
        super().__init__(*args, **kwargs)

        # If the instance does not have a PK we are inserting a new item
        if not self.instance.pk:
            self.year_month_choices = available_months
            self.fields['year_month'] = forms.ChoiceField(choices=self.year_month_choices)

            if year is not None and month is not None:
                self.fields['year_month'].initial = f"{year}_{month}"

            # Add researcher and period to the model instance
            self.instance.researcher = researcher
            self.instance.period = period

        # Get workpackages
        wps = (
            WorkPackage.objects
            .filter(project=self.instance.period.project)
            .order_by('name')
        )
        for wp in wps:
            field_name = "wp_{0:s}".format(wp.name.lower())
            self.fields[field_name] = forms.FloatField(required=False, label="{0:s}: {1:s}".format(wp.name, wp.desc))
            # If instance has PK set initial value as the saved one
            if self.instance.pk:
                try:
                    rp = self.instance.workpackages.get(Q(workpackage=wp))
                    self.fields[field_name].initial = rp.fraction
                except ReportedWorkWorkpackage.DoesNotExist:
                    pass

    def clean(self):
        # Get parent cleaned data
        data = super().clean()

        if 'year_month' in data:
            # We are adding a new item
            try:
                # Store year and month
                year, month = self.cleaned_data.get('year_month').split("_")
                self.instance.year = int(year)
                self.instance.month = int(month)
            except Exception as e:
                raise ValidationError({'year_month': "Invalid month/year selection (Error: {0!s})".format(e)})

        # Check workpackages
        self.reported_workpackages = []
        for k, v in data.items():
            m = re.match('wp_(.*)', k)
            if m is not None:
                if v is not None and v != "":
                    wp_name = m.groups()[0]
                    try:
                        fraction = float(v)
                        if fraction > 0.0:
                            wp = WorkPackage.objects.get(Q(project=self.instance.period.project) & Q(name__iexact=wp_name))
                            try:
                                new_rp = ReportedWorkWorkpackage.objects.get(report=self.instance, workpackage=wp)
                            except ReportedWorkWorkpackage.DoesNotExist:
                                new_rp = ReportedWorkWorkpackage()
                                new_rp.workpackage = wp
                            new_rp.fraction = fraction
                            self.reported_workpackages.append(new_rp)
                    except WorkPackage.DoesNotExist:
                        raise ValidationError({k: 'Could not find the corresponding workpackage'})
                    except (TypeError, ValueError):
                        raise ValidationError({k: 'Invalid fraction specified for workpackage'})
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            saved_pks = []
            for rwp in self.reported_workpackages:
                rwp.report = instance
                rwp.save()
                saved_pks.append(rwp.pk)
            # Delete reported WP that are not included in the save
            ReportedWorkWorkpackage.objects.filter(Q(report=self.instance) & ~Q(pk__in=saved_pks)).delete()
        return instance


class AddReportedMissionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        # Store custom parameters
        kwargs.pop('instance')  # This is passed by the CreateView, but we don't need it, so we discard it
        self.researcher = kwargs.pop('researcher')
        self.period = kwargs.pop('period')
        self.year = kwargs.pop('year')

        # Call parent
        super().__init__(*args, **kwargs)

        # Find missions in the period not already reported
        reported_missions = (
            ReportedMission.objects
            .filter(
                Q(day__researcher=self.researcher) &
                Q(day__day__gte=self.period.rp_start) &
                Q(day__day__lte=self.period.rp_end)
            )
            .values_list('day__pk')
        )

        missions = (
            PresenceData.objects
            .filter(
                Q(researcher=self.researcher) &
                Q(day__gte=self.period.rp_start) &
                Q(day__lte=self.period.rp_end) &
                Q(ts_code=EpasCode.MISSION)
            )
            .exclude(
                Q(pk__in=reported_missions)
            )
        )

        # Filter mission by year if needed
        if self.year is not None:
            missions = missions.annotate(year=ExtractYear('day')).filter(year=self.year)

        # Add workpackage selection
        wps = WorkPackage.objects.filter(project=self.period.project)
        if wps.count():
            self.fields['workpackage'] = forms.ModelChoiceField(label="Workpackage", queryset=wps)

        # Add missions checkboxes
        for m in missions:
            name = 'mission_{0:d}'.format(m.pk)
            self.fields[name] = forms.BooleanField(label=m.day, required=False)

    def clean(self):
        data = self.cleaned_data
        self.missions = []
        for k, v in self.cleaned_data.items():
            m = re.match('^mission_(\d+)$', k)
            if m is not None and v:
                try:
                    pk = int(m.groups()[0])
                    new_m = ReportedMission()
                    new_m.period = self.period
                    new_m.day = PresenceData.objects.get(pk=pk)
                    new_m.workpackage = self.cleaned_data.get('workpackage')
                    self.missions.append(new_m)

                except (PresenceData.DoesNotExist, ValueError):
                    ValidationError({k: "Invalid mission day"})
        if not len(self.missions):
            raise ValidationError('No missions to report')
        return data

    def save(self, commit=True):
        if commit:
            for m in self.missions:
                m.save()
            return m
        else:
            return self.missions[0]
