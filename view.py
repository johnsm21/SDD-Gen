import requests
from SPARQLWrapper import SPARQLWrapper, JSON

prefixMap = {}

def getInstalledOntologies():
    base_url = "http://localhost:9999"
    namespace = "mapper"
    blazegraphURL = base_url + "/blazegraph/namespace/" + namespace + "/sparql"
    sparql = SPARQLWrapper(blazegraphURL)

    sparql.setQuery("""
        prefix vann: <http://purl.org/vocab/vann/>
        select distinct ?g ?onto ?ver ?perfer
        where{
            graph ?g {
                ?onto a owl:Ontology .

                optional {
                    ?onto owl:versionInfo ?ver .
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
        version = '1.0'

        baseUri = result["onto"]["value"]

        if "ver" in result:
            version = result["ver"]["value"]

        if "perfer" in result:
            baseUri = result["perfer"]["value"]


        ontologies.append((getPrefixCC(baseUri), baseUri, version));
    return ontologies

def getPrefixCC(url):
    if not prefixMap.has_key(url):
        print("Had to look up")
        response = requests.get('https://prefix.cc/', params={'q': url})

        if(response.status_code == 201):
            prefixMap[url] = "NONE"
        else:
            prefixMap[url] = response.content.split(" | prefix.cc</title>")[0].split("<title property=\"dc:title\">")[1]

    return prefixMap[url]
