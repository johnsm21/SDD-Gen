import globalVars
import os
import requests
import wordConverter
from SPARQLWrapper import SPARQLWrapper, JSON

import pickle;

from rdflib.namespace import RDF
from rdflib import URIRef, Namespace, Graph, Literal

import sys
sys.path.append('lib/CAMR-Python3/')

# import amr_parsing


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


def generateOntoEmbedding(file, gloveMap, word2Id, weights):
    # Figure out what ontology this is
    g = Graph()
    fileFormat = None
    try:
        g.parse(file, format="rdf")
        fileFormat = "rdf"
    except:
        print("not rdf")
        try:
            g.parse(file, format="xml")
            fileFormat = "xml"
        except:
            print("not xml")
            try:
                g.parse(file, format="ttl")
                fileFormat = "ttl"
            except:
                print("not ttl")
                try:
                    g.parse(file, format="n3")
                    fileFormat = "n3"
                except:
                    print("not n3")
                    try:
                        g.parse(file, format="ntriples")
                        fileFormat = "ntriples"
                    except:
                        print("not ntriples")

    print("number of triples "+ str(len(g)))

    res = g.query(
    """
       prefix owl: <http://www.w3.org/2002/07/owl#>
       prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
       select ?onto ?ver ?verIRI ?oboNameSpace
       where{
          ?onto a owl:Ontology .
          optional{
             ?onto owl:versionInfo ?ver .
          }
          optional{
             ?onto owl:versionIRI ?verIRI .
          }
          optional{
             ?onto oboInOwl:default-namespace ?oboNameSpace .
          }
       }""")

    ontlist = []
    for row in res:

        # handle obo
        if row.oboNameSpace is None:
            ontology = str(row.onto)
        else: # ontology IRI is blank node in the new api :(
            ontology = 'http://purl.obolibrary.org/obo/' + str(row.oboNameSpace)

        version = row.ver
        versionIRI = row.verIRI

        oboNameSpace = row.oboNameSpace
        # print('Here ontology = ' + str(ontology))
        # print('Here versionIRI = ' + str(versionIRI))
        # print('Here version = ' + str(version))
        # print('Here oboNameSpace = ' + str(oboNameSpace))
        ontlist.append([ontology, versionIRI, version])

    ontology = None
    versionIRI = None
    version = None
    if len(ontlist) == 1:
        (ontology, versionIRI, version) = ontlist[0]
    else:
        if len(ontlist) > 1:
            for onto, verI, ver in ontlist:
                ontology = onto
                versionIRI = verI
                version = ver
                if 'ontology' in ontology:
                    break

    # Save metadata
    print('final ontology = ' + str(ontology))
    print('final versionIRI = ' + str(versionIRI))
    print('final version = ' + str(version))

    if ontology is None:
        print('Couldnt parse the file: ' + file);
        return False;

    if str(ontology) in globalVars.loadedOntos:
        print(str(ontology) + ' has already been loaded, skipping!');
        return False;

    ont = {};
    ont['versionIRI'] = versionIRI;
    ont['version'] = version;
    ont['amrDone'] = True;
    ont['notInProgress'] = False;

    globalVars.loadedOntos[str(ontology)] = ont;


    # get all class labels
    res = g.query(
    """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        select distinct ?variable ?label
        where{
           { ?variable a owl:Class }
           UNION
           { ?variable a rdfs:Class }

           ?variable rdfs:label ?label .
        }
    """);
    print('Found ' + str(len(res)) + ' classes!');

    # Generate Embeddings
    classList = {};
    for row in res:
        varIRI = str(row.variable);
        varLabel = str(row.label);
        # print('varIRI = ' + varIRI);
        # print('varLabel = ' + varLabel);
        dataY = wordConverter.tokenize(gloveMap, [varLabel], printMiss=False);
        dataY = wordConverter.token2idY(word2Id, dataY);
        dataY = wordConverter.idY2_L1NormSum(weights, dataY);
        dataY = dataY.pop().detach().numpy()[0, :];

        classList[varIRI] = dataY;
        # sys.exit(0);

    globalVars.loadedOntos[ontology]['classes'] = classList;
    globalVars.loadedOntos[ontology]['notInProgress'] = True;

    # Save the updated globalvars
    f = open(globalVars.loadedOntos_path, 'wb');
    pickle.dump(globalVars.loadedOntos, f);
    f.close();

    return True;

