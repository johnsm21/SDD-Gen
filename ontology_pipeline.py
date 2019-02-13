from rdflib import Graph
import os
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

import sys
sys.path.append('lib/camr/')

import amr_parsing

def ingest(file):
    # Figure out what ontology this is
    ontology = None
    version = None

    g = Graph()
    g.parse(file)
    print("number of triples "+ str(g))

    res = g.query(
    """select ?onto ?ver
        where{
            ?onto a owl:Ontology .
            ?onto owl:versionInfo ?ver .
        }""")

    for row in res:
        ontology = row.onto
        version = row.ver
    g = None # Release resources


    # Create a namespace for it
    url = "http://localhost:9999"
    namespace = ontology + "/" + version
    namespace = namespace.replace(".", "_").replace("http://", "").replace("https://", "").replace("/", "-")

    # Check if namespace exits

    # Generate namespace
    result = generateNameSpace(url, namespace)
    if result:
        print("Created " + namespace)
    else:
        print("Couldn't create " + namespace)
        return False


    # Load Ontology into namespace
    result = loadNameSpace(url, namespace, file)
    if result:
        print("Finished loading triples!")
    else:
        print("Couldn't create loading triples")
        return False

    # Generate a description file for AMR
    descriptFile = file + ".txt"
    generateAMRTextFile(url + "/blazegraph/namespace/" + namespace + "/sparql", descriptFile)
    print("generated description file!")


    # Run AMR
    model = 'lib/amr-semeval-all.train.basic-abt-brown-verb.m'

    # run the preprocessor
    sys.argv = ['amr_parsing.py','-m', 'preprocess', descriptFile]
    amr_parsing.main()

    # run the parser
    sys.argv = ['amr_parsing.py','-m', 'parse', '--model', model, descriptFile]
    amr_parsing.main()
    print("Finished Running AMR")

    return True


def generateAMRTextFile(blazegraphURL, file):
    sparql = SPARQLWrapper(blazegraphURL)
    sparql.setQuery("""
        PREFIX dcterm: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?class ?className ?description
        WHERE{
            ?class a owl:Class ;
            rdfs:label ?className ;
            dcterm:description ?description  ;
        } order by asc(?className)
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    classIndex = []
    with open(file, 'w') as the_file:
        for result in results["results"]["bindings"]:
            classIRI = result["class"]["value"]
            className = result["className"]["value"]
            description = result["description"]["value"]
            classIndex.append((classIRI, className))

            # If there are multiple sentences only look at the first one
            sentence = description.split(".")[0].replace('\n', ' ')
            the_file.write(sentence + "." + '\n')

# curl -X POST http://localhost:9999/blazegraph/namespace/semanticscience_org-ontology-sio_owl-1_43/sparql
    # --data-urlencode 'update=DROP ALL; LOAD <file:///Users/mjohnson/Projects/python-rest/flask-tutorial/temp/sio.owl>;'
def loadNameSpace(blazegraphURL, namespace, file):
    filepath = os.path.abspath(file)
    print("Filepath = " + filepath)
    data = {"update":"DROP ALL; LOAD <file://" + filepath + ">;"}

    response = requests.post(blazegraphURL + "/blazegraph/namespace/" + namespace + "/sparql", data=data)
    return response.status_code == 200


def generateNameSpace(blazegraphURL, namespace):
    headers = {
        'Content-Type': 'application/xml',
    }

    data = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
    <properties>
    <entry key="com.bigdata.rdf.sail.namespace">""" + namespace + """</entry>
    <entry key="com.bigdata.rdf.store.AbstractTripleStore.quads">false</entry>
    </properties>"""

    response = requests.post(blazegraphURL + "/blazegraph/namespace", headers=headers, data=data)
    return response.status_code == 201
