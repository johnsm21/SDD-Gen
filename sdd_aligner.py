from SPARQLWrapper import SPARQLWrapper, JSON
import jellyfish
import helper_function

def labelMatch(results, n, dataDict, graphs):
    # get all classes and IRIs
    classNames = getClassNames(graphs)

    for dict in dataDict:
        ddlabel = dict['column'].lower()
        distArray = []
        for iri, labelArray in classNames.items():
            for label in labelArray:
                d = jellyfish.levenshtein_distance(ddlabel, label.lower())
                distArray.append((iri, d))

        distArray = helper_function.distToConf(distArray)
        distArray = sorted(distArray, key=lambda x: x[1], reverse=True)
        distArray = helper_function.calcArrayStars(distArray)
        print(distArray[0:n])

        results.addDMColumn(dict['column'], attribute = distArray[0:n])

    return results

def getClassNames(graphs):
    # setup sparql endpoint
    base_url = "http://localhost:9999"
    namespace = "mapper"
    sparql = SPARQLWrapper(base_url + "/blazegraph/namespace/" + namespace + "/sparql")
    sparql.setReturnFormat(JSON)

    # Create dictionary of classnames
    classNames = {}
    for g in graphs:
        sparql.setQuery("""
            select distinct ?class ?name
            where{
            	graph <%s> {
            		?class a owl:Class .
                  	?class rdfs:label ?name .
                }
            }""" % g)
        for result in sparql.query().convert()["results"]["bindings"]:
            classIri = result["class"]["value"]
            label = result["name"]["value"]
            if classIri not in classNames:
                classNames[classIri] = [label]
            else:
                classNames[classIri].append(label)

    return classNames
