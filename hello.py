from flask import Flask
app = Flask(__name__)

import sys
sys.path.append('lib/camr/')

import amr_parsing
import os

from flask import flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

import ontology_pipeline

from rdflib import Graph

import requests
import shutil

UPLOAD_FOLDER = "temp/"
ALLOWED_EXTENSIONS = set(['owl'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/', methods=['GET', 'POST'])
def upload_file():
    head = {'upload': 'true'}
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            print("filename = " + UPLOAD_FOLDER + filename)
            ontology_pipeline.ingest(UPLOAD_FOLDER + filename)

            return redirect(url_for('upload_file',
                                    filename=filename))
    return render_template('upload.html', head=head)
    # return '''
    # <!doctype html>
    # <title>Upload Ontology</title>
    # <h1>Upload New Ontology</h1>
    # <form method=post enctype=multipart/form-data>
    #   <input type=file name=file>
    #   <input type=submit value=Upload>
    # </form>
    # '''

@app.route('/ontologies/')
def index():
    head = {'ontologies': 'true'}

    ontologies = [
        {
            'name': 'sio',
            'iri': 'http://semanticscience.org/resource/'
        },
        {
            'name': 'foaf',
            'iri': 'http://xmlns.com/foaf/0.1/'
        }
    ]
    return render_template('ontologies.html', head=head, ontologies=ontologies)

def temp():
    stext = sys.argv[1]
    rtext = sys.argv[2]
    input = sys.stdin
    output = sys.stdout
    if nargs > 3:
        input = open(sys.argv[3])
    if nargs > 4:
        output = open(sys.argv[4], 'w')
    for s in input.xreadlines(  ):
        output.write(s.replace(stext, rtext))
    output.close(  )
    input.close(  )

def download_file(filename, url):
    r = requests.get(url, stream=True)
    file = open(filename, "w")
    file.write(r.text)
    file.close()
    return filename

def download_file_plus(filename, url):
    r = requests.get(url, stream=True)
    file = open(filename, "w")
    file.write(r.text)
    file.close()

    print(filename)

    g = Graph()
    try:
        g.parse(filename, format="xml")
    except:
        print("not xml")
        try:
            g.parse(filename, format="ttl")
            os.rename(filename, filename.replace(".owl", ".ttl"))
        except:
            print("not ttl")
            try:
                g.parse(filename, format="n3")
                os.rename(filename, filename.replace(".owl", ".n3"))
            except:
                print("not n3")
                try:
                    g.parse(filename, format="ntriples")
                except:
                    print("not ntriples")
    print("graph length = " + str(len(g)))


    return filename

def download_rdf(filename, url):
    g = Graph()
    g.parse(url)
    return g.serialize(destination=filename, format="pretty-xml")

@app.route('/load-ontology', methods=['POST']) #GET requests will be blocked
def load_ontology():
    req_data = request.get_json()
    source_urls = req_data['source-urls']

    ontoIndex = 0
    for url in source_urls:
        print(url)
        # response = requests.get(url)
        # print(response.text)
        download_file_plus(UPLOAD_FOLDER + str(ontoIndex) + ".owl", url)
        # download_rdf(UPLOAD_FOLDER + str(ontoIndex) + ".owl", url)
        ontoIndex = ontoIndex + 1
    return "201"

@app.route('/json-example', methods=['POST']) #GET requests will be blocked
def json_example():
    req_data = request.get_json()

    language = req_data['language']
    framework = req_data['framework']
    python_version = req_data['version_info']['python'] #two keys are needed because of the nested object
    example = req_data['examples'][0] #an index is needed because of the array
    boolean_test = req_data['boolean_test']

    return '''
           The language value is: {}
           The framework value is: {}
           The Python version is: {}
           The item at index 0 in the example list is: {}
           The boolean value is: {}'''.format(language, framework, python_version, example, boolean_test)



@app.route("/")
def hello():
    # ontology_pipeline.ingest("temp/sio.owl")

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
    # amr_parsing.main()

    # run the parser
    sys.argv = ['amr_parsing.py','-m', 'parse', '--model', model, textfile_dir + textfile]
    # amr_parsing.main()

    head = {'home': 'true'}
    message = {'content': 'Hello World!'}

    return render_template('home.html', head=head, message=message)
