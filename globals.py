def init():
    global ontoInProgress
    ontoInProgress = {}

## glove_path = 'data/stanford/glove/common-crawl-840B-300d/glove.840B.300d.txt' ## 5 mins to loaded
## glove_path = 'data/stanford/glove/wikipedia2014-gigaword5/glove.6B.300d.txt' ## 40 seconds

glove_path = 'data/stanford/glove/wikipedia2014-gigaword5/glove.6B.50d.txt'

# Transformer settings
model_path = 'data/models/1000ep.pt'
max_sent_length = 15
# heads = 1        # must be a multiple of the word vector dimension
# N = 1
