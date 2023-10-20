# from TransformFramework import *
from rdflib import RDF, Namespace
import yaml
import sys
import re

from yamlLib.base.TransformFramework import IAttribute, IIntermediateModel, IMetaAttribute, IMetaNode, IMetaRelationship, INode, IOntoFactory, IRelationship, stringToList, IToolFormatValidator
from lsprotocol.types import (
    Diagnostic,
    Position,
    Range)
# from rdflib import Graph, Literal, RDF, URIRef, BNode, Namespace, DC,DCTERMS,OWL,RDFS,VANN,XSD

sys.path.append("..")
# print(sys.path)

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
ILO_META_REPLACEMENT_FOR_RESOURCE_CHILDREN = None

def createDiagnostic(msg, startLine=0, startChar=0, endLine=0, endChar=0, src=''):
        return Diagnostic(
            range=Range(
                start=Position(line=startLine, character=startChar),
                end=Position(line=endLine, character=endChar)
            ),
            message=msg,
            source=src)

class ILOValidator(IToolFormatValidator):

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

    def isValidFileContent(self, source):
        obj = self.transformContentToObj(source)
        return type(obj) is dict and obj.get('resources') != None and obj.get('perspectives') != None and self.testWhole()

    def validExpressionsMap(self):
        return self.typeMap

    def transformContentToObj(self, source):
        return yaml.safe_load(source)

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
        lines =source_txt.lines
        # empty values
        pos=[(lines.index(x),len(x)) for x in lines if re.search(self.REQ_START+self.EMPTY_VAL,x)]

        for p in pos:
                diagnostics.append(createDiagnostic("Empty value found.".format(""),startLine=p[0],endLine=p[0],endChar=p[1]))
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




class ILOGraphToIntermediateModel(IIntermediateModel):
    iloValidator = ILOValidator()

    def nameExp():
        pass

    def simpleStringExp():
        pass

    def fromExp():
        pass

    def labelExp():
        pass

    def toExp():
        pass

    def descriptionExp():
        pass

    def abstractExp():
        pass

    def arrayResourceExp():
        pass

    def __init__(self, filePath=""):
        super().__init__(["yaml"], filePath)

    def processData(self, data_src, validate=False):
        try:
            data = data_src.source
            print(data)
            self.yamlObj = yaml.safe_load(data)
        except yaml.YAMLError as exc:
            print(exc)
            return

        if validate and not self.iloValidator.isValidFileContent(data):
            raise Exception("The content of the file is not valid", args=self.iloValidator.val)

        resource = self.yamlObj['resources']

        for r in resource:
            self.processNativeResource(r)

        perspectives = self.yamlObj['perspectives']

        print(len(perspectives))
        for perspective in perspectives:
            self.processNativePerspective(perspective)

    def processFile(self):
        super().processFile()
        with open(self.filePath, "r") as stream:
            self.processData(stream)

    def processNativeResource(self, resource):

        if not self.iloValidator.checkRequiredFields('resource', resource):
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
        for field in self.iloValidator.completeListFor('resource', resource):
            self.processNodeField(field, resource, node)

    def processNodeField(self, fieldName, resource, node: INode):
        # lowerFieldName = fieldName.casefold()
        # identify special attributes that need special handling
        if fieldName == ILO_RESOURCE_ABSTRACT:
            node.isClass = resource[fieldName]
        elif fieldName == ILO_RESOURCE_INSTANCEOF:
            typeRel = IMetaRelationship()
            typeRel.name = ILO_RESOURCE_INSTANCEOF
            typeRel.domains = node.name
            typeRel.ranges = resource[fieldName]
            typeRel.replacement = ILO_META_REPLACEMENT_FOR_RESOURCE_INSTANCEOF
            self.metaRelations.append(typeRel)
        elif fieldName == ILO_RESOURCE_CHILDREN:
            # traverse all children resource first before creating edges
            for childResource in resource[fieldName]:
                self.processNativeResource(childResource)
                typeRel = IMetaRelationship()
                typeRel.name = ILO_RESOURCE_CHILDREN
                typeRel.domains = childResource[ILO_ATT_NAME]
                typeRel.ranges = node.name
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
        if not self.iloValidator.checkRequiredFields('perspective', perspective):
            return

        id = perspective[ILO_ATT_ID] if ILO_ATT_ID in perspective else perspective[ILO_ATT_NAME]

        # check if node already exists if not create id with the given id
        if id not in self.metaNodes.keys():
            node = IMetaNode(id)
            self.metaNodes[id] = node
        else:
            node = self.metaNodes[id]

        # process required and optional fields that exist in the resource
        for field in self.iloValidator.completeListFor('perspective', perspective):
            self.processNodeFieldForPerspective(field, perspective, node)

    def processNodeFieldForPerspective(self, fieldName, perspective, node: INode):
        # lowerFieldName = fieldName.casefold()
        # # identify special attributes that need special handling
        if fieldName == ILO_PERSPECTIVE_EXTENDS:
            # traverse all children resource first before creating edges
            for parentPerspective in stringToList(perspective[fieldName]):
                typeRel = IMetaRelationship()
                typeRel.name = ILO_PERSPECTIVE_EXTENDS
                typeRel.domains = node.name
                typeRel.ranges = parentPerspective
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
        if not self.iloValidator.checkRequiredFields('relation', relation):
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
                node.domains = dom
                node.ranges = ran
                # process remaining fields
                for field in self.iloValidator.completeListFor('relation', relation):
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

    def resolveMetaRelation(self, node: INode, meta: IMetaRelationship, factory: IOntoFactory):
        ns = factory.baseNS
        if meta.name == ILO_RESOURCE_INSTANCEOF:
            return "rdfs:type"
        elif meta.name == ILO_ATT_NAME:
            return "rdfs:label"
        pass


class IntermediateToOntoFactory(IOntoFactory):

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
                mappedAtt = intermediateModel.resolveMetaRelation(i, att, self)
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
