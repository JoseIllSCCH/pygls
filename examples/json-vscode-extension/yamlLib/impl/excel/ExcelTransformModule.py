# from TransformFramework import *
from rdflib import RDF, Namespace
import sys
import re
import pandas as pd
from yamlLib.base.TransformFramework import IAttribute, IIntermediateModel, IMetaAttribute, IMetaNode, IMetaRelationship, INode, IIRtoOntoTransformer, IRelationship, stringToList, IToolFormatValidator
from lsprotocol.types import (
    Diagnostic,
    Position,
    Range)
# from rdflib import Graph, Literal, RDF, URIRef, BNode, Namespace, DC,DCTERMS,OWL,RDFS,VANN,XSD

sys.path.append("..")
# print(sys.path)
EXCEL_SUBSTITUTION = "substitution"
ILO_ATT_NAME = "name"
ILO_ATT_ID = "id"
ILO_ATT_DESCRIPTION = 'description'
ILO_ATT_COLOR = 'color'

# RESOURCE CONSTANTS
ILO_RESOURCE_ABSTRACT = "abstract"
ILO_RESOURCE_INSTANCEOF = "instanceOf"
ILO_RESOURCE_CHILDREN = "children"
ILO_RESOURCE_SUBTITLE = 'subtitle'

# RELATIONS CONSTANTS
ILO_RELATIONS_FROM = 'from'
ILO_RELATIONS_TO = 'to'
ILO_RELATIONS_LABEL = 'label'

# PERSPECTIVE CONSTANTS
ILO_PERSPECTIVE_EXTENDS = 'extends'
ILO_PERSPECTIVE_NOTES = 'notes'
ILO_PERSPECTIVE_RELATIONS = 'relations'

# REPLACEMENT
ILO_META_REPLACEMENT = 'replacement'
ILO_META_REPLACEMENT_FOR_RESOURCE_INSTANCEOF = 'rdfs:type'
ILO_META_REPLACEMENT_FOR_RESOURCE_CHILDREN = 'None'


def createDiagnostic(msg, startLine=0, startChar=0, endLine=0, endChar=0, src=''):
    return Diagnostic(
        range=Range(
            start=Position(line=startLine, character=startChar),
            end=Position(line=endLine, character=endChar)
        ),
        message=msg,
        source=src)


class LimesTemplateExcelValidator(IToolFormatValidator):

    requiredFieldsResource = [ILO_ATT_NAME]
    optionalFieldsResource = [ILO_RESOURCE_SUBTITLE, ILO_ATT_DESCRIPTION,
                              ILO_RESOURCE_ABSTRACT, ILO_RESOURCE_INSTANCEOF, ILO_RESOURCE_CHILDREN, ILO_ATT_ID]

    requiredFieldRelations = [ILO_RELATIONS_FROM]
    optionalFieldsRelations = [
        ILO_RELATIONS_TO, ILO_RELATIONS_LABEL, ILO_ATT_DESCRIPTION, ILO_ATT_COLOR]

    requiredFieldPerspective = [ILO_ATT_NAME]
    optionalFieldsPerspective = [ILO_ATT_ID, ILO_PERSPECTIVE_NOTES,
                                 ILO_ATT_COLOR, ILO_PERSPECTIVE_EXTENDS, ILO_PERSPECTIVE_RELATIONS]

    typeMap = [{'regex': '(\s)*(-)?(\s)*name(\s)*:(\s)*$', 'kind': 0}, {'regex': '(\s)*(-)?(\s)*instanceOf(\s)*:(\s)*$',
                                                                        'kind': 0}, {'regex': '(\s)*(-)?(\s)*label(\s)*:(\s)*$', 'kind': 2}]

    EMPTY_VAL = ":(\s)*$"
    REQ_START = "^(\s)*(-)?(\s)*(name|instanceOf|label|from)"

    # gets the Files path
    # checks if the needed structure of file is provided
    # 1. Page Interface and Assets
    # 2. Expected columns are provided
    def isValidFileContent(self, source):
        df = self.transformContentToObj(source)
        colNames = [('Interface', True), ('Component', True), ('User', True), ('Assets', False)]

        for nameObj in colNames:
            name = nameObj[0]
            mandatory = nameObj[1]
            if mandatory:
                if not name in df.columns:
                    return False
        return True

    def validExpressionsMap(self):
        return self.typeMap

    def transformContentToObj(self, source):
        return pd.read_excel('C:\\Users\\illescas\\Documents\\ThreatRiskAnalysis-Template_anon.xlsx', sheet_name='Interfaces & Assets', skiprows=2)

    def getKindOf(self, sourceItem):
        for item in self.typeMap:
            regex = item['regex']
            if re.search(regex, sourceItem):
                print("{0} matched to regex {1}. Map to {2}".format(
                    sourceItem, regex, item['kind']))
                return item['kind']
        return -1

    def testWhole(self):
        return True

    def validationResults(self, source_txt):
        diagnostics = []
        lines = source_txt.lines
        # empty values
        pos = [(lines.index(x), len(x))
               for x in lines if re.search(self.REQ_START+self.EMPTY_VAL, x)]

        for p in pos:
            diagnostics.append(createDiagnostic("Empty value found.".format(""),
                               startLine=p[0], endLine=p[0], endChar=p[1]))
        return diagnostics
    # def checkRequiredFields(self, fields, obj):
    #     for req in fields:
    #         if req not in obj:
    #             return False

    #     return True

    def checkRequiredFields(self, kind, obj):
        if kind == 'resource':
            fields = self.requiredFieldsResource
        elif kind == 'relation':
            fields = self.requiredFieldRelations
        else:
            fields = self.requiredFieldPerspective

        for req in fields:
            if req not in obj:
                return False

        return True

    def completeListFor(self, kind, obj):

        if kind == 'resource':
            fields = self.requiredFieldsResource+[
                field for field in self.optionalFieldsResource if field in obj]
        elif kind == 'relation':
            fields = self.requiredFieldRelations+[
                field for field in self.optionalFieldsRelations if field in obj]
        else:
            fields = self.requiredFieldPerspective+[
                field for field in self.optionalFieldsPerspective if field in obj]
        return fields


