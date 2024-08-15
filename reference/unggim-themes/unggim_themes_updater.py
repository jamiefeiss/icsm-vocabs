from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, SDO, SKOS, XSD

# preprocess data-themes my moving all newline-broken strings to single-line strings
g = Graph().parse("data-themes.orig.ttl")

# add VocPub metadata to the ConceptScheme
CS = None
for cs in g.subjects(RDF.type, SKOS.ConceptScheme):
    CS = cs

title = g.value(CS, DCTERMS.title)
g.remove((CS, DCTERMS.title, None))
g.add((CS, SKOS.prefLabel, title))

description = g.value(CS, DC.description)
g.remove((CS, DC.description, None))
g.add((CS, SKOS.definition, description))

modified = g.value(CS, DCTERMS.modified)
g.remove((CS, DCTERMS.modified, None))
g.add((CS, SDO.dateCreated, modified))

g.add((CS, SDO.dateModified, Literal("2021-04-27", datatype=XSD.date)))  # from the GitHub repo last commit

history_note = (
        "This vocabulary is a slightly reformatted version of the original obtained" +
        "from https://linkeddataops.adaptcentre.ie/vocabularies/unggim-data-themes.\n\n" +
        "The only changes have been to remove the top-level 'Data Theme' Concept and to add ConceptScheme and Concept"
        "elements required for the VocPub profile of SKOS "
        "(https://w3id.org/profile/vocpub/spec)"
)
g.add((CS, SKOS.historyNote, Literal(history_note)))
g.add((
    CS,
    SDO.citation,
    Literal("https://linkeddataops.adaptcentre.ie/vocabularies/unggim-data-themes", datatype=XSD.anyURI)
))

g.add((CS, SDO.license, URIRef("http://purl.org/NET/rdflicense/cc-by4.0")))

# creator
g.parse(data=f"""
PREFIX schema: <{SDO}>
PREFIX xsd: <{XSD}>

<https://orcid.org/0000-0003-2130-0312>
    a schema:Person ;
    schema:name "Beyza Yaman" ;
    schema:email "beyza.yaman@adaptcentre.ie"^^xsd:anyURI ;
    schema:url "https://dblp.org/pers/y/Yaman:Beyza.html" ;
.

<{CS}> schema:creator <https://orcid.org/0000-0003-2130-0312> .
""")
for t in g.triples((CS, DCTERMS.creator, None)):
    g.remove(t)
for s in g.subjects(FOAF.homepage, URIRef("https://dblp.org/pers/y/Yaman:Beyza.html")):
    for t in g.triples((s, None, None)):
        g.remove(t)

# publisher
g.parse(data=f"""
PREFIX schema: <{SDO}>
PREFIX xsd: <{XSD}>

<https://www.adaptcentre.ie>
    a schema:Organization ;
    schema:name "ADAPT, the world-leading SFI Research Centre for AI-Driven Digital Content Technology" ;
    schema:url "https://www.adaptcentre.ie"^^xsd:anyURI ;
.

<{CS}> schema:publisher <https://www.adaptcentre.ie> .
""")


for t in g.triples((URIRef(CS + "DataTheme"), None, None)):
    g.remove(t)

# update each Concept
for concept in g.subjects(RDF.type, SKOS.Concept):
    if (concept, SKOS.broader, URIRef(str(CS) + "DataTheme")) in g:
        g.remove((concept, SKOS.broader, URIRef(str(CS) + "DataTheme")))
    g.add((concept, SKOS.inScheme, CS))

    for note in g.objects(concept, SKOS.note):
        g.remove((concept, SKOS.note, note))
        g.add((concept, SKOS.definition, note))

    if not g.value(concept, SKOS.broader, None):
        g.add((concept, SKOS.topConceptOf, CS))
        g.add((CS, SKOS.hasTopConcept, concept))


# add in FSDF matches
g.parse(data=f"""
PREFIX : <https://linkeddataops.adaptcentre.ie/vocabularies/unggim-data-themes#>
PREFIX fsdf: <https://linked.data.gov.au/def/fsdf/themes/>
PREFIX skos: <{SKOS}>

:Addresses 
    skos:exactMatch fsdf:geocoded-addressing ;
    skos:altLabel "Geocoded Addressing" ;
.

:Buildings-Settlements
    skos:exactMatch fsdf:buildings-and-settlements ;
.

:Elevation-Depth
    skos:exactMatch fsdf:elevation-and-depth ;
.

:FunctionalAreas
    skos:exactMatch fsdf:administrative-boundaries ;
    skos:altLabel "Administrative Boundaries" ;
.

:GeographicalNames 
    skos:exactMatch fsdf:place-names ;
    skos:altLabel "Place Names" ;
.

:GCRF
    skos:exactMatch fsdf:positioning ;
.

:LandCover-LandUse
    skos:exactMatch fsdf:land-cover-and-land-use ;
.

:LandParcels
    skos:exactMatch fsdf:land-parcel-and-property ;
    skos:altLabel "Place Names" ;
.

:Orthoimagery 
    skos:exactMatch fsdf:imagery ;
    skos:altLabel "Imagery" ;
.

:TransportNetworks 
    skos:exactMatch fsdf:transport ;
    skos:altLabel "Transport" ;
.
""")


g.bind("cs", CS, override=True)
g.serialize(destination="../../unggim-themes.ttl", format="longturtle")