def ingest(file):
    # Figure out what ontology this is
    g = Graph()
    fileFormat = None
    try:
        g.parse(file, format="xml")
        fileFormat = "xml"
    except:
        print("not xml")
        try:
            g.parse(file, format="ttl")
            fileFormat = "ttl"
        except:
            print("not ttl")
            try:
                g.parse(file, format="n3")
                fileFormat = "n3"
            except:
                print("not n3")
                try:
                    g.parse(file, format="ntriples")
                    fileFormat = "ntriples"
                except:
                    print("not ntriples")

    print("number of triples "+ str(len(g)))

    res = g.query(
    """
       prefix owl: <http://www.w3.org/2002/07/owl#>
       prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
       select ?onto ?ver ?verIRI ?oboNameSpace
       where{
          ?onto a owl:Ontology .
          optional{
             ?onto owl:versionInfo ?ver .
          }
          optional{
             ?onto owl:versionIRI ?verIRI .
          }
          optional{
             ?onto oboInOwl:default-namespace ?oboNameSpace .
          }
       }""")

    ontlist = []
    for row in res:

        # handle obo
        if row.oboNameSpace is None:
            ontology = str(row.onto)
        else: # ontology IRI is blank node in the new api :(
            ontology = 'http://purl.obolibrary.org/obo/' + str(row.oboNameSpace)

        version = row.ver
        versionIRI = row.verIRI

        oboNameSpace = row.oboNameSpace
        print('Here ontology = ' + str(ontology))
        print('Here versionIRI = ' + str(versionIRI))
        print('Here version = ' + str(version))
        print('Here oboNameSpace = ' + str(oboNameSpace))
        ontlist.append([ontology, versionIRI, version])

    ontology = None
    versionIRI = None
    version = None
    if len(ontlist) == 1:
        (ontology, versionIRI, version) = ontlist[0]
    else:
        if len(ontlist) > 1:
            for onto, verI, ver in ontlist:
                ontology = onto
                versionIRI = verI
                version = ver
                if 'ontology' in ontology:
                    break


    print('final ontology = ' + str(ontology))
    print('final versionIRI = ' + str(versionIRI))
    print('final version = ' + str(version))

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
    # ts_base_url = "http://localhost:9999"
    sparql_ep = globalVars.ts_base_url + "/blazegraph/namespace/" + namespace + "/sparql"


    graph_namespace = base_graph_namespace + "/ontology"

    globalVars.ontoInProgress[base_graph_namespace] = True

    # Check if namespace exits
    print( '1 sparql_ep = ' + str(sparql_ep))
    print( '2 graph_namespace = ' + str(graph_namespace))
    if checkIfNamespaceExits(sparql_ep, graph_namespace):
        print("Note graph: " + graph_namespace + " already exists skipping ontology load")
    else:
        # Load Ontology into blazegraph
        print("Note graph: " + graph_namespace + " not found starting ontology load")

        print( '3 ts_base_url = ' + str(globalVars.ts_base_url))
        print( '4 graph_namespace = ' + str(graph_namespace))
        print( '5 file = ' + str(file))
        print( '6 namespace = ' + str(namespace))

        # if not loadQuad(globalVars.ts_base_url, graph_namespace, file, namespace):
        if not loadQuad(graph_namespace, file, fileFormat):
            print("checkIfNamespaceExits Error: Couldn't load: " + file)
            globalVars.ontoInProgress[base_graph_namespace] = False
            return False


    globalVars.ontoInProgress[base_graph_namespace] = False

    # Clean up temp directory
    textfile_dir = "temp/"
    files = os.listdir(textfile_dir)
    for file in files:
        if file.endswith(".fail") or file.endswith(".good") or file.endswith(".txt") or file.endswith(".prp") or file.endswith(".tok") or file.endswith(".parse") or file.endswith(".dep") or file.endswith(".parsed"):
            os.remove(os.path.join(textfile_dir, file))

    return True

