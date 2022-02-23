import globals
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

prefixMap = {
'http://hadatac.org/ont/chear':                         'chear',
'http://hadatac.org/chear/hasco/':                      'hasco',
'http://hadatac.org/ont/lesa':                          'lesa',
'http://hadatac.org/ont/vstoi':                         'vstoi',
'http://purl.obolibrary.org/obo/envo.owl':              'envo',
'http://purl.obolibrary.org/obo/pato.owl':              'pato',
'http://purl.obolibrary.org/obo/uo.owl':                'uo',
'http://semanticscience.org/ontology/sio.owl':          'sio',
'http://www.w3.org/1999/02/22-rdf-syntax-ns#':          'rdf',
'http://www.w3.org/2000/01/rdf-schema#':                'rdfs',
'http://www.w3.org/2002/07/owl':                        'owl',
'http://www.w3.org/ns/prov-o#':                         'provo',
'http://purl.obolibrary.org/obo/chebi.owl':             'chebi',

'http://www.cognitiveatlas.org/ontology/cogat.owl':     'cogatOld',
'http://hadatac.org/ont/cogat':                         'cogat',

'http://purl.obolibrary.org/obo/cmo.obo':               'cmo',
'http://purl.obolibrary.org/obo/doid.owl':              'doid',

'http://purl.org/twc/HHEAR':                            'hhear',
'http://purl.obolibrary.org/obo/':                      'obo',

'http://www.w3.org/ns/prov#':                           'prov'
}


def getInstalledOntologies():
    # ts_base_url = "http://localhost:9999"
    namespace = "mapper"
    blazegraphURL = globals.ts_base_url + "/blazegraph/namespace/" + namespace + "/sparql"
    sparql = SPARQLWrapper(blazegraphURL)

    sparql.setQuery("""
        prefix vann: <http://purl.org/vocab/vann/>
        select distinct ?g ?onto ?ver ?perfer ?verIRI
        where{
            graph ?g {
                ?onto a owl:Ontology .

                optional {
                    ?onto owl:versionInfo ?ver .
                }

                optional {
                    ?onto owl:versionIRI ?verIRI .
                }

                optional {
                    ?onto vann:preferredNamespaceUri ?perfer
                }
            }
        } order by asc(?g)
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    ontologies = []
    for result in results["results"]["bindings"]:

        baseUri = result["onto"]["value"]

        if "ver" in result:
            version = result["ver"]["value"]

        else:
            if "verIRI" in result:
                version = result["verIRI"]["value"]
            else:
                version = '1.0'

        # if "perfer" in result:
            # baseUri = result["perfer"]["value"]


        ontologies.append((getPrefixCC(baseUri), baseUri, version));
    return ontologies

def getFullyInstalledOntologies():
    # ts_base_url = "http://localhost:9999"
    namespace = "mapper"
    blazegraphURL = globals.ts_base_url + "/blazegraph/namespace/" + namespace + "/sparql"
    sparql = SPARQLWrapper(blazegraphURL)

    sparql.setQuery("""
        prefix vann: <http://purl.org/vocab/vann/>
        select distinct ?g ?onto ?ver ?perfer ?verIRI
        where{
            graph ?g {
                ?onto a owl:Ontology .

                optional {
                    ?onto owl:versionInfo ?ver .
                }

                optional {
                    ?onto owl:versionIRI ?verIRI .
                }

                optional {
                    ?onto vann:preferredNamespaceUri ?perfer
                }
            }
        } order by asc(?g)
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    ontologies = []
    for result in results["results"]["bindings"]:
        baseUri = result["onto"]["value"]

        if "ver" in result:
            version = result["ver"]["value"]

        else:
            if "verIRI" in result:
                version = result["verIRI"]["value"]
            else:
                version = '1.0'

        # if "perfer" in result:
        #     baseUri = result["perfer"]["value"]

        # check if we have the corresponding amr graph
        ontGraph = result["g"]["value"]

        array  = ontGraph.split('ontology')
        graphName = array[0]
        for i in range(len(array)-2):
            graphName = graphName + 'ontology' + array[i+1]
        print("graphName: " + graphName)

        amrGraph = graphName + 'amr'
        sparql.setQuery("""
            ask{
                graph <""" + amrGraph + """> {
                    ?s ?p ?o
                }
            }
            """)
        exsits = sparql.query().convert()

        if graphName in globals.ontoInProgress.keys():
            ontologies.append((getPrefixCC(baseUri), baseUri, version, exsits["boolean"], globals.ontoInProgress[graphName]), ontGraph);
        else:
            ontologies.append((getPrefixCC(baseUri), baseUri, version, exsits["boolean"], True, ontGraph));

    return ontologies

def getPrefixCC(url):

    if url not in prefixMap.keys():
        print("Had to look up: " + str(url))
        response = requests.get('https://prefix.cc/', params={'q': url})

        if(response.status_code == 201):
            prefixMap[url] = "NONE"
        else:
            prefixMap[url] = response.content.decode('utf-8').split(" | prefix.cc</title>")[0].split("<title property=\"dc:title\">")[1]

    return prefixMap[url]
