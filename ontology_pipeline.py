import globals
import os
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from rdflib.namespace import RDF
from rdflib import URIRef, Namespace, Graph, Literal

import sys
sys.path.append('lib/CAMR-Python3/')

import amr_parsing


rdfFileType = {
'rdf' : 'rdf/xml',
'rdfs' : 'rdf/xml',
'owl' : 'rdf/xml',
'xml' : 'rdf/xml',
'nt' : 'n-triples',
'ttl' : 'turtle',
'n3' : 'n3',
'nq' : 'n-quads'
}

def ingest(file):
    # Figure out what ontology this is
    ontology = None
    version = None

    g = Graph()
    try:
        g.parse(file, format="xml")
    except:
        print("not xml")
        try:
            g.parse(file, format="ttl")
        except:
            print("not ttl")
            try:
                g.parse(file, format="n3")
            except:
                print("not n3")
                try:
                    g.parse(file, format="ntriples")
                except:
                    print("not ntriples")

    print("number of triples "+ str(len(g)))

    res = g.query(
    """
       select ?onto ?ver ?verIRI
       where{
          ?onto a owl:Ontology .
          optional{
             ?onto owl:versionInfo ?ver .
          }
          optional{
             ?onto owl:versionIRI ?verIRI .
          }
       }""")

    for row in res:

        ontology = str(row.onto)
        version = row.ver
        versionIRI = row.verIRI
        print('Here ontology = ' + str(ontology))
        print('Here versionIRI = ' + str(versionIRI))
        print('Here version = ' + str(version))
    g = None # Release resources

    if versionIRI is None:
        if version is None:
            version = '1.0'
        else:
            version = str(version)
        base_graph_namespace = ontology + "/" + version
    else:
        versionIRI = str(versionIRI)
        base_graph_namespace = versionIRI

    print('base_graph_namespace = ' + str(base_graph_namespace))

    # Create a namespace for it
    namespace = "mapper"
    base_url = "http://localhost:9999"
    sparql_ep = base_url + "/blazegraph/namespace/" + namespace + "/sparql"


    graph_namespace = base_graph_namespace + "/ontology"

    globals.ontoInProgress[base_graph_namespace] = True

    # Check if namespace exits
    print( '1 sparql_ep = ' + str(sparql_ep))
    print( '2 graph_namespace = ' + str(graph_namespace))
    if checkIfNamespaceExits(sparql_ep, graph_namespace):
        print("Note graph: " + graph_namespace + " already exists skipping ontology load")
    else:
        # Load Ontology into blazegraph
        print("Note graph: " + graph_namespace + " not found starting ontology load")

        print( '3 base_url = ' + str(base_url))
        print( '4 graph_namespace = ' + str(graph_namespace))
        print( '5 file = ' + str(file))
        print( '6 namespace = ' + str(namespace))
        if not loadQuad(base_url, graph_namespace, file, namespace):
            print("checkIfNamespaceExits Error: Couldn't load: " + file)
            globals.ontoInProgress[base_graph_namespace] = False
            return False


    # Check if amr graph exists
    amr_namespace = base_graph_namespace + "/amr"
    print( '7 sparql_ep = ' + str(sparql_ep))
    print( '8 amr_namespace = ' + str(amr_namespace))
    if checkIfNamespaceExits(sparql_ep, amr_namespace):
        print("Note graph: " + amr_namespace + " already exists skipping AMR load")
    else:
        print("Note graph: " + amr_namespace + " not found begin loading")
        descriptFile = file + ".txt"
        print( '9 sparql_ep = ' + str(sparql_ep))
        print( '10 descriptFile = ' + str(descriptFile))
        classIndex = generateAMRTextFile(sparql_ep, graph_namespace, descriptFile)
        print("generated description file!")

        # Run AMR
        # model = 'lib/amr-semeval-all.train.basic-abt-brown-verb.m'
        model = 'lib/python3_model_5.basic-abt-brown-verb.m'

        # run the preprocessor
        sys.argv = ['amr_parsing.py','-m', 'preprocess', descriptFile]
        amr_parsing.main()

        # run the parser
        sys.argv = ['amr_parsing.py','-m', 'parse', '--model', model, descriptFile]
        amr_parsing.main()
        print("Finished Running AMR")

        # run the AMR to RDF converter
        print( '11 descriptFile + ".all.basic-abt-brown-verb.parsed" = ' + str(descriptFile + ".all.basic-abt-brown-verb.parsed"))
        # print( '12 classIndex = ' + str(classIndex))
        ontoToLabel(descriptFile + ".all.basic-abt-brown-verb.parsed", classIndex)
        print( '13 base_url = ' + str(base_url))
        print( '14 amr_namespace = ' + str(amr_namespace))
        print( '15 descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf" = ' + str(descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf"))
        print( '16 namespace = ' + str(namespace))
        if not loadQuad(base_url, amr_namespace, descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf", namespace):
            print("Error: Couldn't load: " + amr_namespace, descriptFile + ".all.basic-abt-brown-verb.parsed" + ".rdf")
            globals.ontoInProgress[base_graph_namespace] = False
            return False

    globals.ontoInProgress[base_graph_namespace] = False

    # Clean up temp directory
    textfile_dir = "temp/"
    files = os.listdir(textfile_dir)
    for file in files:
        if file.endswith(".fail") or file.endswith(".good") or file.endswith(".txt") or file.endswith(".prp") or file.endswith(".tok") or file.endswith(".parse") or file.endswith(".dep") or file.endswith(".parsed"):
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

def generateAMRTextFile(blazegraphURL, graph_namespace, file):
    sparql = SPARQLWrapper(blazegraphURL)
    sparql.setQuery("""
        prefix dcterm: <http://purl.org/dc/terms/>
        prefix skos: <http://www.w3.org/2004/02/skos/core#>
        select distinct ?class ?className ?description ?definition
        where{
          graph <%s> {
            ?class  a           owl:Class ;
                    rdfs:label  ?className .
            optional{
              ?class dcterm:description ?description .
            }
            optional{
              ?class skos:definition ?definition .
            }
          }
        } order by asc(?className)
        """ % graph_namespace)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    classIndex = []
    classIRIs = []

    with open(file, 'w') as the_file:
        for result in results["results"]["bindings"]:
            classIRI = str(result["class"]["value"])
            className = str(result["className"]["value"])
            if classIRI in classIRIs:
                print('Duplicate description for ' + classIRI)
            else:
                if ("description" in result) or ("definition" in result):
                    if "description" in result:
                        description = str(result["description"]["value"])
                    else:
                        description = str(result["definition"]["value"])

                    classIndex.append((classIRI, className))
                    classIRIs.append(classIRI)

                    # If there are multiple sentences only look at the first one
                    sentence = description.split(".")[0].replace('\n', ' ')
                    the_file.write(sentence + "." + '\n')
    return classIndex


def checkIfNamespaceExits(blazegraphURL, namespace):
    sparql = SPARQLWrapper(blazegraphURL)
    sparql.setQuery("""
        ask{
          graph <%s> {
            ?s ?p ?o .
          }
         }
        """ % namespace)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["boolean"]

def loadQuad(blazegraphURL, quadnamespace, file, namespace):
    filepath = os.path.abspath(file)
    propertiesPath = "RWStore.properties"
    format = rdfFileType[file.split('.')[-1]]

    # RDF Format (Default is rdf/xml)
    # Default Graph URI (Optional - Required for quads mode namespace)
    # Suppress all stdout messages (Optional)
    # Show additional messages detailing the load performance. (Optional)
    # Compute the RDF(S)+ closure. (Optional)
    # Files will be renamed to either .good or .fail as they are processed.
    # The namespace of the KB instance. Defaults to kb.
    # The configuration file for the database instance. It must be readable by the web application.
    # Zero or more files or directories containing the data to be loaded. This should be a comma delimited list. The files must be readable by the web application.
    data = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
        	  <properties>
        	      <entry key="format">{format}</entry>
        	      <entry key="defaultGraph">{quadnamespace}</entry>
        	      <entry key="quiet">false</entry>
        	      <entry key="verbose">0</entry>
        	      <entry key="closure">false</entry>
        	      <entry key="durableQueues">true</entry>
        	      <entry key="namespace">{namespace}</entry>
        	      <entry key="propertyFile">{propertiesPath}</entry>
        	      <entry key="fileOrDirs">{filepath}</entry>
              </properties>"""

    headers = {'Content-Type': 'application/xml',}
    response = requests.post(blazegraphURL + "/blazegraph/dataloader", headers=headers, data=data)
    return (response.status_code == 201) or (response.status_code == 200)
