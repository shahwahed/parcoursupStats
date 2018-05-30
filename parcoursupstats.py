#!/usr/bin/python3

""" This script purpose is to fetch public data from parcoursup and put them into a CSV.
CSV Header are :
'etablissement' : school name
'ville' : school city
'academie' : French National eduction area for this school
'url' : link to parcoursup for aditionnal information
'formation' : formation name (BTS, CPGE ....)
'classes' : number of classes open
'places' : number of seat availlable this year (2018)
'places17' : number of seat availlable last year (2017)
'voeux' : number of vow this year (2018)
'voeux17' : number of vow last year (2017)
'boursier' : information about schoolarship holder seat for this formation
"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__author__ = 's. wahed'
__author_email__ = 's.wahed@laposte.net'
__license__ = 'MIT'

import sys
import csv
import requests
from pyquery import PyQuery as pq

FILENAME = 'parcoursup.csv'

formations = []

formation_critere = []
# progress_meter = 0

BASE_KEY = ['sender', 'g_ti_flg_ens_dis_1',
            'g_tf_cod', 'g_fr_cod', 'g_fl_cod',
            'g_th_cod', 'g_tc_cod', 'g_rg_cod',
            'g_aa_cod', 'g_dp_cod', 'b_cm_cod',
            'g_cn_flg_sahn', 'estIndefini',
            'tri']

HEADERS = {
    'referer':  'https://dossier.parcoursup.fr/Candidat/recherche',
    'origin':  'https://dossier.parcoursup.fr',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) ' \
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

KEYS = ['etablissement', 'ville', 'academie', 'url', 'formation',
        'classes', 'places', 'places17', 'voeux', 'voeux17', 'boursier']

#old url : 
#BASE_URL = 'https://dossier.parcoursup.fr/Candidat/'
BASE_URL = 'https://dossierappel.parcoursup.fr/Candidat/'

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    progress_bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, progress_bar, percents, '%', suffix))

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def build_data(**extra):
    """
    Call to build data to send it to form
    @params:
    BASE_KEY + header
    """
    form_data = {k: -1 for k in BASE_KEY}
    form_data['estIndefini'] = 'true'
    form_data['tri'] = 'geo'
    form_data['g_cn_flg_sahn'] = 0
    for form_keys in extra:
        form_data[form_keys] = extra[form_keys]
    return form_data


def get_formations_page(page):
    """
    Call to retrive formation in page specified in page
    @params:
    page : page number
    """
    url = BASE_URL + 'recherche?ACTION=0&page=%d' % page
    parcoursup_request = my_session.get(url, headers=HEADERS)
    parcoursup_html = pq(parcoursup_request.text)

    for elt in parcoursup_html('tr').filter('.recherche-resultat'):
        tds = pq(elt).find('td')
        etablissement = tds[1].find('strong').text.replace('\t', '')
        etablissement = etablissement.replace('\r\n', '')

        if len(tds) == 9:
            ville = tds[5].text
            academie = tds[7].text
            nom_formation = tds[2].text + ' ' + tds[3].text + ' ' + tds[4].text
        else:
            ville = tds[4].text
            academie = tds[6].text
            nom_formation = tds[2].text + ' ' + tds[3].text

        nom_formation = nom_formation.replace('\r\n', '')
        nom_formation = ' '.join(nom_formation.split())

        url = pq(elt).find('a').filter('.bouton-simple').attr['href']

        formation = {
            'etablissement': etablissement,
            'ville': ville,
            'academie': academie,
            'url': url,
            'formation': nom_formation
            }

        formations.append(formation)


def process_etablissement(formation):
    """
    Call to retrive from each formation stats
    @params:
    formation: formation dictionary
    """
    url = formation['url']
    parcoursup_request = my_session.get(BASE_URL + url, headers=HEADERS)

    parcoursup_html = pq(parcoursup_request.text)

    classes = 0
    places = 0
    places17 = 0
    voeux = 0
    voeux17 = 0
    boursier = ''

    for bloc in parcoursup_html('.blocElement'):
        bloc_query = pq(bloc)
        if bloc_query.find('.nomElement').text() != 'Chiffres':
            continue

        for chiffre in bloc_query.find('.contenu').find('tr'):
            chiffre = pq(chiffre)
            recherche_valeur_chiffre = chiffre.find('th').text()
            chiffre_etablissement = chiffre.find('td').text()
            chiffre_etablissement = ' '.join(chiffre_etablissement.split())

            if 'non disponible' in chiffre_etablissement:
                chiffre_etablissement = '-1'

            if 'Nombre de places offertes sur la plateforme :' in recherche_valeur_chiffre:
                places = int(chiffre_etablissement)

            if 'Nombre de classes :' in recherche_valeur_chiffre:
                classes = int(chiffre_etablissement)

            if "Nombre de places l'année précédente" in recherche_valeur_chiffre:
                places17 = int(chiffre_etablissement)

            if 'Nombre de voeux cette année' in recherche_valeur_chiffre:
                voeux = int(chiffre_etablissement)

            if "Nombre de voeux l'année précédente" in recherche_valeur_chiffre:
                voeux17 = int(chiffre_etablissement)

            if 'Quota de candidats boursier' in recherche_valeur_chiffre:
                boursier = chiffre_etablissement

        formation['classes'] = classes
        formation['places'] = places
        formation['places17'] = places17
        formation['voeux'] = voeux
        formation['voeux17'] = voeux17
        formation['boursier'] = boursier


def get_formations():
    """
    Call to retrive formations, get number of page for each formation in a specific city
    """
    url = BASE_URL + 'recherche?ACTION=0&page=0'
    parcoursup_request = my_session.get(url, headers=HEADERS)
    parcoursup_html = pq(parcoursup_request.text)
    page_bloc = pq(parcoursup_html('ul').filter('.pagination'))

    if page_bloc:
        page_bloc = pq(parcoursup_html('ul').filter('.pagination'))
        max_page = int(page_bloc.find('a')[-2].text) + 1
    else:
        max_page = 2

    for page in range(1, max_page):
        get_formations_page(page)


def process_formations():
    """
    Call to iterate for each formation in formations dictionary
    """
    max_meter = len(formations)
    progress_meter = 0
    print_progress(progress_meter, max_meter)
    for formation in formations:
        try:
            process_etablissement(formation)
            progress_meter = progress_meter + 1
            print_progress(progress_meter, max_meter)
        except IndexError as error:
            print(error)


def get_all_formations():
    """
    Call to iterate for all city and found all formations avaiable in this city
    """
    parcoursup_request = my_session.post(BASE_URL + \
                                         'recherche%s?ACTION=1'
                                         % (';jsessionid=' + jsessionid),
                                         data=build_data(sender='typeFormation', g_tf_cod='-1'),
                                         headers=HEADERS)

    parcoursup_html = pq(parcoursup_request.text)
    select_options = parcoursup_html('select').filter('[name="b_cm_cod"]')
    for selected_option in select_options.items('option'):
        if selected_option.attr('value') != '-1':
            filterFormation = {
                selected_option.attr('value'): selected_option.text()
                }
            formation_critere.append(filterFormation)

    max_meter = len(formation_critere)
    progress_meter = 0
    print_progress(progress_meter, max_meter)

    for critere_selected in formation_critere:
        for formationCrit_key in list(critere_selected.keys()):

            parcoursup_request = my_session.post(BASE_URL + \
                                                 'recherche?ACTION=1',
                                                 data=build_data(sender='ville',
                                                                 g_tf_cod='-1',
                                                                 b_cm_cod=formationCrit_key),
                                                 headers=HEADERS)

            url = BASE_URL + 'recherche?ACTION=2#resultats'
            parcoursup_request = my_session.get(url, headers=HEADERS)
            get_formations()
            progress_meter = progress_meter + 1

        print_progress(progress_meter, max_meter)


my_session = requests.Session()

my_session.get(BASE_URL + 'recherche', headers=HEADERS)

cookies = requests.utils.dict_from_cookiejar(my_session.cookies)
jsessionid = cookies['JSESSIONID']

print('Récupération Information Ville')
get_all_formations()

print('\r\nTraitement Formation')
process_formations()

print('\r\nEcriture fichier CSV')
with open(FILENAME, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=KEYS)
    max_meter_csv = len(formations)
    progress_meter_csv = 0
    print_progress(progress_meter_csv, max_meter_csv)

    writer.writeheader()

    for formation_item in formations:
        try:
            formation_item['url'] = BASE_URL + formation_item['url']
            writer.writerow(formation_item)
            progress_meter_csv = progress_meter_csv + 1
            print_progress(progress_meter_csv, max_meter_csv)
        except IndexError as ferror:
            print(ferror)