class EntityMapKG:
    def __init__(self):
        self.classNameMap = {}
        self.propertyNameMap = {}
        self.attributeNameMap = {}

    def solveClass(self, name):
        return self.solveGeneric(self.classNameMap, name)

    def solveProperty(self, name):
        return self.solveGeneric(self.propertyNameMap, name)

    def solveAttribute(self, name):
        return self.solveGeneric(self.attributeNameMap, name)

    def solveGeneric(self, dic, name):
        return dic[name] if name in dic else name

    def registerClass(self, name, val):
        return self.registerGeneric(self.classNameMap, name, val)

    def registerProperty(self, name, val):
        return self.registerGeneric(self.propertyNameMap, name, val)

    def registerAttribute(self, name, val):
        return self.registerGeneric(self.attributeNameMap, name, val)

    def registerGeneric(self, dic, key, val):
        if not key in dic:
            dic[key] = val
        return dic[key]


class LimesTemplateExcelToIntermediateModel(IIntermediateModel):
    validator = LimesTemplateExcelValidator()
    mapper = EntityMapKG()

    def __init__(self, filePath=""):
        super().__init__(["xlsx"], filePath)

    def filterUniqueFrom(self,list, stringMatch):
        return [x for x in list if x.rfind(stringMatch) < 0]

    def createNode(self, id):
        if id not in self.nodes.keys():
            node = INode(id)
            self.nodes[id] = node
        else:
            node = self.nodes[id]
        return node
    
    def processProtocol(self,row):
        s = row[4]
        empty = pd.isna(s)
        if not empty and '/' in s:
            return s.split('/')
        elif empty:
            print("Use default")
        else:
            print(f"Skip {0}. Format not supported ",s)
        return []
    
    def createCustomConnectionName(self,row):
        l = ["Connection"]

        l.append(row[3].strip())
        l.append(row[2].strip())
        l.extend(self.processProtocol(row))

        name= "_".join(l)
        return re.sub("\\s","__",name)


    def createRelation(self,name,dom,ran):
        rel = IRelationship()
        rel.name = name
        self.relations.append(rel)
        rel.domains.append(dom)
        rel.ranges.append(ran)
        return rel
    
    def processRowAsLine(self,row):
        nodes = []
        # Component 0
        nodes.append(self.createNode(row[3]))
        # Interface or Protocol 1
        nodes.append(self.createNode(row[2]))
        # Constraint 2
        nodes.append(self.createNode(row[8]))
        
        # create connection node which will be core element 3
        nodes.append(self.createNode(self.createCustomConnectionName(row)))
        
        # Process Protocol/Port/Address 3 4 or no
        l = self.processProtocol(row)
        nodes.extend([self.createNode(n) for n in l])


        print(":)>", row[0], row[1][2])
        # att isExternal
        print(row[2], row[1])
        node=self.createNode(row[2])
        att = self.createAttributeNode(row[1])
        # uses
        print(row[3], row[2])
        self.createRelation("uses",nodes[0], nodes[4])
        # exposes Port
        print(row[2], row[3], row[4])
        self.createRelation("exposes Port",nodes[0], nodes[4])
        # over Protocol
        print(row[4])
        self.createRelation("over Protocol",nodes[0], nodes[4])
        # has constraint
        print(row[4], row[5])
        rel =self.createRelation("hasConstraint",nodes[0], nodes[4])
        rel.ontoNameSpace="tsso"
        # description
        print(row[4], row[8])
        # instances of User
        print(row[13:18])
        # instances of Asset

    def processLine(self, row,index):
        df = self.obj
        cols = self.obj.columns
        # if not self.iloValidator.checkRequiredFields('resource', resource):
        customNodes={"Coonection":{}}
        # return
        # isExternal
        print(df[[cols[2], cols[1]]])
        # uses
        print(df[[cols[3], cols[2]]])
        # has Port
        print(df[[cols[2], cols[3], cols[4]]])
        # over
        print(df[[cols[4]]])
        # description
        print(df[[cols[4], cols[5]]])
        # has constraint
        print(df[[cols[4], cols[8]]])
        # instances of User
        print(df.columns[13:18])
        # instances of Asset

    def createClassNodesFromColumns(self,customClasses=[]):
        # classes= [self.obj.columns[i] for i in [2,3,4,8,12,18]]
        classes = [item for string in [self.obj.columns[i]
                                       for i in [2, 3, 4, 8, 12, 18]] for item in string.split('/')]+customClasses
        for c in classes:
            id = c.strip()
            node = self.createNode(id)
            node.isClass = True
            id2 = self.mapper.solveClass(id)
            if id2 != id:
                # APPROACH 1
                typeRel = IMetaRelationship()
                typeRel.name = EXCEL_SUBSTITUTION
                typeRel.domains.append(self.createNode(node))
                typeRel.ranges.append(self.createNode(id2))
                self.metaRelations.append(typeRel)
                # APPROACH 2
                node.attributes.append(IMetaAttribute(EXCEL_SUBSTITUTION, id2))

    def createInstanceNodesFromColumns(self, childIndices, parentIndices):
        childClasses = [self.mapper.solveClass(
            self.obj.columns[childIndex]) for childIndex in childIndices]
        parentClasses = [self.mapper.solveClass(
            self.obj.columns[parentIndex]) for parentIndex in parentIndices]

        for c in childClasses:
            for parentClass in parentClasses:
                typeRel = IMetaRelationship()
                typeRel.name = ILO_META_REPLACEMENT_FOR_RESOURCE_INSTANCEOF
                typeRel.domains.append(self.createNode(c))
                typeRel.ranges.append(self.createNode(parentClass))
                typeRel.replacement = ILO_META_REPLACEMENT_FOR_RESOURCE_INSTANCEOF
                self.metaRelations.append(typeRel)

    def processData(self, data_src, validate=False):
        if validate and not self.validator.isValidFileContent(data_src):
            raise Exception("The content of the file is not valid")

        self.obj = self.validator.transformContentToObj(data_src)
        # CREATE class nodes for columns
        self.createClassNodesFromColumns(["Connection"])

        # Create instance nodes for columns
        # Users
        self.createInstanceNodesFromColumns([13, 14, 15, 16, 17], [12])
        # Assets
        self.createInstanceNodesFromColumns([19, 20, 21], [18])

        # access elements by index
        for r in self.obj.iterrows():
            print(":)>", r[0], r[1][2])
            self.processRowAsLine(r)
            self.processLine(r)
        # process Nodes for instances

    def processFile(self):
        super().processFile()
        with open(self.filePath, "r") as stream:
            self.processData(stream)

    def processNativeResource(self, resource):

        if not self.validator.checkRequiredFields('resource', resource):
            return

        id = resource[ILO_ATT_ID] if ILO_ATT_ID in resource else resource[ILO_ATT_NAME]
        # check if node already exists if not create id with the given id
        if id not in self.nodes.keys():
            node = INode(id)
            self.nodes[id] = node
        else:
            node = self.nodes[id]

        # process required fields
        # optional fields that exist in the resource
        for field in self.validator.completeListFor('resource', resource):
            self.processNodeField(field, resource, node)

    def processNodeField(self, fieldName, resource, node: INode):
        # lowerFieldName = fieldName.casefold()
        # identify special attributes that need special handling
        if fieldName == ILO_RESOURCE_ABSTRACT:
            node.isClass = resource[fieldName]
        elif fieldName == ILO_RESOURCE_INSTANCEOF:
            typeRel = IMetaRelationship()
            typeRel.name = ILO_RESOURCE_INSTANCEOF
            typeRel.domains.append(node.name)
            typeRel.ranges.append(resource[fieldName])
            typeRel.replacement = ILO_META_REPLACEMENT_FOR_RESOURCE_INSTANCEOF
            self.metaRelations.append(typeRel)
        elif fieldName == ILO_RESOURCE_CHILDREN:
            # traverse all children resource first before creating edges
            for childResource in resource[fieldName]:
                self.processNativeResource(childResource)
                typeRel = IMetaRelationship()
                typeRel.name = ILO_RESOURCE_CHILDREN
                typeRel.domains.append(childResource[ILO_ATT_NAME])
                typeRel.ranges.append(node.name)
                typeRel.replacement = ILO_META_REPLACEMENT_FOR_RESOURCE_CHILDREN
                self.metaRelations.append(typeRel)
        else:
            att = IAttribute()
            att.name = fieldName
            att.value = resource[fieldName]
            att.kind = "ATTRIBUTE"
            att.datatype = 'string'
            node.attributes.append(att)

    def processNativePerspective(self, perspective):
        if not self.validator.checkRequiredFields('perspective', perspective):
            return

        id = perspective[ILO_ATT_ID] if ILO_ATT_ID in perspective else perspective[ILO_ATT_NAME]

        # check if node already exists if not create id with the given id
        if id not in self.metaNodes.keys():
            node = IMetaNode(id)
            self.metaNodes[id] = node
        else:
            node = self.metaNodes[id]

        # process required and optional fields that exist in the resource
        for field in self.validator.completeListFor('perspective', perspective):
            self.processNodeFieldForPerspective(field, perspective, node)

    def processNodeFieldForPerspective(self, fieldName, perspective, node: INode):
        # lowerFieldName = fieldName.casefold()
        # # identify special attributes that need special handling
        if fieldName == ILO_PERSPECTIVE_EXTENDS:
            # traverse all children resource first before creating edges
            for parentPerspective in stringToList(perspective[fieldName]):
                typeRel = IMetaRelationship()
                typeRel.name = ILO_PERSPECTIVE_EXTENDS
                typeRel.domains.append( node.name)
                typeRel.ranges.append(parentPerspective)
                self.metaRelations.append(typeRel)
        elif fieldName == ILO_PERSPECTIVE_RELATIONS:
            for relation in perspective[fieldName]:
                self.processNativeRelation(relation)
        else:
            att = IMetaAttribute()
            att.name = fieldName
            att.value = perspective[fieldName]
            att.kind = "ATTRIBUTE"
            att.datatype = 'string'
            node.attributes.append(att)

    def processNativeRelation(self, relation):
        if not self.validator.checkRequiredFields('relation', relation):
            return

        # process required fields
        # optional fields that exist in the resource
        for dom in stringToList(relation[ILO_RELATIONS_FROM]):
            ranges = stringToList(
                relation[ILO_RELATIONS_TO]) if ILO_RELATIONS_TO in relation else ['']
            # create one edge for each pair
            for ran in ranges:
                node = IRelationship()
                self.relations.append(node)
                node.domains.append(dom)
                node.ranges.append(ran)
                # process remaining fields
                for field in self.validator.completeListFor('relation', relation):
                    self.processFieldForRelation(field, relation, node)

    def processFieldForRelation(self, fieldName, relation, node):
        if fieldName == ILO_RELATIONS_FROM or fieldName == ILO_RELATIONS_TO:
            pass
        elif fieldName == ILO_RELATIONS_LABEL:
            node.name = relation[fieldName]
        elif fieldName == ILO_ATT_DESCRIPTION:
            node.description = relation[fieldName]
        else:
            att = IAttribute()
            att.name = fieldName
            att.value = relation[fieldName]
            att.kind = "ATTRIBUTE"
            att.datatype = 'string'
            node.attributes.append(att)

    def resolveMetaRelation(self, node: INode, meta: IMetaRelationship, factory: IIRtoOntoTransformer):
        ns = factory.baseNS
        if meta.name == ILO_RESOURCE_INSTANCEOF:
            return "rdfs:type"
        elif meta.name == ILO_ATT_NAME:
            return "rdfs:label"
        pass


