import time
import datetime
import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from Accounting.models import GAE, VoceSpesa, Stanziamento, Variazione, Impegno, Mandato
from sigla.sigla import SIGLA


class Command(BaseCommand):
    help = 'Sincronizzazione stanziamenti, variazioni, impegni and mandati con SIGLA'

    def handle(self, *args, **options):
        # Carichiamo il logger specifico
        self.logger = logging.getLogger('UpdateFunds')
        self.logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

        # Definiamo il formattatore
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Aggiungiamo il console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Aggiungiamo il file handler
        fh = logging.FileHandler(os.path.join(settings.BASE_DIR, "updatefunds.log"))
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Carichiamo l'intefaccia per SIGLA
        sigla = SIGLA(settings.SIGLA_USERNAME, settings.SIGLA_PASSWORD, self.logger)

        # Prima di tutto carichiamo l'elenco dei progetti
        # NOTA: li carichiamo tutti, perchè una call per progetto è troppo lento (ogni call richiede qualche secondo...)
        progetti = sigla.getProgetti()

        # Carichiamo tutte le GAE definite nel DB
        gaes = GAE.objects.all()

        # Aggiorniamo le informazioni per ogni GAE
        for gae in gaes:
            s = time.time()

            # Selezioniamo il progetto e la data di inizio
            prj = gae.project.sigla_name
            start = progetti[prj]['start']

            # Creiamo la lista di anni da controllare
            years = list(range(start.year, datetime.date.today().year + 1, 1))

            for y in years:
                try:
                    # Carichiamo prima la competenza
                    c = sigla.getCompetenza(gae.name, y)

                    # Analizziamo ogni voce di spesa presente
                    new_pk = []
                    for k, v in c.items():

                        # Cerchiamo la voce nel DB
                        try:
                            voce = VoceSpesa.objects.get(voce=k)
                        except VoceSpesa.DoesNotExist:
                            # La voce non esiste. La aggiungiamo.
                            voce = VoceSpesa()
                            voce.voce = k
                            voce.description = v['descrizione']
                            voce.save()

                        # Cerchiamo se lo stanziamento esiste già
                        try:
                            stanziamento = Stanziamento.objects.get(gae=gae, esercizio=y, voce=voce)
                        except Stanziamento.DoesNotExist:
                            # Non esiste. Lo aggiungiamo.
                            stanziamento = Stanziamento()
                            stanziamento.gae = gae
                            stanziamento.voce = voce
                            stanziamento.esercizio = y

                        # Aggiorniamo lo stanziamento se necessario
                        stanziamento.stanziamento = v['stanziamento']
                        stanziamento.var_piu = v['var_piu']
                        stanziamento.var_meno = v['var_meno']
                        stanziamento.assestato = v['assestato']
                        stanziamento.impegnato = v['impegnato']
                        stanziamento.residuo = v['residuo']
                        stanziamento.pagato = v['pagato']
                        stanziamento.da_pagare = v['dapagare']
                        stanziamento.save()
                        new_pk.append(stanziamento.pk)
                        if settings.DEBUG:
                            self.logger.debug(f"Aggiornato lo stanziamento per la GAE {gae}, anno {y:d}, voce {k}")

                    # Cancelliamo gli stanziamenti che non sono stati aggiornati, altrimenti i residui si sommerebbero ad ogni aggiornamento.
                    Stanziamento.objects.filter(Q(gae=gae, esercizio=y) & ~Q(pk__in=new_pk)).delete()

                    # Ogni stanziamento di competenza deve essere aggiornato con le modifiche degli anni successivi
                    # attraverso i residui

                    for res_y in range(y + 1, years[-1] + 1, 1):
                        r = sigla.getResidui(gae.name, res_y, y)

                        # Analizziamo ogni voce di spesa presente
                        for k, v in r.items():
                            try:
                                voce = VoceSpesa.objects.get(voce=k)
                            except VoceSpesa.DoesNotExist:
                                # La voce non esiste. La aggiungiamo.
                                voce = VoceSpesa()
                                voce.voce = k
                                voce.description = v['descrizione']
                                voce.save()

                            try:
                                # Cerchiamo lo stanziamento corrispondente se esite
                                stanziamento = Stanziamento.objects.get(gae=gae, esercizio=y, voce=voce)

                            except Stanziamento.DoesNotExist:
                                # Se non esiste lo creiamo a zero
                                stanziamento = Stanziamento()
                                stanziamento.gae = gae
                                stanziamento.voce = voce
                                stanziamento.esercizio = y
                                stanziamento.stanziamento = 0.0
                                stanziamento.var_piu = 0.0
                                stanziamento.var_meno = 0.0
                                stanziamento.assestato = 0.0
                                stanziamento.impegnato = 0.0
                                stanziamento.residuo = 0.0
                                stanziamento.pagato = 0.0
                                stanziamento.da_pagare = 0.0

                            # Aggiorniamo lo stanziamento
                            stanziamento.var_piu += v['esercizi'][y]['var_piu_imp']
                            stanziamento.var_meno += v['esercizi'][y]['var_meno_imp']
                            #stanziamento.assestato = v['esercizi'][y]['assestato'] # NOTE: questo assestato si riferisce allo stanziamento improprio del residuo...
                            stanziamento.assestato += (v['esercizi'][y]['var_piu_imp'] - v['esercizi'][y]['var_meno_imp'])
                            stanziamento.impegnato += v['esercizi'][y]['var_piu_obblpro'] - v['esercizi'][y]['var_meno_obblpro'] + v['esercizi'][y]['impegnato']
                            stanziamento.residuo = v['esercizi'][y]['residuo']
                            stanziamento.pagato += v['esercizi'][y]['pagato']
                            stanziamento.da_pagare = v['esercizi'][y]['dapagare']
                            stanziamento.save()

                except Exception as e:
                    self.logger.error(f"Errore nell'aggiornamento degli stanziamenti per la GAE {gae.name} per l'anno {y:d} (Errore: {e})")

                try:
                    # Carichiamo le variazioni alla GAE
                    v = sigla.getVariazioni(gae.name, y)

                    for var in v:
                        # Cerchiamo la voce di spesa
                        try:
                            voce = VoceSpesa.objects.get(voce=var['voce'])
                        except VoceSpesa.DoesNotExist:
                            # La voce di spesa non esiste. Questo può capitare quando la variazione è diretta ad una GAE esterna (e.g. trasferimenti)
                            voce = VoceSpesa()
                            voce.voce = var['voce']
                            voce.description = 'N.D.'
                            voce.save()

                        try:
                            variazione = Variazione.objects.get(gae=gae, data=var['data'], numero=var['numero'], voce=voce)
                            if y < datetime.date.today().year:
                                # Se la variazione esiste già ed è relativa ad un anno passato, la possiamo lasciare così com'è perchè
                                # non può essere stata modificata
                                continue
                        except Variazione.DoesNotExist:
                            # La variazione non esiste, la creiamo
                            variazione = Variazione()
                            variazione.gae = gae
                            if var['tipo'] == 'Residuo':
                                variazione.esercizio = var['es_residuo']
                            else:
                                variazione.esercizio = y
                            variazione.numero = var['numero']
                            variazione.voce = voce
                            if settings.DEBUG:
                                self.logger.debug(f"Aggiungo la variazione {var['numero']:d} per la GAE {gae.name}, anno {y:d}, voce {var['voce']}")

                        # Aggiorniamo la variazione se necessario
                        variazione.tipo = var['tipo']
                        variazione.stato = var['stato']
                        variazione.riferimenti = var['riferimenti'] if var['riferimenti'] is not None else "None"
                        variazione.descrizione = var['descrizione'] if var['descrizione'] is not None else "None"
                        variazione.cdrSrc = var['cdr_prop']
                        variazione.cdrDst = var['cdr_ass']
                        variazione.importo = var['importo']
                        variazione.data = var['data']
                        variazione.save()

                except Exception as e:
                     self.logger.error(f"Errore nell'aggiornamento delle variazioni per la GAE {gae.name}, anno {y:d} (Errore: {e})")

                try:
                    # Scarichiamo tutti gli impegni
                    impegni = sigla.getImpegni(gae.name, y)

                    for im in impegni:
                        # Cerchiamo la voce di spesa
                        try:
                            voce = VoceSpesa.objects.get(voce=im['voce'])
                        except VoceSpesa.DoesNotExist:
                            # La voce di spesa non esiste. Questo è un errore e non dovrebbe succedere
                            # La voce dovrebbe essere stata aggiunta nello step di aggiornamento dei fondi disponibili
                            self.logger.error(f"La voce {im['voce']} non esiste nel database. Questo non dovrebbe essere possibile (GAE: {gae.name}, esercizio: {y:d}, impegno: {im['impegno']:d})")
                            continue

                        try:
                            impegno = Impegno.objects.get(gae=gae, esercizio=y, esercizio_orig=im['esercizio_orig'], numero=im['impegno'])
                            if y < datetime.date.today().year:
                                # Se l'impegno esiste già ed è relativo ad un anno precedente, possiamo lasciarlo così com'è perché non può essere cambiato
                                continue
                        except Impegno.DoesNotExist:
                            # L'impegno non esiste. Lo aggiungiamo.
                            impegno = Impegno()
                            impegno.gae = gae
                            impegno.esercizio = y
                            impegno.esercizio_orig = im['esercizio_orig']
                            impegno.numero = im['impegno']
                            impegno.voce = voce
                            if settings.DEBUG:
                                self.logger.debug(f"Aggiungo l'impegno {im['impegno']:d} per la GAE {gae.name}, anno {y:d}, voce {im['voce']}")

                        # Update impegno if needed
                        impegno.description = im['descrizione']
                        impegno.im_competenza = im['competenza']
                        impegno.im_residui = im['residui']
                        impegno.doc_competenza = im['doc_competenza']
                        impegno.doc_residui = im['doc_residuo']
                        impegno.pagato_competenza = im['pagato_competenza']
                        impegno.pagato_residui = im['pagato_residuo']
                        impegno.save()

                except Exception as e:
                    self.logger.error(f"Errore nell'aggiornamento degli impegni per la GAE {gae.name} per l'anno {y:d} (Errore: {e})")

            if settings.DEBUG:
                self.logger.debug(f"GAE {gae.name} completata in {time.time() - s:.2f}s")

        # Cancelliamo tutti i mandati per ricaricarli
        Mandato.objects.all().delete()

        # Carichiamo i mandati per ciascun impegno registrato
        for im in Impegno.objects.all():
            try:
                if settings.DEBUG:
                    self.logger.debug(f"Verifichiamo l'impegno {im}")
                mandati = sigla.getMandati(im.numero, im.esercizio_orig, im.esercizio)
                if not len(mandati):
                    continue

                for m in mandati:
                    # Se il mandato non ha data lo saltiamo perchè vuol dire che non è stato ancora pagato
                    if m['data'] is None:
                        continue
                    # Se il mandato è annullato lo ignoriamo
                    if m['stato'] == 'A':
                        continue

                    try:
                        mandato = Mandato.objects.get(impegno=im, numero=m['numero'])
                        # Esiste già un mandato relativo all'impegno con lo stesso numero. Questo vuol dire
                        # che ci sono più fatture con importi diversi, relative allo stesso impegno, pagate
                        # con lo stesso mandato. Le sommiamo insieme.
                        mandato.importo += m['importo']
                        mandato.save()
                    except Mandato.DoesNotExist:
                        mandato = Mandato()
                        mandato.impegno = im
                        mandato.numero = m['numero']
                        mandato.description = m['descrizione']
                        mandato.id_terzo = m['id_terzo']
                        mandato.terzo = m['terzo']
                        mandato.importo = m['importo']
                        mandato.data = m['data']
                        mandato.save()

                        if settings.DEBUG:
                            self.logger.debug(f"Aggiungo il mandato {mandato.numero:d} per l'impegno {mandato.impegno.numero:d}/{mandato.impegno.esercizio_orig:d}")

            except Exception as e:
                self.logger.error(f"Errore nel recupero dei mandati per l'impegno {im.numero}/{im.esercizio_orig} per l'anno {im.esercizio:d} (Errore: {e})")

    # TODO: aggiungere un check sugli impegni / mandati dello SplitAccounting per gestire gli impegni pagati su più anni.
