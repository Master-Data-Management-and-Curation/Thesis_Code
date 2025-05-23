# Generated by Django 4.2.20 on 2025-04-14 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# Projects.migrations.0002_copy_data
# NOTE: the migration of the data will not be needed on new installs. So the RunPython blocks are now commented

class Migration(migrations.Migration):

    replaces = [('Projects', '0001_initial'), ('Projects', '0002_copy_data'), ('Projects', '0003_auto_20220411_1829'), ('Projects', '0004_auto_20220413_0917'), ('Projects', '0005_researcher_username'), ('Projects', '0006_alter_researcher_username'), ('Projects', '0007_alter_researcherrole_role'), ('Projects', '0008_auto_20220422_1708'), ('Projects', '0009_auto_20220422_1837'), ('Projects', '0010_project_depreciation'), ('Projects', '0011_alter_project_agency'), ('Projects', '0012_alter_project_options_alter_researcher_options_and_more'), ('Projects', '0013_alter_project_options_alter_researcher_options_and_more'), ('Projects', '0014_auto_20230118_2137'), ('Projects', '0015_conflictofinterest_end_date')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('agency', models.CharField(max_length=200)),
                ('reference', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('surname', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['surname', 'name'],
            },
        ),
        migrations.CreateModel(
            name='WorkPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('desc', models.CharField(default='', max_length=200)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Projects.project')),
            ],
            options={
                'ordering': ['project__name', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ResearcherRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('RI', 'Researcher'), ('PR', 'Senior Researcher'), ('DR', 'Research Director')], default='RI', max_length=2)),
                ('start_date', models.DateField()),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Projects.researcher')),
            ],
            options={
                'ordering': ['researcher', 'start_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='researcher',
            constraint=models.UniqueConstraint(fields=('name', 'surname'), name='projects_researcher_unique'),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.UniqueConstraint(fields=('name',), name='projects_project_unique'),
        ),
        migrations.AddConstraint(
            model_name='workpackage',
            constraint=models.UniqueConstraint(fields=('project', 'name'), name='projects_workpackage_unique'),
        ),
        migrations.AddConstraint(
            model_name='researcherrole',
            constraint=models.UniqueConstraint(fields=('researcher', 'start_date'), name='projects_researcherrole_unique'),
        ),
        #migrations.RunPython(
        #    code=Projects.migrations.0002_copy_data.migrate_reasearchers_and_roles,
        #),
        #migrations.RunPython(
        #    code=Projects.migrations.0002_copy_data.migrate_projects_and_wps,
        #),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='workpackage',
            name='name',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name='project',
            name='pi',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Projects.researcher'),
        ),
        migrations.AlterField(
            model_name='researcherrole',
            name='role',
            field=models.CharField(choices=[('RI', 'Researcher'), ('PR', 'Senior Researcher'), ('DR', 'Research Director'), ('ID', 'Institute Director'), ('FP', 'Full Professor'), ('AP', 'Associate Professor')], default='RI', max_length=2),
        ),
        migrations.AddField(
            model_name='researcher',
            name='username',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='researcherrole',
            name='role',
            field=models.CharField(choices=[('TD', 'Researcher (TD)'), ('RI', 'Researcher'), ('PR', 'Senior Researcher'), ('DR', 'Research Director'), ('ID', 'Institute Director'), ('FP', 'Full Professor'), ('AP', 'Associate Professor')], default='RI', max_length=2),
        ),
        migrations.AddField(
            model_name='project',
            name='sigla_cup',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='sigla_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='sigla_name',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='depreciation',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='project',
            name='agency',
            field=models.CharField(choices=[('EU-H2020', 'EU-H2020'), ('EU-HorizonEu', 'EU-HorizonEu'), ('MUR', 'MUR'), ('CNR', 'CNR')], max_length=200),
        ),
        migrations.AlterModelOptions(
            name='workpackage',
            options={'default_permissions': (), 'ordering': ['project__name', 'name']},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'default_permissions': (), 'ordering': ['name'], 'permissions': [('project_view', 'View list of projects'), ('project_manage', 'Manage list of projects')]},
        ),
        migrations.AlterModelOptions(
            name='researcher',
            options={'default_permissions': (), 'ordering': ['surname', 'name'], 'permissions': [('researcher_view', 'View list of researchers'), ('researcher_manage', 'Manage list of researchers')]},
        ),
        migrations.AlterModelOptions(
            name='researcherrole',
            options={'default_permissions': (), 'ordering': ['researcher', 'start_date'], 'permissions': [('role_manage_own', 'Modify own role')]},
        ),
        migrations.CreateModel(
            name='ConflictOfInterest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('delegate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegate_for_conflict', to='Projects.researcher')),
                ('director', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='director_in_conflict', to='Projects.researcher')),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conflicts', to='Projects.researcher')),
            ],
            options={
                'verbose_name_plural': 'ConflictsOfInterest',
                'ordering': ['director', 'researcher', '-start_date'],
                'permissions': [('conflict_manage', 'Manage conflicts of interest')],
                'default_permissions': (),
            },
        ),
        migrations.AddConstraint(
            model_name='conflictofinterest',
            constraint=models.UniqueConstraint(fields=('researcher', 'director', 'start_date'), name='projects_conflictofinterest_unique'),
        ),
        migrations.AddField(
            model_name='conflictofinterest',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
