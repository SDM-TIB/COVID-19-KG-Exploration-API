#!/usr/bin/env python3
#
# Description: POST service for exploration of
# data of Lung Cancer in the iASiS KG.
#

import sys
from flask import Flask, abort, request, make_response
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import logging
import os
import itertools
import get_publication

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)




KG = os.environ["ENDPOINT"]
EMPTY_JSON = "{}"

app = Flask(__name__)

############################
#
# Query constants
#
############################




QUERY_DRUG_TO_DRUGS_INTERACTIONS ="""
SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effect AS ?effectLabel  ?impactLabel   WHERE {  
                                           ?interaction <http://covid-19.tib.eu/vocab/precipitant_hasDrugBankID> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/object_hasDrugBankID> ?affectdDrug.
                                           ?affectdDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> ?affectdDrugCUI.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectdDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                            ?interaction <http://covid-19.tib.eu/vocab/effect> ?effectCUI.
                                            ?effect <http://covid-19.tib.eu/vocab/hasCUIAnnotation>  ?effectCUI.
                                            ?effect a  <http://covid-19.tib.eu/vocab/AdverseEvent>.
                                           ?interaction <http://covid-19.tib.eu/vocab/impact> ?impactLabel.                                   
"""


QUERY_DRUG_TO_DRUGS_INTERACTIONS_PREDICTED ="""
SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?confidence ?provenance WHERE {  
                                           ?interaction a <http://covid-19.tib.eu/vocab/DrugDrugPrediction>.
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor1> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor2> ?affectdDrug.
                                           ?affectdDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> ?affectdDrugCUI.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectdDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                          ?interaction <http://covid-19.tib.eu/vocab/confidence> ?confidence.
                                           ?interaction <http://covid-19.tib.eu/vocab/predictionMethod> ?provenance.                                
"""

QUERY_DRUGS_TO_DRUGS_INTERACTIONS ="""
SELECT * {{
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effect AS ?effectLabel ?impactLabel  WHERE {{
                                           ?interaction <http://covid-19.tib.eu/vocab/precipitantDrug> <http://covid-19.tib.eu/Annotation/{0}>.
                                           ?interaction <http://covid-19.tib.eu/vocab/objectDrug> <http://covid-19.tib.eu/Annotation/{1}>.
                                           
                                           ?interaction <http://covid-19.tib.eu/vocab/precipitant_hasDrugBankID> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/object_hasDrugBankID> ?affectedDrug.
                                           
                                           
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           
                                           ?interaction <http://covid-19.tib.eu/vocab/effect> ?effectCUI.
                                           ?effect <http://covid-19.tib.eu/vocab/hasCUIAnnotation> ?effectCUI.
                                           ?effect a  <http://covid-19.tib.eu/vocab/AdverseEvent>.
                                           ?interaction <http://covid-19.tib.eu/vocab/impact> ?impactLabel.     
}}}} UNION 
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effect AS ?effectLabel ?impactLabel  WHERE {{  
                                           ?interaction <http://covid-19.tib.eu/vocab/precipitantDrug> <http://covid-19.tib.eu/Annotation/{1}>.
                                           ?interaction <http://covid-19.tib.eu/vocab/objectDrug> <http://covid-19.tib.eu/Annotation/{0}>.
                                           
                                           ?interaction <http://covid-19.tib.eu/vocab/precipitant_hasDrugBankID> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/object_hasDrugBankID> ?affectedDrug.
                                           
                                          ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/effect> ?effectCUI.
                                           ?effect <http://covid-19.tib.eu/vocab/hasCUIAnnotation> ?effectCUI.
                                           ?effect a  <http://covid-19.tib.eu/vocab/AdverseEvent>.
                                           ?interaction <http://covid-19.tib.eu/vocab/impact> ?impactLabel.
}}}}}}                                     
"""


