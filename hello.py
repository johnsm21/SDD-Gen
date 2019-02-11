from flask import Flask
app = Flask(__name__)

import sys
# sys.path.append('/Users/mjohnson/Projects/TWC-NHANES/lib/camr/')
sys.path.append('lib/camr/')

import amr_parsing
import os

@app.route("/")
def hello():
    textfile_dir = "temp/"
    textfile = 'textFile.txt'
    model = 'lib/amr-semeval-all.train.basic-abt-brown-verb.m'

    # clean up parsed files
    files = os.listdir(textfile_dir)
    for file in files:
        if file.endswith(".prp") or file.endswith(".tok") or file.endswith(".parse") or file.endswith(".dep") or file.endswith(".parsed"):
            os.remove(os.path.join(textfile_dir, file))

    # run the preprocessor
    sys.argv = ['amr_parsing.py','-m', 'preprocess', textfile_dir + textfile]
    amr_parsing.main()

    # run the parser
    sys.argv = ['amr_parsing.py','-m', 'parse', '--model', model, textfile_dir + textfile]
    amr_parsing.main()

    return "Hello World!"
