import rdflib
from rdflib import Graph,URIRef
from pyshacl import validate
from datetime import datetime
from lsprotocol.types import (Diagnostic,Position, Range, DiagnosticSeverity,MessageType)
import re

# ValidationResult items IRI
res_FocusNode_IRI=URIRef("http://www.w3.org/ns/shacl#focusNode")
res_ResultPath_IRI=URIRef("http://www.w3.org/ns/shacl#resultPath")
res_Value_IRI=URIRef("http://www.w3.org/ns/shacl#value")
res_SourceShape_IRI=URIRef("http://www.w3.org/ns/shacl#sourceShape")
res_SourceConstraintComponent_IRI=URIRef("http://www.w3.org/ns/shacl#sourceConstraintComponent")
res_Detail_IRI=URIRef("http://www.w3.org/ns/shacl#detail")
res_ResultMessage_IRI=URIRef("http://www.w3.org/ns/shacl#resultMessage")
res_ResultSeverity_IRI=URIRef("http://www.w3.org/ns/shacl#resultSeverity")
res_SourceConstraint_IRI=URIRef("http://www.w3.org/ns/shacl#sourceConstraint")

#Severity Values IRI
#infoSeverityIRI = URIRef("http://www.w3.org/ns/shacl#Information")
warningSeverityIRI = URIRef("http://www.w3.org/ns/shacl#Warning")
violationSeverityIRI = URIRef("http://www.w3.org/ns/shacl#Violation")

#Filtering elements to retrieve only the subject of kind ValidationResult
typeIRI = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
validationResultsIRI = URIRef("http://www.w3.org/ns/shacl#ValidationResult")

SHACL_Keys={"Severity":res_ResultSeverity_IRI,
            "Conflicting Item":res_FocusNode_IRI,
            "Shape":res_SourceShape_IRI,
            "Constraint Component":res_SourceConstraintComponent_IRI,
            "Value":res_Value_IRI,
            "Path":res_ResultPath_IRI,
            "Message":res_ResultMessage_IRI,
            "Detail":res_Detail_IRI
#              "Violated Constraint":res_SourceConstraint_IRI
           }
#            "Information",
#             "Warning":warningSeverityIRI,
#             "Violation":violationSeverityIRI}

attributesList = list(SHACL_Keys.keys())




def matchingClass(line,className):
  txt = line.strip()
  #Check if the string starts with "- name:":
  x = re.findall("\A-(\s)*name(\s)*:(\s)*"+className+"$", txt)

  return True if x else False


def validateContent(dataGraph,shaclGraph):
    validationResult= validate(data_graph=dataGraph,shacl_graph=shaclGraph,ont_graph=None,
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=False,
            meta_shacl=True,
            advanced=True,
            js=False,
            debug=False)
    return validationResult
        


def prepareSHACLDiagnostics(ls,validationResult,text_doc):
        conforms, results_graph, results_text = validationResult
        print(results_graph)
        print("**************************")
        print(results_text)
#         print(validationResult)

        
        validationResultMap = {}
        
        #extract information from validation graph for the validation result items and filter by subjects
        for sub in results_graph.subjects(typeIRI,validationResultsIRI):
            #extract infor6mation that is relevant from each validation result such as severity, focus node, constraint component, etc
            for pred, obj in results_graph.predicate_objects(sub):
                if not (pred==typeIRI):
                    #convert subject's iri to string 
                    subj=str(sub)
                    # create a map between validation result entry and attributes 
                    curr= validationResultMap[subj] if subj in validationResultMap else {}
                    #new subject==blank node found, therefore a new validation result entry must be recorded 
                    if(subj not in validationResultMap):
                        validationResultMap[subj]={}
                    #obtain entry's map
                    curr=validationResultMap[subj]
                    #record attribute
                    curr[pred]=obj    

        
        #add results to tabs
        print(printValidationResult(conforms,validationResultMap))
        return createDiagnosticsForResult(ls,conforms,validationResultMap,text_doc.lines)


def severityAsString(severityIRI):
    severityAsString = str(severityIRI)
    index = severityAsString.rindex("#")
    return severityAsString[(index if index>0 else 0)+1:]


def printValidationResult(conforms, vR,selectedAtts =attributesList):
    #Output to third tab
    msgList = []
    msgList.append(datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))
    msgList.append("Graph Conforms to Shape Graph:{0}".format(conforms))
    msgList.append("Validation found {0} violations.".format(len(vR)))

    msgList.append("\n")
    msgList.append("=== Attributes that will be considered ===")    
    #Selected tags, if empty then we consider all

    for att in selectedAtts:
        msgList.append(" ".join([att,">",SHACL_Keys[att]]))
    msgList.append("=== \n")

    count=0
    for item in vR:
        valResult = vR[item];
        severityStr = severityAsString(valResult[res_ResultSeverity_IRI])
        msgList.append("{0}) {1}".format(count,severityStr.upper()))

        count=count+1
        for atts in selectedAtts:
            resEntry = SHACL_Keys[atts]
            if resEntry!=res_ResultSeverity_IRI and resEntry in valResult:
                val = valResult[resEntry]
                msgList.append(" ".join([atts,val]))
        msgList.append("\n")

    return "\n".join(msgList)

def createDiagnosticElement(msg, startLine=0, startChar=0, endLine=0,endChar=0,severity= DiagnosticSeverity.Warning):
    d = Diagnostic(
            range=Range(
                start=Position(line=startLine, character=startChar),
                end=Position(line=endLine, character=endChar)
            ),
            message=msg)
    return d

