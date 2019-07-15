from flask import Flask


import sys
sys.path.append('lib/CAMR-Python3/')

import globals
import amr_parsing
import os

from flask import flash, request, redirect, url_for, render_template, jsonify, make_response
from werkzeug.utils import secure_filename

import ontology_pipeline
import helper_function
import view
import sdd_aligner

from rdflib import Graph

import requests
import shutil

from flask_cors import CORS
from sdd_generator import SDD

app = Flask(__name__)
UPLOAD_FOLDER = "temp/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

globals.init()

ALLOWED_EXTENSIONS = set(['owl'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/check-ontology/', methods=['POST'])
def check_ontology():
    req_data = request.get_json()
    print(req_data)

    # create an array of IRIs
    onts = view.getFullyInstalledOntologies()
    ontologies = {}
    for ont in onts:
        ontologies[ont[1]] = ont

    source_urls = req_data['source-urls']
    urls = []
    for url in source_urls:
        d = {}
        d['url'] = url
        if url in ontologies.keys():
            d['ready'] = ontologies[url][3] and ontologies[url][4]
        else:
            d['ready'] = False
        urls.append(d)

    response = {}
    response['source-urls'] = urls
    return jsonify(response)

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

    onts = view.getFullyInstalledOntologies()

    ontologies = []
    for ont in onts:
        print(ont)
        ontDicr = {
            'name': ont[0],
            'iri': ont[1],
            'version': ont[2],
            'amrDone': ont[3],
            'notInProgress': ont[4],
        }
        ontologies.append(ontDicr)
    # ontologies = [
    #     {
    #         'name': 'sio',
    #         'iri': 'http://semanticscience.org/resource/'
    #     },
    #     {
    #         'name': 'foaf',
    #         'iri': 'http://xmlns.com/foaf/0.1/'
    #     }
    # ]
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

    g = Graph()
    found = True
    try:
        g.parse(filename, format="xml")
        os.rename(filename, filename.replace(".owl", ".xml"))
        filename = filename.replace(".owl", ".xml")
    except:
        print("not xml")
        try:
            g.parse(filename, format="ttl")
            os.rename(filename, filename.replace(".owl", ".ttl"))
            filename = filename.replace(".owl", ".ttl")
        except:
            print("not ttl")
            try:
                g.parse(filename, format="n3")
                os.rename(filename, filename.replace(".owl", ".n3"))
                filename = filename.replace(".owl", ".n3")
            except:
                print("not n3")
                try:
                    g.parse(filename, format="ntriples")
                    os.rename(filename, filename.replace(".owl", ".nt"))
                    filename = filename.replace(".owl", ".nt")
                except:
                    found = False
                    print("not ntriples")
    print("graph length = " + str(len(g)))


    return [filename, found]

def download_rdf(filename, url):
    g = Graph()
    g.parse(url)
    return g.serialize(destination=filename, format="pretty-xml")

@app.route('/load-ontology', methods=['POST']) #GET requests will be blocked
def load_ontology():
    req_data = request.get_json()
    source_urls = req_data['source-urls']

    ontoIndex = 0
    urls = []
    for url in source_urls:
        print(url)
        # response = requests.get(url)
        # print(response.text)
        [file, work] = download_file_plus(UPLOAD_FOLDER + str(ontoIndex) + ".owl", url)

        if work:
            print("Ingesting " + url)
            ontology_pipeline.ingest(file)

        d = {}
        d['url'] = url
        d['ready'] = work
        urls.append(d)
        # download_rdf(UPLOAD_FOLDER + str(ontoIndex) + ".owl", url)
        ontoIndex = ontoIndex + 1

    response = {}
    response['source-urls'] = urls
    return jsonify(response)


@app.route('/populate-sdd', methods=['POST'])
def populate_sdd():

    # Parse Input
    req_data = request.get_json()
    if 'N' not in req_data:
        print('Bad Request: N must be defined')
        return make_response(jsonify({'Bad Request': 'N must be defined'}), 400)

    if 'data-dictionary' not in req_data:
        print('Bad Request: data-dictionary must be defined')
        return make_response(jsonify({'Bad Request': 'data-dictionary must be defined'}), 400)

    if 'source-urls' not in req_data:
        print('Bad Request: data-dictionary source-urls must be defined')
        return make_response(jsonify({'Bad Request': 'data-dictionary source-urls must be defined'}), 400)

    numResults = req_data['N']
    dataDict = req_data['data-dictionary']
    ontologies = req_data['source-urls']

    if type(numResults) is not int:
        print('Bad Request: N must be an int')
        return make_response(jsonify({'Bad Request': 'N must be an int'}), 400)

    if numResults < 1:
        print('Bad Request: N must be greater than 0')
        return make_response(jsonify({'Bad Request': 'N must be greater than 0'}), 400)

    if type(dataDict) is not list:
        print('Bad Request: data-dictionary must be a list of dictionaries')
        return make_response(jsonify({'Bad Request': 'data-dictionary must be a list of dictionaries'}), 400)

    if len(dataDict) == 0:
        print('Bad Request: data-dictionary must not be empty')
        return make_response(jsonify({'Bad Request': 'data-dictionary must not be empty'}), 400)

    for i in dataDict:
        if type(i) is not dict:
            print('Bad Request: data-dictionary must contain dictionaries')
            return make_response(jsonify({'Bad Request': 'data-dictionary must contain dictionaries'}), 400)

        if 'column' not in i:
            print('Bad Request: data-dictionary dictionaries must contain a column name')
            return make_response(jsonify({'Bad Request': 'data-dictionary dictionaries must contain a column name'}), 400)

        if type(i['column']) is not str:
            print('Bad Request: data-dictionary dictionaries column name must be a string')
            return make_response(jsonify({'Bad Request': 'data-dictionary dictionaries column name must be a string'}), 400)

        if 'description' not in i:
            print('Bad Request: data-dictionary dictionaries must contain a column description')
            return make_response(jsonify({'Bad Request': 'data-dictionary dictionaries must contain a column description'}), 400)

        if type(i['description']) is not str:
            print('Bad Request: data-dictionary dictionaries column description must be a string')
            return make_response(jsonify({'Bad Request': 'data-dictionary dictionaries column description must be a string'}), 400)


    if type(ontologies) is not list:
        print('Bad Request: ontologies must be a list of ontologies')
        return make_response(jsonify({'Bad Request': 'ontologies must be a list of ontologies'}), 400)

    if len(ontologies) == 0:
        print('Bad Request: ontologies must be not be empty')
        return make_response(jsonify({'Bad Request': 'ontologies must be not be empty'}), 400)

    for i in ontologies:
        if type(i) is not str:
            print('Bad Request: ontologies must contain strings')
            return make_response(jsonify({'Bad Request': 'ontologies must contain strings'}), 400)


    graphNames = []
    onts = view.getFullyInstalledOntologies()
    for ont in onts:
        if ont[3] and ont[4]: # check if its installed
            if ont[1] in ontologies: # check if we need it
                graphNames.append(ont[5])

    if len(graphNames) != len(ontologies):
        print('Bad Request: missing ontology')
        return make_response(jsonify({'Bad Request': 'missing ontology'}), 400)

    results = SDD(ontologies, sioLabels = True)
    results = sdd_aligner.labelMatch(results, numResults, dataDict, graphNames)
    print(results.sdd)

    urls = []
    response = {}
    response['source-urls'] = urls
    return jsonify(response)

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

@app.route('/get-sdd/', methods=['GET','POST'])
def get_sdd():
    chearid = {}
    chearid['column'] = 'CHEARPID'
    chearid['attribute'] = helper_function.calcStars([{"value": "hasco:originalID", "confidence": 0.9}, {"value": "sio:Number", "confidence": 0.7}, {"value": "chear:Weight", "confidence": 0.25}])
    chearid['attributeOf'] = helper_function.calcStars([{"value": '??mother', "confidence": 0.85}, {"value": '??child', "confidence": 0.85}, {"value": '??birth', "confidence": 0.5}])



    age = {}
    age['column'] = 'age'
    age['attribute'] = helper_function.calcStars([{"value": "sio:Age", "confidence": 0.95}, {"value": "sio:Number", "confidence": 0.6}, {"value": "chear:Birth", "confidence": 0.2}])
    age['attributeOf'] = helper_function.calcStars([{"value": '??mother', "confidence": 0.85}, {"value": '??child', "confidence": 0.85}, {"value": '??birth', "confidence": 0.5}])
    columns = [chearid, age]


    prepregnancy = {}
    prepregnancy['column'] = '??prepregnancy'
    prepregnancy['entity'] = helper_function.calcStars([{"value": "chear:PrePregnancy", "confidence": 0.8}, {"value": "chear:Pregnancy", "confidence": 0.7}, {"value": "chear:Birth", "confidence": 0.6}])

    head = {}
    head['column'] = '??head'
    head['entity'] = helper_function.calcStars([{"value": "uberon:0000033", "confidence": 1.0}, {"value": "chear:Pregnancy", "confidence": 0.2}, {"value": "chear:Weight", "confidence": 0.1}])
    head['relation'] = helper_function.calcStars([{"value": "sio:isPartOf", "confidence": 0.7}, {"value": "sio:isProperPartOf", "confidence": 0.7}, {"value": "sio:isLocatedIn", "confidence": 0.5}])
    virtual_columns = [prepregnancy, head]

    sheet = {}
    sheet['columns'] = columns
    sheet['virtual-columns'] = virtual_columns

    sdd = {}
    sdd['Dictionary Mapping'] = sheet

    response = {}
    response['N'] = 3
    response['sdd'] = sdd

    return jsonify(response)
