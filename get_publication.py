#!/usr/bin/env python
# coding: utf-8

import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import json


def load_drug_cui(data):
    input_cui = data['drugs']
    input_cui_uri = ','.join(['<http://covid-19.tib.eu/vocab/'+cui+'>' for cui in input_cui])
    return input_cui_uri


def get_publication(input_cui_uri, sparql):
    query = """
    select distinct ?pub ?year ?journal ?title ?url ?drug ?drugLabel where {
        ?drug a <http://covid-19.tib.eu/vocab/Drug>.
        ?ann a <http://covid-19.tib.eu/vocab/Annotation>.
        ?ann <http://covid-19.tib.eu/vocab/hasAnnotation> ?drug.
        ?drug <http://covid-19.tib.eu/vocab/externalLink> ?drugID.
        ?drug <http://covid-19.tib.eu/vocab/drugLabel> ?drugLabel.
        ?ann <http://covid-19.tib.eu/vocab/annotates> ?pub.
        ?ann_cov a <http://covid-19.tib.eu/vocab/COVID_Annotation>.
        ?ann_cov <http://covid-19.tib.eu/vocab/annotates> ?pub.
        ?pub <http://covid-19.tib.eu/vocab/title> ?title.
        ?pub <http://covid-19.tib.eu/vocab/year> ?year.
        ?pub <http://covid-19.tib.eu/vocab/journal> ?journal.
        ?pub <http://covid-19.tib.eu/vocab/url> ?url.

        Filter(?drug in (""" + input_cui_uri + """))
    }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    dictionary = {}
    dictionary['Publication:'] = {}
    for r in results['results']['bindings']:
        pub = (r['pub']['value']).replace('http://covid-19.tib.eu/Publication/', '')
        year = r['year']['value']
        journal = r['journal']['value']
        title = r['title']['value']
        url = r['url']['value']
        drug = (r['drug']['value']).replace('http://covid-19.tib.eu/vocab/', '')
        drugLabel = r['drugLabel']['value']

        if pub not in dictionary['Publication:']:
            dictionary['Publication:'][pub] = {}
            dictionary['Publication:'][pub]['year:'] = year
            dictionary['Publication:'][pub]['journal:'] = journal
            dictionary['Publication:'][pub]['title:'] = title
            dictionary['Publication:'][pub]['url:'] = url
            dictionary['Publication:'][pub]['Drug:'] = []
            dictionary['Publication:'][pub]['DrugLabel:'] = []
            dictionary['Publication:'][pub]['Drug:'].append(drug)
            dictionary['Publication:'][pub]['DrugLabel:'].append(drugLabel)
        else:
            dictionary['Publication:'][pub]['Drug:'].append(drug)
            dictionary['Publication:'][pub]['DrugLabel:'].append(drugLabel)

    '''with open('publication.json', 'w') as fp:
        json.dump(dictionary, fp)'''
    return dictionary

def process(input_dicc,endpoint):
    #endpoint = "https://f0ffbb86.ngrok.io/sparql"
    sparql = SPARQLWrapper(endpoint)

    input_cui_uri = load_drug_cui(input_dicc)
    return get_publication(input_cui_uri, sparql)
