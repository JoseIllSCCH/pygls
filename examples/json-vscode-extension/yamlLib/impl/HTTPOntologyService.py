import urllib.parse
import requests
import re

from yamlLib.base.TransformFramework import IOntologyService

OWL_NS = "http://www.w3.org/2002/07/owl#";
RDF_NS = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#';
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
DC_TERMS_NS = "http://purl.org/dc/terms/"


CLASS = 'Class'
INSTANCES = 'NamedIndividual'
OP = 'ObjectProperty'
DP = 'DataTypeProperty'
ANNO = "AnnotationProperty"
TYPE = "type"

RDFS_COMMENT = "comment"
RDFS_LABEL = "label"

RDFS_DOMAIN = "domain"
RDFS_RANGE = "range"

TSSO_NS_REGEX = "\Ahttp(s)?:(.)*technical_standards#"

def encodeURIComponent(text):
    return urllib.parse.quote(text,safe='')

class HTTPService(IOntologyService):

    def __init__(self,url):
        self.repoURL= url

    

    async def genericRetrievalOf(self,parameters, regex=TSSO_NS_REGEX, filter=True):
        fullPars = parameters+["infer=True"]
        textPars = "&".join(fullPars)
        headers= {'Accept':'application/rdf+json'}

        response  = requests.get(self.repoURL+textPars, headers= headers)
        if response.ok:
            result = response.json()
            classes = [ k  for k in result if filter and re.search(regex, k)]
            return classes
        else: 
            result=[]
            print("Not OK")
        return result



    async def retrieveClasses(self):
        return await self.genericRetrievalOf(["pred=" + encodeURIComponent("<" + RDF_NS + TYPE + ">"), "obj=" + encodeURIComponent("<" + OWL_NS + CLASS + '>')])
    

    async def retrieveInstances(self):
        return await self.genericRetrievalOf(["pred=" + encodeURIComponent("<" + RDF_NS + TYPE + ">"), "obj=" + encodeURIComponent("<" + OWL_NS + INSTANCES + '>')])
    

    async def retrieveObjectProperties(self):
        return await self.genericRetrievalOf(["pred=" + encodeURIComponent("<" + RDF_NS + TYPE + ">"), "obj=" + encodeURIComponent("<" + OWL_NS + OP + '>')])
    

