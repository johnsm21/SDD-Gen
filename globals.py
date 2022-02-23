def init():
    global ontoInProgress
    ontoInProgress = {}

## glove_path = 'data/stanford/glove/common-crawl-840B-300d/glove.840B.300d.txt' ## 5 mins to loaded
## glove_path = 'data/stanford/glove/wikipedia2014-gigaword5/glove.6B.300d.txt' ## 40 seconds

import configparser
config = configparser.ConfigParser()
config.read('config.ini')


glove_path = config.get('glove', 'glove_path') # config._sections.glove.glove_path

# Transformer settings
model_path = config.get('transformer', 'model_path')  # config._sections.transformer.model_path
max_sent_length = config.getint('transformer', 'max_sent_length')
print(max_sent_length);

ts_base_url = config.get('blazegraph', 'ts_base_url') # config._sections.blazegraph.ts_base_url #"http://localhost:9999" #'http://host.docker.internal:9999' # "http://localhost:9999"
# heads = 1        # must be a multiple of the word vector dimension
# N = 1
