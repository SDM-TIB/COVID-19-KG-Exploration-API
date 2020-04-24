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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



KG="https://f0ffbb86.ngrok.io/sparql"
#KG = os.environ["IASISKG_ENDPOINT"]
#all
#KG="http://node2.research.tib.eu:18873/sparql"
#KG="http://node2.research.tib.eu:11789/sparql"
#drug_pub
#KG="http://node2.research.tib.eu:11124/sparql"
EMPTY_JSON = "{}"

app = Flask(__name__)

############################
#
# Query constants
#
############################




QUERY_DRUG_TO_DRUGS_INTERACTIONS ="""
SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effectLabel ?impactLabel  WHERE {  
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug1CUI> ?effectorDrug.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug2CUI> ?affectdDrug.
                                           ?effectorDrug <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           ?affectdDrug <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasEffect> ?effect.
                                           ?effect <http://covid-19.tib.eu/vocab/effectLabel> ?effectLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasImpact> ?impact.
                                           ?impact <http://covid-19.tib.eu/vocab/impactLabel> ?impactLabel.                                       
"""

QUERY_DRUGS_TO_DRUGS_INTERACTIONS ="""
SELECT * {{
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effectLabel ?impactLabel  WHERE {{
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug1CUI> <http://covid-19.tib.eu/vocab/{0}>.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug2CUI> <http://covid-19.tib.eu/vocab/{1}>.
                                           <http://covid-19.tib.eu/vocab/{0}> <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           <http://covid-19.tib.eu/vocab/{1}> <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasEffect> ?effect.
                                           ?effect <http://covid-19.tib.eu/vocab/effectLabel> ?effectLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasImpact> ?impact.
                                           ?impact <http://covid-19.tib.eu/vocab/impactLabel> ?impactLabel.       
}}}} UNION 
{{SELECT DISTINCT ?effectorDrugLabel ?affectdDrugLabel ?effectLabel ?impactLabel  WHERE {{  
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug1CUI> <http://covid-19.tib.eu/vocab/{1}>.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasDrug2CUI> <http://covid-19.tib.eu/vocab/{0}>.
                                           <http://covid-19.tib.eu/vocab/{1}> <http://covid-19.tib.eu/vocab/drugLabel> ?effectorDrugLabel.
                                           <http://covid-19.tib.eu/vocab/{0}> <http://covid-19.tib.eu/vocab/drugLabel> ?affectdDrugLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasEffect> ?effect.
                                           ?effect <http://covid-19.tib.eu/vocab/effectLabel> ?effectLabel.
                                           ?interaction <http://covid-19.tib.eu/vocab/hasImpact> ?impact.
                                           ?impact <http://covid-19.tib.eu/vocab/impactLabel> ?impactLabel.    
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
    query+="FILTER(?affectdDrug in ("
    query+="<http://covid-19.tib.eu/vocab/"+drug+">"
    query+="))}"
        
    qresults = execute_query(query,limit,page)
    return qresults


def drugs2_interactions_query(drug_pairs,limit,page):
    query=QUERY_DRUGS_TO_DRUGS_INTERACTIONS.format(drug_pairs[0],drug_pairs[1])        
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
           
        if elem=='Drug':
            #drugs_pairs=[(x,y) for x,y in list(itertools.product(lcuis, lcuis)) if x!=y]
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
                        interaction["effect"]=result["effectLabel"]["value"]
                        interaction["impact"]=result["impactLabel"]["value"]
                        drugInteractions[drug]["DDI"].append(interaction)
        elif elem=="Drugs":
            drugs_pairs=[(x,y) for x,y in list(itertools.product(lcuis, lcuis)) if x!=y and x<y]
            for drug_pair in drugs_pairs :
                query_reslut=drugs2_interactions_query(drug_pair,limit,page)
                drugInteractions[str(drug_pair)]=dict()
                if len(query_reslut)>0:
                    drugInteractions[str(drug_pair)]["Labels"]=query_reslut[0]["affectdDrugLabel"]["value"]+" AND "+query_reslut[0]["effectorDrugLabel"]["value"]
                    drugInteractions[str(drug_pair)]["DDI"]=[]
                    for result in query_reslut:
                        interaction=dict()
                        interaction["effectorDrug"]=result["effectorDrugLabel"]["value"]
                        interaction["affectdDrug"]=result["affectdDrugLabel"]["value"]
                        interaction["effect"]=result["effectLabel"]["value"]
                        interaction["impact"]=result["impactLabel"]["value"]
                        drugInteractions[str(drug_pair)]["DDI"].append(interaction)

        
    results['DDI']=drugInteractions
    return results
           






@app.route('/exploration', methods=['POST'])
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
        response = proccesing_response(input_list,target,limit,page,sort)
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
