
from rdflib import Graph, Literal, RDF, URIRef, BNode, Namespace, DC, DCTERMS, OWL, RDFS, VANN, XSD
from rdflib.namespace import DefinedNamespace, Namespace
import owlready2 as owlapi
import yamlLib.TSSOMod as tsso

class IIntermediateFactory:

    def __init__(self,extensions):
        self.extensions = extensions

    def processFile(self):
        pass

    def isExtensionSupported(self):
        return False
    
    def getExtension(self):
        pass

# generic class that has to be implemented to create a graph representation of the deseired format.
# The intermediate representation can then be mapped by a IOntologyFactory to ontology constructs
class IIntermediateModel:
    def __init__(self, extensions, filePath):
        self.filePath = filePath
        self.nodes = {}
        self.extensions = extensions
        self.relations = []
        # nodes that don't need to be materialized but contain meta data proper of the origin fornmat
        self.metaNodes = {}
        self.metaRelations = []
        self.valid= True

    def getExtensions(self):
        return self.extensions

    def isExtensionSupported(self, ext):
        return ext in self.extensions

    def processFile(self):
        pass

    def getNodes(self):
        return self.nodes

    def getRelations(self):
        return self.relations

    def getNode(self, name):
        for node in self.nodes:
            if node.name == name:
                return node

    def resolveMetaRelation(self, meta, factory):
        pass

    def isValid(self):
        return self.valid
# base element containing the fields required for reconstruction in both directions


class IBase:
    def __init__(self):
        self.name = ""
        self.kind = ''
        self.description = ""
        self.attributes = []
        self.ontoReference = {}
        self.ontoNameSpace = {}

# generic node that represents classes or instances in both worlds
# these nodes can be connected among each other and be described by attributes


class INode(IBase):

    def __init__(self, name=""):
        super().__init__()
        self.name = name
        self.relations = []
        self.isClass = False

# generic connection between INodes
# it has a source and a destination


class IRelationship(IBase):
    def __init__(self):
        super().__init__()
        self.domains = []
        self.ranges = []

    def fromNode(self):
        return self.domains

    def toNode(self):
        return self.ranges

    def isWrapper(self):
        return False

# a wrapper of a relationship
# this means that original relationship will be replaced by the defined replacement
# can be replaced by a tool specifc construct that maps to a different kind of construct


class IRelationshipWrapper(IRelationship):
    def __init__(self, replace):
        super().__init__()
        self.origin = ''
        self.replace = replace

    def isWrapper(self):
        return True

    def getOrigin(self):
        return self.origin

    def getReplacement(self):
        return self.replace

# attribute of IBase elements


class IAttribute(IBase):
    def __init__(self, value={}):
        # literal value
        self.value = value
        # datatype
        self.datatype = ''


class IOntoReference:
    def __init__(self, obj):
        self.obj = obj
        # namespace object
        self.namespace = {}

# Generic node that holds information required for the source model
# they are intended to be referenced only through IMetaRelationship


class IMetaNode(INode):
    def __init__(self, name=""):
        super().__init__(name)


class IMetaAttribute(IAttribute):
    def __init__(self, value={}):
        super().__init__(value)

# Object used to connect main objects to meta objects which should not be considered when materializing


class IMetaRelationship(IRelationship):
    def __init__(self):
        super().__init__()