QUERY_DRUGS_TO_DRUGS_INTERACTIONS_PREDICTED ="""
SELECT * {{
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?confidence ?provenance  WHERE {{
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor1> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor2> ?affectedDrug.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> <http://covid-19.tib.eu/Annotation/{0}>.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> <http://covid-19.tib.eu/Annotation/{1}>.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/confidence> ?confidence.
                                           ?interaction <http://covid-19.tib.eu/vocab/predictionMethod> ?provenance.       
}}}} UNION 
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?confidence ?provenance  WHERE {{  
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor1> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/interactor2> ?affectedDrug.
                                            ?effectorDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> <http://covid-19.tib.eu/Annotation/{1}>.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/hasCUIAnnotation> <http://covid-19.tib.eu/Annotation/{0}>.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectedDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/confidence> ?confidence.
                                           ?interaction <http://covid-19.tib.eu/vocab/predictionMethod> ?provenance.    
}}}}}}                                     
"""
############################
#
# Query generation
#
############################


def execute_query(query,limit,page):
    if limit!=0:
       query+="LIMIT "+str(limit)
    query+=" OFFSET "+str(page)   
    sparql_ins = SPARQLWrapper(KG)
    sparql_ins.setQuery(query)
    sparql_ins.setReturnFormat(JSON)
    return sparql_ins.query().convert()['results']['bindings']



############################
#
# Processing results
#
############################

def drug2_interactions_query(drug,limit,page):
    query=QUERY_DRUG_TO_DRUGS_INTERACTIONS
    query+="FILTER(?affectdDrugCUI in ("
    query+="<http://covid-19.tib.eu/Annotation/"+drug+">"
    query+="))}"
        
    qresults = execute_query(query,limit,page)
    return qresults


def drug2_interactions_predicted_query(drug,limit,page):
    query=QUERY_DRUG_TO_DRUGS_INTERACTIONS_PREDICTED
    query+="FILTER(?affectdDrugCUI in ("
    query+="<http://covid-19.tib.eu/Annotation/"+drug+">"
    query+="))}"
        
    qresults = execute_query(query,limit,page)
    return qresults


def drugs2_interactions_query(drug_pairs,limit,page):
    query=QUERY_DRUGS_TO_DRUGS_INTERACTIONS.format(drug_pairs[0],drug_pairs[1])        
    qresults = execute_query(query,limit,page)
    return qresults


def drugs2_interactions_predicted_query(drug_pairs,limit,page):
    query=QUERY_DRUGS_TO_DRUGS_INTERACTIONS_PREDICTED.format(drug_pairs[0],drug_pairs[1])        
    qresults = execute_query(query,limit,page)
    return qresults


