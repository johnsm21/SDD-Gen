from SPARQLWrapper import SPARQLWrapper, JSON
import jellyfish
import helper_function
import numpy as np
from scipy import spatial
import torch
import wordConverter
import globalVars

def transformerMatchWithOntoPriority(results, n, dataDict, graphs, gloveMap, word2Id, model):
    pMod = 0.8
    slope = (pMod - 1)/(len(graphs)-1) # (1-pMod)/len(graphs)

    # generate description embedding
    dataX = []
    dataCol = []
    for dict in dataDict:
        dataCol.append(dict['column'])
        dataX.append(dict['description'])

    dataX = np.array(dataX)
    dataX = wordConverter.tokenize(gloveMap, dataX)
    dataX = wordConverter.token2id(word2Id, dataX)
    (dataX, input_msk) = wordConverter.pad_id(globalVars.max_sent_length, dataX)
    input_msk = torch.from_numpy(np.asarray(input_msk))
    dataX = torch.from_numpy(np.asarray(dataX))
    predict = model.forward(dataX, input_msk)
    predict = predict.detach().numpy()

    for j in range(len(dataCol)):
        ddC = dataCol[j]
        ddVect = predict[j]

        distArray = []
        for i in range(len(graphs)):
            weight = (slope*i) + 1
            classNames = getClassNames([graphs[i]])
            for iri, labelArray in classNames.items():
                for label in labelArray:
                    if label.lower() in gloveMap:
                        labelVect = gloveMap[label.lower()]

                        # d = spatial.distance.cosine(labelVect, ddVect)
                        # distArray.append((label, d))


                        d = ((1.0 - spatial.distance.cosine(labelVect, ddVect)) + 1.0)/2.0
                        d = d * weight

                        if d > 0.85:
                             distArray.append((iri, d))


        distArray = sorted(distArray, key=lambda x: x[1], reverse=True)
        distArray = helper_function.fakeStars(distArray)

        size = min([len(distArray), n])

        results.addDMColumn(ddC, attribute = distArray[0:size])

    return results


def semanticLabelMatchWithOntoPriority(results, n, dataDict, graphs, gloveMap):
    pMod = 0.8

    slope = (pMod - 1)/(len(graphs)-1) # (1-pMod)/len(graphs)
    # weights = [ (slope*x) + 1 for x in range(len(graphs))]

    for dict in dataDict:
        ddlabel = dict['column'].lower()

        distArray = []
        if ddlabel in gloveMap:
            ddVect = gloveMap[ddlabel]
            for i in range(len(graphs)):
                weight = (slope*i) + 1
                classNames = getClassNames([graphs[i]])
                for iri, labelArray in classNames.items():
                    for label in labelArray:
                        if label.lower() in gloveMap:
                            labelVect = gloveMap[label.lower()]
                            d = ((1.0 - spatial.distance.cosine(ddVect, labelVect)) + 1.0)/2.0
                            d = d * weight

                            if d > 0.7:
                            # || a - b||
                            # d = np.linalg.norm(ddVect - labelVect)
                                distArray.append((iri, d))

            # distArray = helper_function.distToConf(distArray)
            distArray = sorted(distArray, key=lambda x: x[1], reverse=True)
            distArray = helper_function.fakeStars(distArray)


        size = min([len(distArray), n])

        # print('ddlabel = ' + str(ddlabel))
        # print('distArray = ' + str(distArray[0:size]))

        results.addDMColumn(dict['column'], attribute = distArray[0:size])

    return results



def semanticLabelMatch(results, n, dataDict, graphs, gloveMap):
    # get all classes and IRIs
    classNames = getClassNames(graphs)

    # classNames = getAllClassNames()
    # print('classNames = ' + str(classNames))
    # print('dataDict')

    for dict in dataDict:
        ddlabel = dict['column'].lower()

        distArray = []
        if ddlabel in gloveMap:
            ddVect = gloveMap[ddlabel]
            for iri, labelArray in classNames.items():
                for label in labelArray:
                    if label.lower() in gloveMap:
                        labelVect = gloveMap[label.lower()]
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
    # ts_base_url = "http://localhost:9999"
    namespace = "mapper"
    sparql = SPARQLWrapper(globalVars.ts_base_url + "/blazegraph/namespace/" + namespace + "/sparql")
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
    # ts_base_url = "http://localhost:9999"
    namespace = "mapper"
    sparql = SPARQLWrapper(globalVars.ts_base_url + "/blazegraph/namespace/" + namespace + "/sparql")
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