# Defines methods to create ontological elements
class IOntoFactory:

    def __init__(self, baseNS):
        self.concepts = []
        self.instances = []
        self.objectProperties = []
        self.dataProperties = []
        self.namespaces = []
        self.g = Graph()
        self.initDefaultNS()
        self.initDefautAnnotations()
        self.service = IOntoService()

    def initDefaultNS(self):
        # bind an RDFLib-provided namespace to a prefix
        self.g.bind("rdfs", RDFS)
        self.g.bind("owl", OWL)
        self.g.bind("dc", DC)
        self.g.bind("dcterm", DCTERMS)
        self.g.bind("xsd", XSD)
        self.g.bind("van", VANN)

    def initDefautAnnotations(self):
        annoList = [RDFS.comment, RDFS.label, DC.description]
        g = self.g
        for anno in annoList:
            g.add((anno, RDF.type, OWL.AnnotationProperty))
        # self.g.namespace_manager.


    def transformToOnto(self,baseFactory:IIntermediateModel):
        graph = self.g
        ns = self.baseNS
        nodes = baseFactory.getNodes()
        classNodes = [nodes[key] for key in nodes if nodes[key].isClass]
        for n in classNodes:
            print("Class: ", n)
            iriRef = ns[n.name]
            print(iriRef)

        instanceNodes = [nodes[key] for key in nodes if not nodes[key].isClass]
        for i in instanceNodes:
            print("Instance: ", i)
            instanceRef = ns[i.name]

            for att in i.attributes:
                mappedAtt = baseFactory.resolveMetaRelation(i, att, self)
                self.processAttribute(instanceRef, ns, att)

        for rel in baseFactory.relations:
            print("OP: ", rel.name, rel.domains, rel.ranges)
            ns = self.baseNS
            self.g.add((ns[self.cleanName(rel.domains)], ns[self.cleanName(
                rel.name)], ns[self.cleanName(rel.ranges)]))

        for rel in baseFactory.metaRelations:
            print("MetaOP: ", self.cleanName(rel.name), self.cleanName(
                rel.domains), self.cleanName(rel.ranges))

    def cleanName(self, name, isRel=False):
        return name

    def processAttribute(self, instanceRef, ns, att):
        print("Map Att:", instanceRef, " for ns:", ns, att)
        print(att.name, att.value, att.datatype)
        # self.g.add()
        pass

    def registerNamespace(self, prefix, ns):
        self.g.bind(prefix, ns)

    def addConcept(concept):
        pass

    def addInstance(self, iri, ClassIri):
        self.g.add((iri, RDF.type, ClassIri))
        pass

    def addObjectProperty(self, iriDom, iriOP, iriRange):
        self.g.add((iriDom, iriOP, iriRange))
        pass

    def addDataProperty(self):
        pass

    def getNSFor(self, iri):
        return URIRef(iri)

    def createIRIFor(self, path):
        return URIRef(path)

    def createBlank(self):
        return BNode()

    def createNS(self, iri):
        return Namespace(iri)

    def getValueFor(self, subjectIRI=None, opIRI=RDF.value):
        return self.g.value(subjectIRI, opIRI)


class Mapper:

    def __init__(self):
        self.ontoFactory = IOntoFactory()
        self.baseFactory = IIntermediateModel()

    def ontoToINode(self):
        pass

    def ontoToIRelation(self):
        pass

    def ontoToIAttribute(self):
        pass

    def baseToIOntoConcept(self):
        pass

    def baseToIOntoInstance(self):
        pass

    def baseToIOntoRelation(self):
        pass


def stringToList(s, separator=','):
    return [elem.strip() for elem in s.split(',')]


class IOntoService:

    def __init__(self, ontPath="C:\\Users\\illescas\\Desktop\\Jose\\Git\\TechnicalStandardsOntology\\Documentation\\resources\\ontology.nt"):
        self.onto = owlapi.get_ontology(ontPath).load()

    def searchCandidateOP(self, dom, range, name):
        owlapi.IRIS[name]
        if name==None or name== tsso.TSSO:
            # search depending on the domain and range
            res=tsso.TSSO.partOfComponentSolution
        else:
            tokens = ["*#"]+name.split(" ")
            searchPattern = "*".join(tokens)
            res= self.onto.search(iri=searchPattern)
            res= tsso.TSSO.partOfComponentSolution
        return res

    def getNS(self, iri):
        return self.onto.get_namespace(iri)

    def getClassIRI(self):
        pass

    def getInstanceIRI(self):
        pass

    def getOPIRI(self):
        pass

    def getDPIR(self):
        pass

    def getElementIRI(self, name):
        print(name in dir(tsso.TSSO))
        print(hasattr(tsso.TSSO,name))
        print(name)
        return tsso.TSSO[name] if hasattr(tsso.TSSO,name) else None

class IToolFormatValidator:


    def isValidFileContent(self,content):
        return False
    
    def validExpressionsMap(self):
        return {"":"Object"}
    
    def transformContentToObj(self,source):
        return {}
    
    def getKindOf(self,sourceItem):
        return -1
    
class IOntologyService:


    async def genericRetrievalOf(self,parameters, regex, filter):
        pass



    async def retrieveClasses(self):
       pass
    

    async def retrieveInstances(self):
        pass
    

    async def retrieveObjectProperties(self):
        pass

    def getKGAsGraph(self,url='http://OHIO:7200/repositories/SHACLTest/rdf-graphs/service?default')->Graph:
        dataGraph =  Graph()
        dataGraph.parse(url)
        print(f"Graph g has {len(dataGraph)} statements.")
        return dataGraph

