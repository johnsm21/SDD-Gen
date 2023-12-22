from rdflib.plugins.stores import sparqlstore
from rdflib import BNode

def init():
    global ontoInProgress
    ontoInProgress = {}

    global loadedOntos
    loadedOntos = {};

# RDFlib doesn't support bnodes by defualt so we use some basic code to name
# the bnodes
def my_bnode_ext(node):
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node
    return sparqlstore._node_to_sparql(node)
## glove_path = 'data/stanford/glove/common-crawl-840B-300d/glove.840B.300d.txt' ## 5 mins to loaded
## glove_path = 'data/stanford/glove/wikipedia2014-gigaword5/glove.6B.300d.txt' ## 40 seconds

import configparser
config = configparser.ConfigParser()
config.read('config.ini')


glove_path = config.get('glove', 'glove_path') # config._sections.glove.glove_path
loadedOntos_path = config.get('glove', 'onto_path')

# Transformer settings
model_path = config.get('transformer', 'model_path')  # config._sections.transformer.model_path
max_sent_length = config.getint('transformer', 'max_sent_length')


ts_base_url = config.get('fuseki', 'url') # config._sections.blazegraph.ts_base_url #"http://localhost:9999" #'http://host.docker.internal:9999' # "http://localhost:9999"
store = sparqlstore.SPARQLUpdateStore(node_to_sparql=my_bnode_ext)
store.open((ts_base_url + '/ds/query', ts_base_url + '/ds/update'))

httpsOn = config.getboolean('sddgen', 'enableHTTPS')
