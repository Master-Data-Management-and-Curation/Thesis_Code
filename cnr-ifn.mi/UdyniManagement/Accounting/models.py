from django.db import models
from Projects.models import Researcher, Project


class GAE(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=16, unique=True, db_index=True)
    description = models.TextField()
    include_funding = models.BooleanField(default=True)

    def __str__(self):
        return "GAE {0!s}: {1!s}".format(self.name, self.description)

    class Meta:
        ordering = ["project", "name"]
        default_permissions = ()
        permissions = [
            ('gae_view', 'View GAE list'),
            ('gae_view_own', 'View GAE of own projects'),
            ('gae_manage', 'Manage GAE list'),
        ]


class VoceSpesa(models.Model):
    voce = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.CharField(max_length=300)
    depreciation = models.BooleanField(default=False)

    def __str__(self):
        return "{0:s}: {1:s}".format(self.voce, self.description)

    class Meta:
        ordering = ["voce", ]
        default_permissions = ()


class Stanziamento(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    stanziamento = models.FloatField(default=0.0)
    var_piu = models.FloatField(default=0.0)
    var_meno = models.FloatField(default=0.0)
    assestato = models.FloatField(default=0.0)
    impegnato = models.FloatField(default=0.0)
    residuo = models.FloatField(default=0.0)
    pagato = models.FloatField(default=0.0)
    da_pagare = models.FloatField(default=0.0)

    def __str__(self):
        return "Stato GAE {0!s} Voce {1!s}".format(self.gae.name, self.voce.voce)

    class Meta:
        ordering = ["gae", "esercizio", "voce"]
        constraints = [
            models.UniqueConstraint(fields=['gae', 'esercizio', 'voce', ], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


class Variazione(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10)
    numero = models.IntegerField()
    stato = models.CharField(max_length=3)
    riferimenti = models.TextField()
    descrizione = models.TextField()
    cdrSrc = models.CharField(max_length=30)
    cdrDst = models.CharField(max_length=30)
    importo = models.FloatField(default=0.0)
    data = models.DateField(null=True, blank=True)

    def __str__(self):
        return "Variazione GAE {0!s} Voce {1!s} Importo {2:.2f}".format(self.gae.name, self.voce.voce, self.importo)

    class Meta:
        ordering = ["gae", "data"]
        constraints = [
            models.UniqueConstraint(fields=['gae', 'data', 'numero', 'voce'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


class Impegno(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    esercizio_orig = models.IntegerField()
    numero = models.BigIntegerField()
    description = models.CharField(max_length=300)
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    im_competenza = models.FloatField(default=0.0)
    im_residui = models.FloatField(default=0.0)
    doc_competenza = models.FloatField(default=0.0)
    doc_residui = models.FloatField(default=0.0)
    pagato_competenza = models.FloatField(default=0.0)
    pagato_residui = models.FloatField(default=0.0)

    def __str__(self):
        return "{0:d}/{1:d}: {2:s} (Totale: {3:.2f} Pagato: {4:.2f})".format(self.numero, self.esercizio_orig, self.description, self.im_competenza+self.im_residui, self.pagato_competenza+self.pagato_residui)

    class Meta:
        ordering = ['gae', 'esercizio_orig', 'numero']
        constraints = [
            models.UniqueConstraint(fields=['gae', 'esercizio_orig', 'esercizio', 'numero'], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


class Mandato(models.Model):
    impegno = models.ForeignKey(Impegno, on_delete=models.CASCADE)
    numero = models.IntegerField()
    description = models.CharField(max_length=300)
    id_terzo = models.IntegerField()
    terzo = models.CharField(max_length=200)
    importo = models.FloatField()
    data = models.DateField()

    def __str__(self):
        return "{0:d} ({1:d}): {2:s} [€ {3:.2f}]".format(self.numero, self.impegno.esercizio, self.terzo, self.importo)

    class Meta:
        ordering = ['impegno', 'data']
        constraints = [
            models.UniqueConstraint(fields=['impegno', 'numero', ], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


#================================================
# Splitted accounting on the same GAE

class SplitContab(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    responsible = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    include_funding = models.BooleanField(default=False)
    notes = models.TextField(null=True)

    def __str__(self):
        return "GAE {0:s} (Resp. {1!s})".format(self.gae.name, self.responsible)

    class Meta:
        ordering = ['gae', 'responsible']
        constraints = [
            models.UniqueConstraint(fields=['gae', 'responsible', ], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()
        permissions = [
            ('splitcontab_view', 'View split accounting'),
            ('splitcontab_view_own', 'View own split accounting'),
            ('splitcontab_manage', 'Manage split accounting'),
            ('splitcontab_manage_own', 'Manage own split accounting'),
        ]


class SplitBudget(models.Model):
    contab = models.ForeignKey(SplitContab, on_delete=models.CASCADE)
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    year = models.IntegerField()
    importo = models.FloatField()

    class Meta:
        ordering = ['contab', 'voce', 'year']
        constraints = [
            models.UniqueConstraint(fields=['contab', 'voce', 'year', ], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


class SplitImpegno(models.Model):
    contab = models.ForeignKey(SplitContab, on_delete=models.CASCADE)
    impegno = models.ForeignKey(Impegno, on_delete=models.PROTECT)

    class Meta:
        ordering = ['contab', 'impegno']
        constraints = [
            models.UniqueConstraint(fields=['impegno', ], name="%(app_label)s_%(class)s_unique"),
        ]
        default_permissions = ()


class SplitVariazione(models.Model):
    src_contab = models.ForeignKey(SplitContab, on_delete=models.CASCADE, related_name="var_src")
    dst_contab = models.ForeignKey(SplitContab, on_delete=models.CASCADE, related_name="var_dst")
    src_voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT, related_name="var_src")
    dst_voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT, related_name="var_dst")
    importo = models.FloatField()

    class Meta:
        ordering = ['src_contab', 'dst_contab']
        default_permissions = ()
