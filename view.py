

def generateAMRTextFile(blazegraphURL, file):
    base_url = "http://localhost:9999"
    blazegraphURL = base_url + "/blazegraph/namespace/" + namespace + "/sparql"
    sparql = SPARQLWrapper(blazegraphURL)

    sparql.setQuery("""
        prefix vann: <http://purl.org/vocab/vann/>
        select distinct ?g ?onto ?ver ?perfer
        where{
            graph ?g {
                ?onto a owl:Ontology .
                ?onto owl:versionInfo ?ver .

                optional {
                    ?onto vann:preferredNamespaceUri ?perfer
                }
            }
        } order by asc(?g)
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        classIRI = result["class"]["value"]
        className = result["className"]["value"]
        description = result["description"]["value"]
        classIndex.append((classIRI, className))

        # If there are multiple sentences only look at the first one
        sentence = description.split(".")[0].replace('\n', ' ')
        the_file.write(sentence + "." + '\n')
    return classIndex

def getPrefixCC(url):
    response = requests.get('https://prefix.cc/', params={'q': url})
    json_response = response.json()

    if(response.status_code == 201):
        return "none"
    else:
        print(json_response)
        return "found"