def proccesing_response(input_dicc, target,limit,page,sort):
    cuis=dict()
    results=dict()

    drugInteractions=dict()
    for elem in input_dicc:
        lcuis = input_dicc[elem]
        if len(lcuis)==0:
            continue
        for item in lcuis:
            cuis[item]=elem

        if len(cuis)==0:
            continue

   
       ############################Interactions#####################################         
           
        if elem=='Drugs':
            if target=="DDI":
                for drug in lcuis:
                    query_reslut=drug2_interactions_query(drug,limit,page)
                    drugInteractions[drug]=dict()
                    if len(query_reslut)>0:
                        drugInteractions[drug]["Label"]=query_reslut[0]["affectdDrugLabel"]["value"]
                        drugInteractions[drug]["DDI"]=[]
                        for result in query_reslut:
                            interaction=dict()
                            interaction["effectorDrug"]=result["effectorDrugLabel"]["value"]
                            interaction["affectdDrug"]=result["affectdDrugLabel"]["value"]
                            interaction["effect"]=result["effectLabel"]["value"].replace('http://covid-19.tib.eu/AdverseEvent/','').split('_')[0]
                            interaction["impact"]=result["impactLabel"]["value"]
                            drugInteractions[drug]["DDI"].append(interaction)
            elif target=="DDIS":
                drugs_pairs=[(x,y) for x,y in list(itertools.product(lcuis, lcuis)) if x!=y and x<y]
                for drug_pair in drugs_pairs :
                    query_reslut=drugs2_interactions_query(drug_pair,limit,page)
                    drugInteractions[str(drug_pair)]=dict()
                    if len(query_reslut)>0:
                        drugInteractions[str(drug_pair)]["Labels"]=query_reslut[0]["affectdDrugLabel"]["value"]+" AND "+query_reslut[0]["effectorDrugLabel"]["value"]
                        drugInteractions[str(drug_pair)]["DDIS"]=[]
                        for result in query_reslut:
                            interaction=dict()
                            interaction["effectorDrug"]=result["effectorDrugLabel"]["value"]
                            interaction["affectdDrug"]=result["affectdDrugLabel"]["value"]
                            interaction["effect"]=result["effectLabel"]["value"].replace('http://covid-19.tib.eu/AdverseEvent/','').split('_')[0]
                            interaction["impact"]=result["impactLabel"]["value"]
                            if interaction not in drugInteractions[str(drug_pair)]["DDIS"]:
                                drugInteractions[str(drug_pair)]["DDIS"].append(interaction)
            elif target=="DDIP":
                #drugs_pairs=[(x,y) for x,y in list(itertools.product(lcuis, lcuis)) if x!=y]
                for drug in lcuis:
                    query_reslut=drug2_interactions_predicted_query(drug,limit,page)
                    drugInteractions[drug]=dict()
                    if len(query_reslut)>0:
                        drugInteractions[drug]["Label"]=query_reslut[0]["affectdDrugLabel"]["value"]
                        drugInteractions[drug]["DDIP"]=[]
                        for result in query_reslut:
                            interaction=dict()
                            interaction["effectorDrug"]=result["effectorDrugLabel"]["value"]
                            interaction["affectdDrug"]=result["affectdDrugLabel"]["value"]
                            interaction["confidence"]=result["confidence"]["value"]
                            interaction["provenance"]=result["provenance"]["value"]
                            drugInteractions[drug]["DDIP"].append(interaction)
            elif target=="DDIPS":
                drugs_pairs=[(x,y) for x,y in list(itertools.product(lcuis, lcuis)) if x!=y and x<y]
                for drug_pair in drugs_pairs :
                    query_reslut=drugs2_interactions_predicted_query(drug_pair,limit,page)
                    drugInteractions[str(drug_pair)]=dict()
                    if len(query_reslut)>0:
                        drugInteractions[str(drug_pair)]["Labels"]=query_reslut[0]["affectdDrugLabel"]["value"]+" AND "+query_reslut[0]["effectorDrugLabel"]["value"]
                        drugInteractions[str(drug_pair)]["DDIPS"]=[]
                        for result in query_reslut:
                            interaction=dict()
                            interaction["effectorDrug"]=result["effectorDrugLabel"]["value"]
                            interaction["affectdDrug"]=result["affectdDrugLabel"]["value"]
                            interaction["confidence"]=result["confidence"]["value"]
                            interaction["provenance"]=result["provenance"]["value"]
                            drugInteractions[str(drug_pair)]["DDIPS"].append(interaction)

        
    results['Interactions']=drugInteractions
    return results
           






@app.route('/covid19kg-exp', methods=['POST'])
def run_exploration_api():
    if (not request.json):
        abort(400)
    if 'limit' in request.args:
        limit = int(request.args['limit'])
    else:
        limit = 0
    if 'page' in request.args:
        page = int(request.args['page'])
    else:
        page = 0
    if 'sort' in request.args:
        sort = request.args['sort']
    else:
        sort = 0
    if 'target' in request.args:
        target = request.args['target']
    else:
        abort(400)


    input_list = request.json
    if len(input_list) == 0:
        logger.info("Error in the input format")
        r = "{results: 'Error in the input format'}"
    else:
        if target!="Pub":
            response = proccesing_response(input_list,target,limit,page,sort)       
        elif target=="Pub":
            response=get_publication.process(input_list,KG)
    r = json.dumps(response, indent=4)  
    logger.info("Sending the results: ")
    response = make_response(r, 200)
    response.mimetype = "application/json"
    return response

def main(*args):
    if len(args) == 1:
        myhost = args[0]
    else:
        myhost = "0.0.0.0"
    app.run(debug=False, host=myhost)
    
if __name__ == '__main__':
     main(*sys.argv[1:])
