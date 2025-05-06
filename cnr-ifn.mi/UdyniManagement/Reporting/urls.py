from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView
from UdyniManagement.views import EmptyView

from . import views

urlpatterns = [
    path('', EmptyView.as_view(), name='reporting_index'),

    path('epascodes/', views.EpasCodeList.as_view(), name='epas_view'),
    path('epascodes/import', views.EpasCodeImport.as_view(), name='epas_import'),
    path('epascodes/update', views.EpasCodeUpdate.as_view(), name='epas_update'),

    path('bankholidays/', views.BankHolidayList.as_view(), name='bankholiday_view'),
    path('bankholidays/add', views.BankHolidayCreate.as_view(), name='bankholiday_add'),
    path('bankholidays/<int:pk>/modify', views.BankHolidayUpdate.as_view(), name='bankholiday_mod'),
    path('bankholidays/<int:pk>/delete', views.BankHolidayDelete.as_view(), name='bankholiday_del'),

    path('costs/', views.PersonnelCostList.as_view(), name='cost_view'),
    path('costs/add', views.PersonnelCostCreate.as_view(), name='cost_add'),
    path('costs/<int:pk>/modify', views.PersonnelCostUpdate.as_view(), name='cost_mod'),
    path('costs/<int:pk>/delete', views.PersonnelCostDelete.as_view(), name='cost_del'),

    path('presences/', views.PresenceDataList.as_view(), name='presencedata_view'),
    path('presences/detail/<int:researcher>/<int:year>', views.PresenceDataDetail.as_view(), name='presencedata_detailyear'),
    path('presences/detail/<int:researcher>/<int:year>/<int:month>', views.PresenceDataDetail.as_view(), name='presencedata_detailmonth'),
    path('presences/import', views.PresenceDataImport.as_view(), name='presencedata_import'),
    path('presences/store', views.PresenceDataStore.as_view(), name='presencedata_store'),

    path('periods/', views.ReportingPeriodList.as_view(), name='reporting_periods'),
    path('periods/add', views.ReportingCreate.as_view(), name='reporting_add'),
    path('periods/<int:pk>/modify', views.ReportingUpdate.as_view(), name='reporting_mod'),
    path('periods/<int:pk>/delete', views.ReportingDelete.as_view(), name='reporting_del'),

    path('reporting/', views.ReportingList.as_view(), name='reporting_list'),
    path('reporting/byresearcher/<int:rid>/', views.ReportingByResearcher.as_view(), name='reporting_byresearcher'),

    path('reporting/ajax/period', views.ReportingAjaxPeriod.as_view(), name="reporting_ajax_period"),
    path('reporting/ajax/year', views.ReportingAjaxYear.as_view(), name="reporting_ajax_year"),
    path('reporting/ajax/byresearcher/<int:rid>/<int:pid>/add_work', views.ReportingAddWork.as_view(), name='reporting_add_work'),
    path('reporting/ajax/byresearcher/<int:rid>/<int:pid>/add_mission', views.ReportingAddMission.as_view(), name='reporting_add_mission'),
    path('reporting/ajax/byresearcher/<int:rid>/work/<int:wid>/modify', views.ReportingModWork.as_view(), name='reporting_mod_work'),
    path('reporting/ajax/byresearcher/<int:rid>/work/<int:wid>/delete', views.ReportingDelWork.as_view(), name='reporting_del_work'),
    path('reporting/ajax/byresearcher/<int:rid>/mission/<int:mid>/modify', views.ReportingModMission.as_view(), name='reporting_mod_mission'),
    path('reporting/ajax/byresearcher/<int:rid>/mission/<int:mid>/delete', views.ReportingDelMission.as_view(), name='reporting_del_mission'),

    path('timesheets/', views.TimeSheetsView.as_view(), name='timesheets_view'),
    path('timesheets/<int:rid>/<int:year>/generate', views.TimeSheetsGenerate.as_view(), name='timesheets_generate'),
    path('timesheets/<int:rid>/<int:year>/print', views.TimeSheetsPrint.as_view(), name='timesheets_print'),

    path('timesheets/ajax/<int:rid>/<int:year>/generate', views.TimesheetAjaxDenied.as_view(), name='timesheets_ajax_generate_base'),
    path('timesheets/ajax/<int:rid>/<int:year>/generate/<int:month>', views.TimeSheetsAjaxGenerate.as_view(), name='timesheets_ajax_generate'),
    path('timesheets/ajax/check', views.TimeSheetsAjaxCheck.as_view(), name='timesheets_ajax_check'),

]

menu = {
    'name': 'Reporting',
    'link': reverse_lazy('reporting_index'),
    'icon': 'fa-solid fa-file-invoice-dollar',
    'subsections': [
        {
            'name': 'Personnel costs',
            'link': reverse_lazy('cost_view'),
            'permissions': ['Reporting.costs_manage', 'Reporting.costs_view'],
        },
        {
            'name': 'Presences',
            'link': reverse_lazy('presencedata_view'),
            'permissions': [
                'Reporting.presences_manage',
                'Reporting.presences_manage_own',
                'Reporting.presences_view',
                'Reporting.presences_view_own',
            ],
        },
        # {
        #     'name': 'Expenses reporting',
        #     'link': '', #reverse_lazy(''),
        #     'permissions': [],
        # },
        {
            'name': 'Reporting periods',
            'link': reverse_lazy('reporting_periods'),
            'permissions': [
                'Reporting.reporting_manage',
                'Reporting.reporting_manage_own',
                'Reporting.reporting_view',
            ],
        },
        #{
        #    'name': 'Reporting planning',
        #    'link': reverse_lazy('reporting_planning'),
        #    'permissions': [],
        #},
        {
            'name': 'Personnel reporting',
            'link': reverse_lazy('reporting_list'),
            'permissions': [
                'Reporting.reporting_manage',
                'Reporting.reporting_manage_own',
                'Reporting.reporting_view',
            ],
        },
        {
            'name': 'Timesheets',
            'link': reverse_lazy('timesheets_view'),
            'permissions': [
                'Reporting.timesheet_manage',
                'Reporting.timesheet_manage_own',
                'Reporting.timesheet_view',
                'Reporting.timesheet_view_own',
            ],
        },
        {
            'name': 'Bank holidays',
            'link': reverse_lazy('bankholiday_view'),
            'permissions': ['Reporting.holiday_view', 'Reporting.holiday_manage'],
        },
        {
            'name': 'EPAS codes',
            'link': reverse_lazy('epas_view'),
            'permissions': ['Reporting.epas_view', 'Reporting.epas_manage'],
        },
    ],
    'permissions': [
        'Reporting.epas_view',
        'Reporting.epas_manage',
        'Reporting.holiday_view',
        'Reporting.holiday_manage',
        'Reporting.costs_manage',
        'Reporting.costs_view',
        'Reporting.presences_manage',
        'Reporting.presences_manage_own',
        'Reporting.presences_view',
        'Reporting.presences_view_own',
        'Reporting.reporting_manage',
        'Reporting.reporting_manage_own',
        'Reporting.reporting_view',
        'Reporting.timesheet_manage',
        'Reporting.timesheet_manage_own',
        'Reporting.timesheet_view',
        'Reporting.timesheet_view_own',
    ],
}