class DefaultIRToOntoTransformer(IIRtoOntoTransformer):

    def __init__(self, baseNS="https://w3id.org/tsso#", graphPath=""):
        super().__init__(baseNS)
        if graphPath != "":
            self.g.parse(graphPath)
        self.baseNS = Namespace(baseNS)
        self.g.bind("tsso", self.baseNS)

    def transformToOnto(self, intermediateModel: IIntermediateModel):
        if intermediateModel == None:
            pass
        processedRelations = []
        processedMetaRelations = []
        graph = self.g
        ns = self.baseNS
        nodes = intermediateModel.getNodes()
        classNodes = [nodes[key] for key in nodes if nodes[key].isClass]
        for n in classNodes:
            print("Class: ", n.name, self.service.getElementIRI(n.name))
            # self.g.add((self.service.))

        print()
        instanceNodes = [nodes[key] for key in nodes if not nodes[key].isClass]
        for i in instanceNodes:
            instanceRef = ns[i.name]

            for att in i.attributes:
                mappedAtt = intermediateModel.resolveMetaRelation(i, att)
                self.processAttribute(instanceRef, ns, att)

            print()

            self.processRelations(
                [relD for relD in intermediateModel.relations if relD.domains == i.name], processedRelations)

            print()

            self.processMetaRelations([relD for relD in intermediateModel.metaRelations if hasattr(
                relD, 'replacement') and relD.domains == i.name], processedMetaRelations)

            print("Instance: ", instanceRef)

            print()
            print()

        self.processRelations(
            [t for t in intermediateModel.relations if t not in processedRelations], processedRelations)

        self.processMetaRelations(
            [t for t in intermediateModel.metaRelations if t not in processedMetaRelations], processedMetaRelations)

        # Print the number of "triples" in the Graph
        print(f"Graph g has {len(graph)} statements.")
        # Prints: Graph g has 86 statements.

        # Print out the entire Graph in the RDF Turtle format
        onotString = graph.serialize(format="turtle")
        print(onotString)
        return onotString

    def cleanName(self, name, isRel=False):
        tokens = name.split(" ")
        res = tokens[0]
        return res if not isRel else res.casefold()+("".join([t.capitalize() for t in tokens[1:]]) if len(tokens) > 1 else "")

    def processRelations(self, relList, vistedList, message="OP"):
        ns = self.baseNS
        for rel in relList:
            instanceRef = ns[rel.domains]
            print(message, "> Relationship to process for ", instanceRef, rel.name)
            op = ns[self.cleanName(rel.name, isRel=True)]
            self.g.add((instanceRef, op, ns[rel.ranges]))
            vistedList.append(rel)
        print()

    def processMetaRelations(self, metaList, visitedList, message="MetaOP"):
        ns = self.baseNS
        for rel in metaList:
            print(message, self.cleanName(rel.name), self.cleanName(
                rel.domains), self.cleanName(rel.ranges))
            hasReplacement = hasattr(rel, ILO_META_REPLACEMENT)
            if hasReplacement:
                print("MetaRelationship", rel.name,
                      " (", rel.replacement, ")to process for ", rel)

            if rel.name == ILO_RESOURCE_INSTANCEOF:
                self.g.add((ns[rel.domains], RDF.type, ns[rel.ranges]))
            elif rel.name == ILO_RESOURCE_CHILDREN and hasReplacement:
                self.g.add((ns[rel.domains], self.service.searchCandidateOP(
                    rel.domains, rel.ranges, ns[rel.replacement]), ns[rel.ranges]))
            else:
                pass
                # raise Exception("No proper ")
            visitedList.append(rel)

    def processAttribute(self, instanceRef, ns, att):
        print("Map Att:", instanceRef, " for ns:", ns, att)
        print(att.name, att.value, att.datatype)
        # self.g.add()
        pass

    def findCandidateRelationshipFor(self, dom, range, name):
        return "owl:TopObjectProperty" if not name else name

    def getValueFor(self, subjectIRI=None, opIRI=RDF.value):
        return self.g.value(subjectIRI, opIRI)

    def testForSubject(self, subject):
        for t in self.g.triples((subject, None, None)):
            print(t)
