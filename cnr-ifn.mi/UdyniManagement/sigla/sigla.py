# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 16:39:01 2022

Python API for SIGLA

@author: Michele Devetta <michele.devetta@cnr.it>
"""

import time
import datetime
import requests
import json
import logging


class SIGLA(object):

    def __init__(self, username, password, logger=None):
        """ Initialize object
        """
        # Check logger
        if logger is None:
            # Start logger
            self.logger = logging.getLogger('SIGLA')
            self.logger.setLevel(logging.INFO)

            # Define formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # Add console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        else:
            self.logger = logger

        # Store credentials
        self.__credentials = (username, password)
        self.__cds = "036"
        self.__cdu = "036.001"
        self.__cdr = "036.001.000"
        self.__base_url = "https://contab.cnr.it/SIGLA/"


    def getCds(self):
        return self.__cds


    def getCdu(self):
        return self.__cdu


    def getCdr(self):
        return self.__cdr


    def getRequest(self, url):
        r = requests.get("{0:s}{1:s}?proxyUrl={1:s}".format(self.__base_url, url), auth=self.__credentials)
        if r.status_code == 200:
            try:
                data = json.loads(r.content)
            except Exception as e:
                try:
                    data = json.loads(r.content.decode('ISO-8859-1'))
                except:
                    raise e
            if 'elements' in data:
                return data['elements']
            else:
                return data
        else:
            try:
                message = str(json.loads(r.content)['message'])
            except:
                message = "Fetch failed"
            raise requests.HTTPError('[Error {0:d}] {1:s}'.format(r.status_code, message))


    def postRequest(self, url, filters=[], esercizio=datetime.date.today().year):
        # Process filters
        clauses = []
        for f in filters:
            if type(f) is dict:
                for k, v in f:
                    clauses.append({"condition":"AND", "fieldName": k, "operator":"=", "fieldValue": v})
            elif type(f) is tuple:
                if len(f) > 2:
                    clauses.append({"condition":f[2], "fieldName": f[0], "operator":"=", "fieldValue": f[1]})
                else:
                    clauses.append({"condition":"AND", "fieldName": f[0], "operator":"=", "fieldValue": f[1]})

        # Initialize request
        ipp = 200
        request = {
            "maxItemsPerPage": ipp,
            "activePage": 0,
            "context": {
                "cd_unita_organizzativa": self.__cdu,
                "cd_cds": self.__cds,
                "cd_cdr": self.__cdr,
                "esercizio": esercizio,
            },
            "clauses": clauses,
        }

        out = []
        total_items = None
        while True:
            r = requests.post("{0:s}{1:s}?proxyUrl={1:s}".format(self.__base_url, url), json=request, auth=self.__credentials)
            if r.status_code == 200:
                try:
                    data = r.content.decode('utf-8')
                    data = json.loads(data)
                except Exception as e:
                    try:
                        data = json.loads(r.content.decode('ISO-8859-1'))
                    except:
                        raise e
                # Get total items if needed
                if total_items is None:
                    total_items = data['totalNumItems']

                # Store data
                out += data['elements']

                if data['activePage'] * ipp + len(data['elements']) < total_items:
                    request['activePage'] += 1
                    continue
                break

            else:
                try:
                    message = str(json.loads(r.content)['message'])
                except:
                    message = "Fetch failed"
                raise requests.HTTPError('[Error {0:d}] {1:s}'.format(r.status_code, message))

        self.logger.debug("[SIGLA] Got {0!s} Results: {1:d}".format(url, total_items))

        return out


    def getProgetti(self, pg_progetto=None):
        # Load data
        s = time.time()
        filters = []
        if pg_progetto is not None:
            filters.append(('pg_progetto', pg_progetto))
        data = self.postRequest('ConsProgettiAction.json', filters=filters)
        self.logger.debug("Progetti retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        projects = {}
        for el in data:
            projects[el['cd_progetto']] = {
                'id': el['pg_progetto'],
                'desc': el['ds_progetto'],
                'start': datetime.date.fromtimestamp(el['dt_inizio'] / 1000) if el['dt_inizio'] is not None else None,
                'end': datetime.date.fromtimestamp(el['dt_fine'] / 1000) if el['dt_fine'] is not None else None,
                'cup': el['cd_cup'],
            }

        return projects


    def getGAE(self, pg_progetto):
        # Load data
        s = time.time()
        data = self.postRequest('ConsGAEAction.json', filters=[('pg_progetto', pg_progetto)])
        self.logger.debug("GAE retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        gae = {}
        for el in data:
            gae[el['cd_linea_attivita']] = el['ds_linea_attivita']

        return gae


    def filterVoce(self, voce):
        filter_map = {
            '1.01.03.01.02.007.01': '13012',  # Altri materiali tecnico-specialistici non sanitari
            '1.01.03.01.02.999.01': '13017',  # Altri beni e materiali di consumo
            '1.01.03.02.09.005.01': '13074',  # Manutenzione ordinaria e riparazioni di attrezzature
            '1.01.03.02.11.009.01': '13083',  # Prestazioni tecnico-scientifiche a fini di ricerca
            '1.01.03.02.12.003.01': '13087',  # Collaborazioni coordinate e a progetto
            '1.02.02.01.05.001.01': '22010',  # Attrezzature scientifiche
        }

        if voce in filter_map:
            return filter_map[voce]
        else:
            return voce


    def getCompetenza(self, gae, esercizio):
        # Load data
        s = time.time()
        data = self.postRequest('ConsGaeCompetenzaAction.json', filters=[('cdCentroResponsabilita', self.getCdr()), ('cdLineaAttivita', gae), ('esercizio', esercizio)])
        self.logger.debug("Competenza retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        gae = {}
        for el in data:
            voce = self.filterVoce(el['cdElementoVoce'])
            gae[voce] = {
                'descrizione': el['dsElementoVoce'],
                'stanziamento': el['imStanzInizialeA1'],
                'var_piu': el['variazioniPiu'],
                'var_meno': el['variazioniMeno'],
                'assestato': el['assestatoComp'],
                'impegnato': el['imObblAccComp'],
                'residuo': el['daAssumere'],
                # '': el['imAssDocAmmSpe'],
                # '': el['imAssDocAmmEtr'],
                'pagato': el['imMandatiReversaliPro'],
                'dapagare': el['daPagareIncassare'],
            }

        return gae


    def getResidui(self, gae, esercizio=datetime.date.today().year, esercizio_residuo=None):
        # Load data
        s = time.time()
        if esercizio_residuo is not None:
            data = self.postRequest('ConsGAEResSpeVocAction.json', filters=[('cd_centro_responsabilita', self.getCdr()), ('cd_linea_attivita', gae), ('esercizio', esercizio), ('esercizio_res', esercizio_residuo)], esercizio=esercizio)
        else:
            data = self.postRequest('ConsGAEResSpeVocAction.json', filters=[('cd_centro_responsabilita', self.getCdr()), ('cd_linea_attivita', gae), ('esercizio', esercizio)], esercizio=esercizio)
        self.logger.debug("Residui retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        gae = {}
        for el in data:
            voce = self.filterVoce(el['cd_elemento_voce'])
            if voce not in gae:
                gae[voce] = {
                    'descrizione': el['ds_elemento_voce'],
                    'esercizi': {},
                }
            gae[voce]['esercizi'][el['esercizio_res']] = {
                'stanz_improprio': el['im_stanz_res_improprio'],
                'stanz_proprio': el['iniziale'],
                'var_piu_imp': el['var_piu_stanz_res_imp'],
                'var_meno_imp': el['var_meno_stanz_res_imp'],
                'var_piu_obblpro': el['var_piu_obbl_res_pro'],
                'var_meno_obblpro': el['var_meno_obbl_res_pro'],
                'assestato': el['ass_res_imp'],
                'impegnato': el['im_obbl_res_imp'],
                'residuo': el['disp_res'],
                'pagato': el['pagato_totale'],
                'dapagare': el['rimasti_da_pagare'],
            }

        return gae


    def getImpegni(self, gae, esercizio):
        # Load data
        s = time.time()
        data = self.postRequest('ConsImpegnoGaeAction.json', filters=[('cdUnitaOrganizzativa', self.getCdu()), ('cdLineaAttivita', gae), ('esercizio', esercizio), ])
        self.logger.debug("Impegni retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        impegni = []
        for el in data:
            impegni.append({
                'esercizio': el['esercizio'],
                'esercizio_orig': el['esercizioOriginale'],
                'impegno': el['pgObbligazione'],
                'descrizione': el['dsObbligazione'],
                'voce': self.filterVoce(el['cdElementoVoce']),
                'competenza': el['imScadenzaComp'],
                'residui': el['imScadenzaRes'],
                'doc_competenza': el['imAssociatoDocAmmComp'],
                'doc_residuo': el['imAssociatoDocAmmRes'],
                'pagato_competenza': el['imPagatoComp'],
                'pagato_residuo': el['imPagatoRes'],
           })

        return impegni


    def getVariazioni(self, gae, esercizio):
        # Load data
        s = time.time()
        data = self.postRequest('ConsVarCompResAction.json', filters=[('gae', gae), ('esercizio', esercizio), ], esercizio=esercizio)
        self.logger.debug("Variazioni retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        variazioni = []
        for el in data:
            # Extract importo
            importo = 0.0
            for im in ['importo', 'imDecInt', 'imDecEst', 'imAccInt', 'imAccEst', 'imEntrata']:
                if el[im] != 0:
                    self.logger.debug("[Var] Found non-null '{0:s}', value = {1:.2f}".format(im, el[im]))
                    if importo == 0:
                        importo = el[im]
                    else:
                        if importo != el[im]:
                            # TODO: handle better!
                            self.logger.error("[Var] Found a non matching importo!!!")

            variazioni.append({
                'tipo': el['tipoVar'],
                'numero': el['numVar'],
                'stato': el['stato'],
                'riferimenti': el['riferimentiDescVariazione'],
                'descrizione': el['descVariazione'],
                'cdr_prop': el['cdrProponente'],
                'cdr_ass': el['cdrAssegn'],
                'es_residuo': el['esResiduo'],
                'importo': importo,
                'voce': self.filterVoce(el['voceDelPiano']),
                'data': datetime.date.fromtimestamp(el['dtApprovazione']/1000) if el['dtApprovazione'] else None
           })

        return variazioni


    def getMandati(self, obbligazione, esercizio_orig, esercizio):
        s = time.time()
        data = self.postRequest('ConsRicercaMandatiPerTerzoAction.json', filters=[('pg_obbligazione', obbligazione), ('esercizio_ori_obbligazione', esercizio_orig)], esercizio=esercizio)
        self.logger.debug("Mandati retrieved in {0:.2f}s".format(time.time() - s))

        # Extract needed data
        mandati = []
        try:
            for el in data:
                mandati.append({
                    'numero': el['pg_mandato'],
                    'descrizione': el['ds_mandato'],
                    'id_terzo': el['cd_terzo'],
                    'terzo': el['denominazione_sede'],
                    'importo': el['im_mandato_riga'],
                    'voce': self.filterVoce(el['cd_elemento_voce']),
                    'stato': el['stato_mandato'],
                    'data': datetime.date.fromtimestamp(el['dt_pagamento']/1000) if el['dt_pagamento'] else None,
                    'annullamento': datetime.date.fromtimestamp(el['dt_annullamento']/1000) if el['dt_annullamento'] else None,
                })
        except Exception as e:
            self.logger.error("[{0:s}] {1!s} (Obbl.: {2:d} Es. orig.: {3:d} Es.: {4:d}".format(type(e).__name__, e, obbligazione, esercizio_orig, esercizio))
            return []

        return mandati


    def getFatture(self, mandato, esercizio):
        s = time.time()
        fatture = []
        # First retrieve pg_docamm from ConsMandatoRigaAction.json
        data = self.postRequest('ConsMandatoRigaAction.json', filters=[('pg_mandato', mandato), ('esercizio', esercizio), ], esercizio=esercizio)
        if len(data):
            for el in data:
                obj = {
                    'esercizio': el['esercizio'],
                    'mandato': el['pg_mandato'],
                    'esercizio_impegno': el['esercizio_obbligazione'],
                    'impegno': el['pg_obbligazione'],
                    'tipo': el['cd_tipo_documento_amm'],
                    'importo': el['im_mandato_riga'],
                }
                if el['cd_tipo_documento_amm'] == 'FATTURA_P':
                    df = self.postRequest('ConsFatturaPassivaAction.json', filters=[('pgFatturaPassiva', el['pg_doc_amm']), ('cdUnitaOrganizzativa', self.getCdu()), ('esercizio', esercizio), ], esercizio=esercizio)
                    obj['pg_fattura'] = df[0]['pgFatturaPassiva']
                    obj['nr_fattura'] = df[0]['nrFatturaFornitore']
                    obj['dt_fattura'] = df[0]['dtFatturaFornitore']
                    obj['imponibile'] = df[0]['imTotaleImponibile']
                    obj['iva'] = df[0]['imTotaleIva']
                    obj['totale'] = df[0]['imTotaleFattura']
                fatture.append(obj)

        self.logger.debug("Fatture retrieved in {0:.2f}s".format(time.time() - s))
        return fatture
