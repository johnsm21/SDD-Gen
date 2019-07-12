import view

class SDD:
    """A class that programmatically builds a Semantic Data Dictionary"""

    sdd = {}
    prefixes = {}

    def __init__(self, graphs):
        # Init prefix mapping
        p_sheet = []
        for g in graphs:
            self.prefixes[g] = view.getPrefixCC(g)
            row = {}
            row["Prefix"] = self.prefixes[g]
            row["URI"] = g
            p_sheet.append(row)
        self.sdd['Prefixes'] = p_sheet

        # Init dictionary mapping
        dm_sheet = {}
        dm_sheet['columns'] = []
        dm_sheet['virtual-columns'] = []
        self.sdd['Dictionary Mapping'] = dm_sheet

    def __reduceIRI(self, iri):
        for prefixIri, prefix in self.prefixes.items():
            if prefixIri in iri:
                return iri.replace(prefixIri, prefix + ':')
        return iri


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
