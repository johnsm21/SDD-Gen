import numpy as np
from scipy import stats
from operator import itemgetter
from SPARQLWrapper import SPARQLWrapper, JSON
import xlrd


# listODict [{"value": "hasco:originalID", "confidence": 0.9}, {"value": "sio:Number", "confidence": 0.7}, {"value": "chear:Weight", "confidence": 0.25}]
def calcStars(listODict):
    # create confidence array
    confList = []
    for i in listODict:
        confList.append(i["confidence"])
    confArray = np.array(confList)

    # Calculate z-score
    zArray = stats.zscore(confArray)

    # Calculate stars
    confList = []
    for i in zArray.tolist():
        x = int(round(i))
        if x < 0 :
            x = 0
        confList.append(x)

    # Generate new dictionaries
    x = 0
    for i in listODict:
        i["star"] = confList[x]
        x = x + 1

    return listODict

# listOfTuple [('http://semanticscience.org/resource/SIO_000585', 0.9696969696969697),
def calcArrayStars(listOfTuple):
    # create confidence array
    confList = []
    for i in listOfTuple:
        confList.append(i[1])
    confArray = np.array(confList)

    # Calculate z-score
    zArray = stats.zscore(confArray)

    # Calculate stars
    confList = []
    for i in zArray.tolist():
        x = int(round(i))
        if x < 0 :
            x = 0
        confList.append(x)

    # Generate new dictionaries
    x = 0
    listOfTriple = []
    for i in listOfTuple:
        listOfTriple.append((i[0], i[1], confList[x]))
        x = x + 1

    return listOfTriple


def fakeStars(listOfTuple):

    # remove duplicates and add fake stars
    listOfTriple = []
    iris = []
    for i in listOfTuple:
        if i[0] not in iris:
            iris.append(i[0])
            listOfTriple.append((i[0], i[1], round(i[1], 2)))

    return listOfTriple

def distToConf(distArray):
    maxDist = max(distArray,key=itemgetter(1))[1]
    distArray = list(map(lambda i: (i[0], ((-1*i[1]) + maxDist)/maxDist), distArray))
    return distArray

def getSioLabel(sioIri):
    base_url = "http://localhost:9999"
    namespace = "mapper"
    sparql = SPARQLWrapper(base_url + "/blazegraph/namespace/" + namespace + "/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        select ?label ?type
        where{
          <%s> rdfs:label ?label ;
             a  ?type .
        }
        """ % sioIri)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        label = result["label"]["value"]
        type = result["type"]["value"]

        labelParts = label.split()
        print('label = ' + label)
        print('type = ' + type)
        if type == 'http://www.w3.org/2002/07/owl#Class':
            labelParts[0] = labelParts[0][0].capitalize()+labelParts[0][1:]
        iri = 'http://semanticscience.org/resource/' + labelParts[0]

        if len(labelParts) > 1:
            for i in labelParts[1:]:
                if i.startswith('(') and i.endswith(')'):
                    iri = iri + i[1:-1]
                else:
                    iri = iri + i[0].capitalize()+i[1:]

        return iri

def sdd_loader(sddPath: str) -> dict:
    # Grab this data from ouyr file
    Column_data = []
    Attribute_data = []
    attributeOf_data = []
    Unit_data = []
    Time_data = []
    Entity_data = []
    Role_data = []
    Relation_data = []
    inRelationTo_data = []
    wasDerivedFrom_data = []
    wasGeneratedBy_data = []

    # file ttype specfic loading
    if(".csv" in sddPath):
        df = pd.read_csv(sddPath).replace(np.nan, '', regex=True)
        for index, row in df.iterrows():
            Column_data.append(row["Column"])
            Attribute_data.append(row["Attribute"])
            attributeOf_data.append(row["attributeOf"])
            Unit_data.append(row["Unit"])
            Time_data.append(row["Time"])
            Entity_data.append(row["Entity"])
            Role_data.append(row["Role"])
            Relation_data.append(row["Relation"])
            inRelationTo_data.append(row["inRelationTo"])
            wasDerivedFrom_data.append(row["wasDerivedFrom"])
            wasGeneratedBy_data.append(row["wasGeneratedBy"])

    elif(".xlsx" in sddPath):
        wb = xlrd.open_workbook(sddPath)
        sheet = wb.sheet_by_name("Dictionary Mapping")

        for i in range(sheet.ncols):
            if sheet.cell_value(0, i).strip() == "Column" :
                ColumnIndex = i

            if sheet.cell_value(0, i).strip() == "Attribute" :
                AttributeIndex = i

            if sheet.cell_value(0, i).strip() == "attributeOf" :
                attributeOfIndex = i

            if sheet.cell_value(0, i).strip() == "Unit" :
                UnitIndex = i

            if sheet.cell_value(0, i).strip() == "Time" :
                TimeIndex = i

            if sheet.cell_value(0, i).strip() == "Entity" :
                EntityIndex = i

            if sheet.cell_value(0, i).strip() == "Role" :
                RoleIndex = i

            if sheet.cell_value(0, i).strip() == "Relation" :
                RelationIndex = i

            if sheet.cell_value(0, i).strip() == "inRelationTo" :
                inRelationToIndex = i

            if sheet.cell_value(0, i).strip() == "wasDerivedFrom" :
                wasDerivedFromIndex = i

            if sheet.cell_value(0, i).strip() == "wasGeneratedBy" :
                wasGeneratedByIndex = i

        for i in range(sheet.nrows):
            if i > 0:
                Column_data.append(sheet.cell_value(i, ColumnIndex))
                Attribute_data.append(sheet.cell_value(i, AttributeIndex))
                attributeOf_data.append(sheet.cell_value(i, attributeOfIndex))
                Unit_data.append(sheet.cell_value(i, UnitIndex))
                Time_data.append(sheet.cell_value(i, TimeIndex))
                Entity_data.append(sheet.cell_value(i, EntityIndex))
                Role_data.append(sheet.cell_value(i, RoleIndex))
                Relation_data.append(sheet.cell_value(i, RelationIndex))
                inRelationTo_data.append(sheet.cell_value(i, inRelationToIndex))
                wasDerivedFrom_data.append(sheet.cell_value(i, wasDerivedFromIndex))
                wasGeneratedBy_data.append(sheet.cell_value(i, wasGeneratedByIndex))

    else:
        print("Filetype not supported")
        return -1

    schema_data = {}
    entity_data = {}
    for i in range(len(Column_data)):
        dataum = {}
        dataum["inRelationTo"] = inRelationTo_data[i]
        dataum["wasDerivedFrom"] = wasDerivedFrom_data[i]

        if Column_data[i][:2]!="??" :
            dataum["Attribute"] = Attribute_data[i]
            dataum["attributeOf"] = attributeOf_data[i]
            dataum["Unit"] = Unit_data[i]
            dataum["Time"] = Time_data[i]
            dataum["wasGeneratedBy"] = wasGeneratedBy_data[i]

            schema_data[Column_data[i]] = dataum

        else:
            dataum["Entity"] = Entity_data[i]
            dataum["Role"] = Role_data[i]
            dataum["Relation"] = Relation_data[i]

            entity_data[Column_data[i]] = dataum

    return [schema_data, entity_data]
