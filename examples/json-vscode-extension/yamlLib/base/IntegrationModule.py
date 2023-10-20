from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import URIRef, BNode
from rdflib.namespace import RDF, OWL

class IIntegrationService:
    # Define the DBpedia SPARQL endpoint
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    dbs = {"DBPedia":"http://dbpedia.org/sparql"}

    found = ([],[])
    def searchForDBPedia(self,concept_to_check):
        term = concept_to_check[concept_to_check.rindex('#')+1:] if concept_to_check.rfind("#") else concept_to_check
        # Define the SPARQL query to check if the concept exists
        query = f"""
            SELECT ?s
            WHERE {{
                ?s rdfs:label "{term}"@en.
            }}
        """

        # Set the query and request format
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)

        # Execute the SPARQL query
        results = self.sparql.query().convert()

        # Check if any results were returned
        res = self.found[0] if len(results["results"]["bindings"]) > 0 else self.found[1]
        res.append(term)



    # for term in [s for s in data_graph.subjects(predicate=RDF.type,object=OWL.Class) if  not isinstance(s,BNode)]:
    #     searchForDBPedia(term)

    # print("Summary")
    # print("=====")
    # print(f"Total elements scanned {len(found[0])+len(found[1])}")
    # print("\n")
    # print(f"Found concepts:{len(found[0])} in DBPedia")
    # for t in found[0]:
    #     print(f"The concept '{t}' exists in DBpedia.")

    # print("\n")
    # print(f"Found concepts:{len(found[1])} in DBPedia")
    # for t in found[1]:
    #     print(f"The concept '{t}' does not exists in DBpedia.")