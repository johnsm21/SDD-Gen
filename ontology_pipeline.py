import os
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from rdflib.namespace import RDF
from rdflib import URIRef, Namespace, Graph, Literal

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
    namespace = "mapper"
    base_url = "http://localhost:9999"
    sparql_ep = base_url + "/blazegraph/namespace/" + namespace + "/sparql"

    base_graph_namespace = ontology + "/" + version
    graph_namespace = base_graph_namespace + "/ontology"

    # Check if namespace exits
    if checkIfNamespaceExits(sparql_ep, graph_namespace):
        print("Note graph: " + graph_namespace + " already exists skipping ontology load")
    else:
        print("Note graph: " + graph_namespace + " not found starting ontology load")
        if not loadQuad(base_url, graph_namespace, file, namespace):
            print("Error: Couldn't load: " + file)
            return False


    # Check if amr graph exists
    amr_namespace = base_graph_namespace + "/amr"
    if checkIfNamespaceExits(sparql_ep, amr_namespace):
        print("Note graph: " + amr_namespace + " already exists skipping AMR load")
    else:
        print("Note graph: " + amr_namespace + " not found begin loading")
        descriptFile = file + ".txt"
        classIndex = generateAMRTextFile(sparql_ep, descriptFile)
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

        # run the AMR to RDF converter
        ontoToLabel(descriptFile + ".all.basic-abt-brown-verb.parsed", classIndex)
        if not loadQuad(base_url, amr_namespace, descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf", namespace):
            print("Error: Couldn't load: " + amr_namespace, descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf")
            return False

    # Clean up temp directory
    textfile_dir = "temp/"
    files = os.listdir(textfile_dir)
    for file in files:
        if file.endswith(".good") or file.endswith(".txt") or file.endswith(".prp") or file.endswith(".tok") or file.endswith(".parse") or file.endswith(".dep") or file.endswith(".parsed"):
            os.remove(os.path.join(textfile_dir, file))

    return True

def cleanNodeValue(value):
    return value.rstrip().split("-")[0]


def ontoToLabel(filepathIn, classIndex):
    base = Namespace("https://github.com/tetherless-world/TWC-NHANES/AMR/")
    doco = Namespace("http://purl.org/spar/doco/")
    prov = Namespace("http://www.w3.org/ns/prov#")

    g = Graph()
    g.bind('prov', prov)
    g.bind('doco', doco)
    g.bind('amr', base)

    entity = ""
    stack = []
    with open(filepathIn) as f:
        for line in f:
            # parse id
            if "# ::id " in line:
                id = line.split("# ::id ")[1].rstrip()
                entity = "Sentence/" + id + "/"
                g.add( (base[entity], RDF.type, doco.Sentence) )
                g.add( (base[entity], prov.wasDerivedFrom, URIRef(classIndex[int(id)-1][0])))

                # reset stack
                uniqueID = 0
                stack = []
                stack.append(base[entity])

            else: # not id
                # parse sentence
                if "# ::snt " in line:
                    snt = line.split("# ::snt ")[1].rstrip()
                    g.add( (stack[-1], prov.value, Literal(snt)) )

                else: # not sentence
                    # parse root node
                    if line[0] == "(":
                        node = line[1:].split(" / ")[0]
                        node_value = cleanNodeValue(line[1:].split(" / ")[1])

                        nodeIRI = base[entity + "AMRNode/" + node + "/"]
                        g.add( (nodeIRI, RDF.type, base.AMRNode) )
                        g.add( (stack[-1], base.hasRootNode, nodeIRI) )
                        g.add( (nodeIRI, prov.value, Literal(node_value)) )

                        stack.append(nodeIRI)
                        # print(node + ": " + node_value)

                    else: # not root node
                        # parse node
                        if line[0] == "\t":
                            noDepth = line.lstrip("\t")
                            currentDepth = len(line) - len(noDepth)

                            parse = noDepth.split(" (")
                            if len(parse) == 1: # 2 value line
                                edge = parse[0].split(" ")[0][1:]
                                node = edge + "Node" + str(uniqueID)
                                value = parse[0].split(" ")[1].rstrip("\n)")
                                uniqueID = uniqueID + 1
                            else:
                                if len(parse) == 2: # 3 value line
                                    edge = parse[0][1:]
                                    node = parse[1].split(" / ")[0]
                                    value = parse[1].split(" / ")[1].rstrip("\n)")
                                else: # Unknown Case
                                    print("Unkown Case = " + line)

                            # check if this node is a child, if its not get rid of unneeded state
                            while (currentDepth <= (len(stack)-2)):
                                stack.pop()

                            nodeIRI = base[entity + "AMRNode/" + node + "/"]
                            g.add( (nodeIRI, RDF.type, base.AMRNode) )
                            g.add( (stack[-1], base[edge], nodeIRI) )
                            g.add( (nodeIRI, prov.value, Literal(value)) )
                            stack.append(nodeIRI)

                        else: # not a node
                            if not (line.rstrip() == ""): # your not empty lines so what are you?
                                print("vvvvvvBADvvvvvvv")
                                print(line)
                                print("^^^^^^BAD^^^^^^^")
    g.serialize(destination=filepathIn + ".rdf", format="pretty-xml")

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
    return classIndex


def checkIfNamespaceExits(blazegraphURL, namespace):
    sparql = SPARQLWrapper(blazegraphURL)
    sparql.setQuery("""
        ask{
          graph <""" + namespace + """> {
            ?s ?p ?o .
          }
         }
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["boolean"]

def loadQuad(blazegraphURL, quadnamespace, file, namespace):
    filepath = os.path.abspath(file)
    print("Filepath = " + filepath)
    propertiesPath = "RWStore.properties"

    headers = {
        'Content-Type': 'application/xml',
    }

    data = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
        	  <properties>
        	      <!-- RDF Format (Default is rdf/xml) -->
        	      <entry key="format">rdf/xml</entry>

        	      <!-- Default Graph URI (Optional - Required for quads mode namespace) -->
                  <entry key="defaultGraph">""" + quadnamespace + """</entry>

        	      <!-- Suppress all stdout messages (Optional) -->
        	      <entry key="quiet">false</entry>

        	      <!-- Show additional messages detailing the load performance. (Optional) -->
        	      <entry key="verbose">0</entry>

        	     <!-- Compute the RDF(S)+ closure. (Optional) -->
                     <entry key="closure">false</entry>

        	     <!-- Files will be renamed to either .good or .fail as they are processed.
                           The files will remain in the same directory. -->
        	     <entry key="durableQueues">true</entry>

        	     <!-- The namespace of the KB instance. Defaults to kb. -->
        	     <entry key="namespace">""" + namespace + """</entry>

        	     <!-- The configuration file for the database instance. It must be readable by the web application. -->
                     <entry key="propertyFile">""" + propertiesPath + """</entry>

        	     <!-- Zero or more files or directories containing the data to be loaded.
                           This should be a comma delimited list. The files must be readable by the web application. -->

                   <entry key="fileOrDirs">""" + filepath + """</entry>
              </properties>"""

    response = requests.post(blazegraphURL + "/blazegraph/dataloader", headers=headers, data=data)
    return response.status_code == 201