def createDiagnosticsForResult(ls,conforms,validationResultMap,source_lines,selectedAtts =attributesList):
    diagnostics=[]

    #Output to third tab
    msgList = []
    msgList.append(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    msgList.append("Graph Conforms to Shape Graph:{0}".format(conforms))
    msgList.append("Validation found {0} violations.".format(len(validationResultMap)))

    # diagnostics.append(createDiagnosticElement("\n".join(msgList)))

    ls.show_message("\n".join(msgList),MessageType.Error)
    # print("=== Attributes that will be considered ===")    
    # #Selected tags, if empty then we consider all

    # for att in selectedAtts:
    #    print(att,">",SHACL_Keys[att])
    # print("=== \n")

    count=0
    for item in validationResultMap:
        msgList = []
        valResult = validationResultMap[item]
        severityStr = severityAsString(valResult[res_ResultSeverity_IRI])
        msgList.append("{0}) {1}".format(count,severityStr.upper()))

        count=count+1
        for atts in selectedAtts:
            resEntry = SHACL_Keys[atts]
            if resEntry!=res_ResultSeverity_IRI and resEntry in valResult:
                val = valResult[resEntry]
                msgList.append("{0} {1}".format(atts,val))
                if  atts=="Conflicting Item":
                    line_pos = determinePosFor(atts,val[val.index('#')+1:],source_lines)
        msgList.append("\n")


        diagnostics.append(createDiagnosticElement("\n".join(msgList),startLine=line_pos[0][0],endLine=line_pos[0][0],endChar=line_pos[0][1]))

    
    return diagnostics

def determinePosFor(att,val, lines):
    res = [(lines.index(x),len(x)) for x in lines if matchingClass(x,val)]
    return res if res else (0,0)
# def printValidationResultsTab(conforms, vR):
#     out = secondPane.children[0]
#     #New lists for tabpane
#     children = []
#     titles= []
#     #Selected tags, if empty then we consider all
#     selectedAtts = tags.value if len(tags.value)>0 else attributesList
#     with out:
#         # Getting the current date and time
#         print(datetime.now())
#         print("Graph Conforms to Shape Graph:",conforms)
#         print("Validation found {0} violations.".format(len(vR)))

#         print()
#         print("=== Attributes that will be considered ===")    
        
#         for att in selectedAtts:
#             print(att,">",SHACL_Keys[att])
#         print("=== \n")
    
#     print()
#     count=0
#     for item in vR:
#         valResult = vR[item];
#         severityStr = severityAsString(valResult[res_ResultSeverity_IRI])
#         children.append(widgets.Output(layout={'border': '1px solid red'}));
#         out = children[len(children)-1]
        
#         with out:
#             titles.append("{0}) {1}".format(count,severityStr.upper()))

#             count=count+1
#             for atts in selectedAtts:
#                 resEntry = SHACL_Keys[atts]
#                 if resEntry!=res_ResultSeverity_IRI and resEntry in valResult:
#                     val = valResult[resEntry]
#                     print(atts,val)
#             print()
    
#     accordion.children = children
#     accordion.titles= titles

class ISHACLService:
    shapesGraph =  Graph()

    def __init__(self) -> None:
        pass

    def addToGraph():
        pass

    def resetGraph(self):
        self.shapesGraph = Graph()


    def parse(self,local):
        self.shapesGraph.parse(local)


class LocalSHACLService(ISHACLService):
    constraints =[ """
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:    <http://www.example.org/#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix :   <http://www.scch.org/proto#>.
@prefix ts: <https://w3id.org/tsso#>.

# Property restriction on hasCapability, that means that at least one hasCapability is expected
ex:ComponentShape-capability
	a sh:PropertyShape ;
	sh:path ts:hasCapability;
	sh:minCount 1 ;
	sh:deactivated false.

# Property restriction on hasSolutionStructure, that means that at least one SolutionStrcuture is expected
ex:SystemShape-solution
	a sh:PropertyShape ;
	sh:path ts:hasComponentSolution;
	sh:minCount 1 ;
	sh:deactivated false.
    
ex:ValidComponentShape
a sh:NodeShape;
sh:targetClass ts:Component;
sh:property ex:ComponentShape-capability.

ex:ValidSystemShape
a sh:NodeShape;
sh:targetClass ts:System;
sh:property ex:SystemShape-solution.

""","""
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:    <http://www.example.org/#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix :   <http://www.scch.org/proto2#>.
@prefix ts: <https://w3id.org/tsso#>.


ex:SecurityLevelProvisionShape
	a sh:NodeShape;
	sh:targetClass ts:Provision;
	sh:property[
		sh:path ts:securityLevel;
		sh:minInclusive 1;
		sh:maxInclusive 4;
	];
.

ex:SecurityLevelRequirementShape
	a sh:NodeShape;
	sh:targetClass ts:Requirement;
	sh:and(
	ex:SecurityLevelProvisionShape
	sh:property[
		sh:path ts:isMandatory;
		sh:hasValue true;
	]);
.

ex:CapabilityToRequirementShape
	a sh:NodeShape;
	sh:targetClass ts:Provision;
	sh:property[
		sh:path ts:demandsCapability;
		sh:class ts:Capability;
		sh:minCount 1;
	];
.
"""]
    
    def parseAll(self):
        for c in self.constraints:
            self.shapesGraph.parse(data=c)

    def parse(self,local):
        self.shapesGraph.parse(local)

    def getShapesGraph(self):
        return self.shapesGraph