## Removed because it is no longer used. Old code prior to fuseki shift
# def cleanNodeValue(value):
#     return value.rstrip().split("-")[0]
#
#
# def ontoToLabel(filepathIn, classIndex):
#     base = Namespace("https://github.com/tetherless-world/TWC-NHANES/AMR/")
#     doco = Namespace("http://purl.org/spar/doco/")
#     prov = Namespace("http://www.w3.org/ns/prov#")
#
#     g = Graph()
#     g.bind('prov', prov)
#     g.bind('doco', doco)
#     g.bind('amr', base)
#
#     entity = ""
#     stack = []
#     with open(filepathIn) as f:
#         for line in f:
#             # parse id
#             if "# ::id " in line:
#                 id = line.split("# ::id ")[1].rstrip()
#                 entity = "Sentence/" + id + "/"
#                 g.add( (base[entity], RDF.type, doco.Sentence) )
#                 g.add( (base[entity], prov.wasDerivedFrom, URIRef(classIndex[int(id)-1][0])))
#
#                 # reset stack
#                 uniqueID = 0
#                 stack = []
#                 stack.append(base[entity])
#
#             else: # not id
#                 # parse sentence
#                 if "# ::snt " in line:
#                     snt = line.split("# ::snt ")[1].rstrip()
#                     g.add( (stack[-1], prov.value, Literal(snt)) )
#
#                 else: # not sentence
#                     # parse root node
#                     if line[0] == "(":
#                         node = line[1:].split(" / ")[0]
#                         node_value = cleanNodeValue(line[1:].split(" / ")[1])
#
#                         nodeIRI = base[entity + "AMRNode/" + node + "/"]
#                         g.add( (nodeIRI, RDF.type, base.AMRNode) )
#                         g.add( (stack[-1], base.hasRootNode, nodeIRI) )
#                         g.add( (nodeIRI, prov.value, Literal(node_value)) )
#
#                         stack.append(nodeIRI)
#                         # print(node + ": " + node_value)
#
#                     else: # not root node
#                         # parse node
#                         if line[0] == "\t":
#                             noDepth = line.lstrip("\t")
#                             currentDepth = len(line) - len(noDepth)
#
#                             parse = noDepth.split(" (")
#                             if len(parse) == 1: # 2 value line
#                                 edge = parse[0].split(" ")[0][1:]
#                                 node = edge + "Node" + str(uniqueID)
#                                 value = parse[0].split(" ")[1].rstrip("\n)")
#                                 uniqueID = uniqueID + 1
#                             else:
#                                 if len(parse) == 2: # 3 value line
#                                     edge = parse[0][1:]
#                                     node = parse[1].split(" / ")[0]
#                                     value = parse[1].split(" / ")[1].rstrip("\n)")
#                                 else: # Unknown Case
#                                     print("Unkown Case = " + line)
#
#                             # check if this node is a child, if its not get rid of unneeded state
#                             while (currentDepth <= (len(stack)-2)):
#                                 stack.pop()
#
#                             nodeIRI = base[entity + "AMRNode/" + node + "/"]
#                             g.add( (nodeIRI, RDF.type, base.AMRNode) )
#                             g.add( (stack[-1], base[edge], nodeIRI) )
#                             g.add( (nodeIRI, prov.value, Literal(value)) )
#                             stack.append(nodeIRI)
#
#                         else: # not a node
#                             if not (line.rstrip() == ""): # your not empty lines so what are you?
#                                 print("vvvvvvBADvvvvvvv")
#                                 print(line)
#                                 print("^^^^^^BAD^^^^^^^")
#     g.serialize(destination=filepathIn + ".rdf", format="pretty-xml")

## Removed because it is no longer used. Old code prior to fuseki shift
# def generateAMRTextFile(blazegraphURL, graph_namespace, file):
#     sparql = SPARQLWrapper(blazegraphURL)
#     sparql.setQuery("""
#         prefix dcterm: <http://purl.org/dc/terms/>
#         prefix skos: <http://www.w3.org/2004/02/skos/core#>
#         select distinct ?class ?className ?description ?definition
#         where{
#           graph <%s> {
#             ?class  a           owl:Class ;
#                     rdfs:label  ?className .
#             optional{
#               ?class dcterm:description ?description .
#             }
#             optional{
#               ?class skos:definition ?definition .
#             }
#           }
#         } order by asc(?className)
#         """ % graph_namespace)
#
#     sparql.setReturnFormat(JSON)
#     results = sparql.query().convert()
#
#     classIndex = []
#     classIRIs = []
#
#     with open(file, 'w') as the_file:
#         for result in results["results"]["bindings"]:
#             classIRI = str(result["class"]["value"])
#             className = str(result["className"]["value"])
#             if classIRI in classIRIs:
#                 print('Duplicate description for ' + classIRI)
#             else:
#                 if ("description" in result) or ("definition" in result):
#                     if "description" in result:
#                         description = str(result["description"]["value"])
#                     else:
#                         description = str(result["definition"]["value"])
#
#                     classIndex.append((classIRI, className))
#                     classIRIs.append(classIRI)
#
#                     # If there are multiple sentences only look at the first one
#                     sentence = description.split(".")[0].replace('\n', ' ')
#                     the_file.write(sentence + "." + '\n')
#     return classIndex


def checkIfNamespaceExits(blazegraphURL, namespace):
    query = """
        ask{
            graph <%s> {
                ?s ?p ?o .
            }
        }
    """ % namespace
    qres = globalVars.store.query(query)
    return qres.askAnswer

def loadQuad(quadnamespace, file, fileFormat):
    filepath = os.path.abspath(file)

    graph = Graph(globalVars.store, identifier = URIRef(quadnamespace))
    graph.parse(filepath, format = fileFormat)

    print('graph size = ' + str(len(graph)))
    return len(graph) > 0
