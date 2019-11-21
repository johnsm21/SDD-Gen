import view
import helper_function

class SDD:
    """A class that programmatically builds a Semantic Data Dictionary"""

    sdd = {}
    prefixes = {}
    sioLabels = False

    def __init__(self, graphs, sioLabels = False):
        # Init prefix mapping
        p_sheet = []
        for g in graphs:
            row = {}

            self.prefixes[g] = view.getPrefixCC(g)
            row["Prefix"] = self.prefixes[g]
            
            if not (g[-1] == '/') or (g[-1] == '#'):
                g = g + '#' # We assume were # IRI if were missing a trailing character



            row["URI"] = g

            p_sheet.append(row)
        self.sdd['Prefixes'] = p_sheet

        # Init dictionary mapping
        dm_sheet = {}
        dm_sheet['columns'] = []
        dm_sheet['virtual-columns'] = []
        self.sdd['Dictionary Mapping'] = dm_sheet
        self.sioLabels = sioLabels

    def __reduceIRI(self, iri):

        # check for sio Labels
        if self.sioLabels :
            sioIRI = 'http://semanticscience.org/resource/'
            if sioIRI in iri:
                iri = helper_function.getSioLabel(iri)

        for prefixIri, prefix in self.prefixes.items():
            if prefixIri in iri:
                return iri.replace(prefixIri, prefix + ':')
        return iri

    def generateAcc(self, sddGT):
        [gt_columns, gt_vcolumns] = helper_function.sdd_loader(sddGT)
        # print('schema_data = ' + str(gt_columns))
        # print('entity_data = ' + str(gt_vcolumns))

        attributeCorrect = 0
        total = 0
        for column in self.sdd['Dictionary Mapping']['columns']:
            if column['column'] in gt_columns:
                total = total + 1
                for attribute in column['attribute']:
                    if gt_columns[column['column']]['Attribute'] == attribute['value']:
                        attributeCorrect = attributeCorrect + 1
                        break    # We only count it once
        attributeCorrect = (attributeCorrect * 100) / len(self.sdd['Dictionary Mapping']['columns'])
        self.sdd['Accuracy'] = {'attribute': attributeCorrect}
        return None

    # Assuming [(IRI, conf, star), ]
    def addDMColumn(self, column, attribute = None, attributeOf = None, unit = None, time = None, entity = None, role = None, relation = None, inRelationTo = None, wasDerivedFrom = None, wasGeneratedBy = None):
        col = {}
        col['column'] = column

        if attribute is not None:
            col['attribute'] = []
            for i in attribute:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['attribute'].append(rslt)

        if attributeOf is not None:
            col['attributeOf'] = []
            for i in attributeOf:
                rslt = {}
                rslt["value"] = i[0]
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['attributeOf'].append(rslt)

        if unit is not None:
            col['Unit'] = []
            for i in unit:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['Unit'].append(rslt)

        if time is not None:
            col['Time'] = []
            for i in time:
                rslt = {}
                rslt["value"] = i[0]
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['Time'].append(rslt)

        if entity is not None:
            col['Entity'] = []
            for i in entity:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['Entity'].append(rslt)

        if role is not None:
            col['Role'] = []
            for i in role:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['Role'].append(rslt)

        if relation is not None:
            col['Relation'] = []
            for i in relation:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['Relation'].append(rslt)

        if inRelationTo is not None:
            col['inRelationTo'] = []
            for i in inRelationTo:
                rslt = {}
                rslt["value"] = i[0]
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['inRelationTo'].append(rslt)

        if wasDerivedFrom is not None:
            col['wasDerivedFrom'] = []
            for i in wasDerivedFrom:
                rslt = {}
                rslt["value"] = i[0]
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['wasDerivedFrom'].append(rslt)

        if wasGeneratedBy is not None:
            col['wasGeneratedBy'] = []
            for i in wasGeneratedBy:
                rslt = {}
                rslt["value"] = self.__reduceIRI(i[0])
                rslt["confidence"] = i[1]
                rslt["star"] = i[2]
                col['wasGeneratedBy'].append(rslt)

        if column.startswith('??'):
            self.sdd['Dictionary Mapping']['virtual-columns'].append(col)
        else:
            self.sdd['Dictionary Mapping']['columns'].append(col)
