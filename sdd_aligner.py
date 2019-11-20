from SPARQLWrapper import SPARQLWrapper, JSON
import jellyfish
import helper_function
import numpy as np


def semanticLabelMatch(results, n, dataDict, graphs, gloveVect):
    # get all classes and IRIs
    classNames = getClassNames(graphs)

    # classNames = getAllClassNames()
    # print('classNames = ' + str(classNames))
    # print('dataDict')

    for dict in dataDict:
        ddlabel = dict['column'].lower()

        distArray = []
        if ddlabel in gloveVect:
            ddVect = gloveVect[ddlabel]
            for iri, labelArray in classNames.items():
                for label in labelArray:
                    if label.lower() in gloveVect:
                        labelVect = gloveVect[label.lower()]
                        # || a - b||
                        d = np.linalg.norm(ddVect - labelVect)
                        distArray.append((iri, d))

            distArray = helper_function.distToConf(distArray)
            distArray = sorted(distArray, key=lambda x: x[1], reverse=True)
            distArray = helper_function.calcArrayStars(distArray)

        size = min([len(distArray), n])

        print('ddlabel = ' + str(ddlabel))
        print('distArray = ' + str(distArray[0:size]))

        results.addDMColumn(dict['column'], attribute = distArray[0:size])

    return results

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

        # Add N uniques IRIs
        distResult = []
        iris = []
        for dist in distArray:
            if dist[0] not in iris:
                distResult.append(dist)
                iris.append(dist[0])
                if len(distResult) == n:
                    break;

        # print(distResult)

        results.addDMColumn(dict['column'], attribute = distResult)

    return results


def descriptionMatch(results, n, dataDict, graphs):
    print(results)
    print(n)
    print(dataDict)
    print(graphs)
    return results

def getAllClassNames():
    # setup sparql endpoint
    base_url = "http://localhost:9999"
    namespace = "mapper"
    sparql = SPARQLWrapper(base_url + "/blazegraph/namespace/" + namespace + "/sparql")
    sparql.setReturnFormat(JSON)

    # Create dictionary of classnames
    classNames = {}

    sparql.setQuery("""
        select distinct ?class ?name
        where{
    		{ ?class a owl:Class }
            union
            { ?class a rdfs:Class }
          	?class rdfs:label ?name .
        }""")

    for result in sparql.query().convert()["results"]["bindings"]:
        classIri = result["class"]["value"]
        label = result["name"]["value"].lower()
        if classIri not in classNames:
            classNames[classIri] = [label]
        else:
            if label not in classNames[classIri]:
                classNames[classIri].append(label)

    return classNames


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
            		{ ?class a owl:Class }
                    union
                    { ?class a rdfs:Class }
                  	?class rdfs:label ?name .
                }
            }""" % g)
        for result in sparql.query().convert()["results"]["bindings"]:
            classIri = result["class"]["value"]
            label = result["name"]["value"].lower()
            if classIri not in classNames:
                classNames[classIri] = [label]
            else:
                if label not in classNames[classIri]:
                    classNames[classIri].append(label)

    return classNames
