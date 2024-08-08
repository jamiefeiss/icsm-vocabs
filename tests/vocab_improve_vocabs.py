from pathlib import Path
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, SDO, SH, SKOS, XSD
from pyshacl import validate


def _get_vocpub_graph() -> Graph:
    graph = Graph()
    graph.parse(Path(__file__).parent / "vocpub-4.10.ttl")
    return graph

ICSM_IRI = URIRef("https://linked.data.gov.au/org/icsm")
CSDM_WG_IRI = URIRef("https://linked.data.gov.au/org/csdm-pg")

CSDM_AGENT_GRAPH = Graph().parse(data=f"""
PREFIX schema: <{SDO}> 
PREFIX xsd: <{XSD}>

<{CSDM_WG_IRI}>
    a schema:Organization ;
    schema:name "CSDM Project Group" ;
    schema:url "https://icsm-au.github.io/3d-csdm/docs/"^^xsd:anyURI ;
    schema:parentOrganization <{ICSM_IRI}> ;
.

<{ICSM_IRI}>
    a schema:Organization ;
    schema:name "Intergovernmental Committee on Surveying & Mapping" ;
    schema:url "https://icsm.gov.au"^^xsd:anyURI ;
.
""")

for file in Path(Path(__file__).parent.parent.resolve() / "cadastre").glob("**/*.ttl"):
    print(file)
    g = Graph().parse(file)

    conforms, results_graph, results_text = validate(
        data_graph=g,
        shacl_graph=_get_vocpub_graph(),
        allow_warnings=True,
    )

    if not conforms:

        # add standard prefixes
        for cs in g.subjects(RDF.type, SKOS.ConceptScheme):
            g.bind("cs", cs)
            g.bind("", Namespace(str(cs) + "/"))

            # add CS metadata
            for c in g.subjects(RDF.type, SKOS.Concept):
                g.add((cs, SKOS.hasTopConcept, c))
                g.add((c, SKOS.topConceptOf, cs))

                if g.value(c, SKOS.definition) is None:
                    g.add((c, SKOS.definition, Literal("")))

            g.add((cs, SDO.dateCreated, Literal("2022-03-18", datatype=XSD.date)))

            for a in g.subjects(RDF.type, PROV.Activity):
                for dm in g.objects(a, PROV.endedAtTime):
                    g.add((cs, SDO.dateModified, Literal(str(dm).split("T")[0], datatype=XSD.date)))

            g.add((cs, SDO.creator, CSDM_WG_IRI))
            g.add((cs, SDO.publisher, ICSM_IRI))

            for pl in g.objects(cs, SKOS.prefLabel):
                g.add((cs, SKOS.definition, Literal(str(pl), lang="en")))


        # add in CSDM agent info
        g += CSDM_AGENT_GRAPH

        # serialize as longturtle
        # print(g.serialize(format="longturtle"))

        # validate
        conforms, results_graph, results_text = validate(
            data_graph=g,
            shacl_graph=_get_vocpub_graph(),
            allow_warnings=True,
        )

        if not conforms:
            for x in results_graph.subjects(SH.resultSeverity, SH.Violation):
                for s, p, o in results_graph.triples((x, SH.focusNode|SH.resultMessage, None)):
                    print(s, p, o)
            break
        else:
            print(f"Conforms: {conforms}")
            g.serialize(destination=file, format="longturtle")
    else:
        print(f"{file} already valid")

