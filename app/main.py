from flask import Flask

import sys
import globals
import os
import glove

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

import datetime
import json

import torch

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--cert_name', type=ascii, default='', help='the filename of the pks12 certificate')
parser.add_argument('--cert_pass', type=ascii, default='', help='the password to the pks12 certificate')
args = vars(parser.parse_args())


import tempfile
from cryptography.hazmat.primitives import serialization
import cryptography.hazmat.primitives.serialization.pkcs12


app = Flask(__name__)
UPLOAD_FOLDER = "temp/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

globals.init()

CORS(app)


ALLOWED_EXTENSIONS = set(['owl', 'ttl', 'rdf'])

algorithms = ['string-dist']

print("Loading Glove Vectors...")
gloveMap, word2Id, weights = glove.loadGlove(globals.glove_path)


print("Intialize Transformer Network...")
model = torch.load(globals.model_path)
model.eval()

print("Server Ready!")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/ping/', methods=['POST'])
def ping():
    response = {}
    response['on'] = True
    return jsonify(response)

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

def checkDDRequest(req_data):
    if 'N' not in req_data:
        print('Bad Request: N must be defined')
        return 'N must be defined'

    if 'data-dictionary' not in req_data:
        print('Bad Request: data-dictionary must be defined')
        return 'data-dictionary must be defined'

    if 'source-urls' not in req_data:
        print('Bad Request: data-dictionary source-urls must be defined')
        return 'data-dictionary source-urls must be defined'

    numResults = req_data['N']
    dataDict = req_data['data-dictionary']
    ontologies = req_data['source-urls']

    if type(numResults) is not int:
        print('Bad Request: N must be an int')
        return 'N must be an int'

    if numResults < 1:
        print('Bad Request: N must be greater than 0')
        return 'N must be greater than 0'

    if type(dataDict) is not list:
        print('Bad Request: data-dictionary must be a list of dictionaries')
        return 'data-dictionary must be a list of dictionaries'

    if len(dataDict) == 0:
        print('Bad Request: data-dictionary must not be empty')
        return 'data-dictionary must not be empty'

    for i in dataDict:
        if type(i) is not dict:
            print('Bad Request: data-dictionary must contain dictionaries')
            return 'data-dictionary must contain dictionaries'

        if 'column' not in i:
            print('Bad Request: data-dictionary dictionaries must contain a column name')
            return 'data-dictionary dictionaries must contain a column name'

        if type(i['column']) is not str:
            print('Bad Request: data-dictionary dictionaries column name must be a string')
            return 'data-dictionary dictionaries column name must be a string'

        if 'description' not in i:
            print('Bad Request: data-dictionary dictionaries must contain a column description')
            return 'data-dictionary dictionaries must contain a column description'

        if type(i['description']) is not str:
            print('Bad Request: data-dictionary dictionaries column description must be a string')
            return 'data-dictionary dictionaries column description must be a string'

    if type(ontologies) is not list:
        print('Bad Request: ontologies must be a list of ontologies')
        return 'ontologies must be a list of ontologies'

    if len(ontologies) == 0:
        print('Bad Request: ontologies must be not be empty')
        return 'ontologies must be not be empty'

    for i in ontologies:
        if type(i) is not str:
            print('Bad Request: ontologies must contain strings')
            return 'ontologies must contain strings'

    return (numResults, dataDict, ontologies)


@app.route('/populate-sdd', methods=['POST'])
def populate_sdd():

    # Parse Input
    req_data = request.get_json()

    print(req_data)

    parsed = checkDDRequest(req_data)

    if isinstance(parsed, str):
        return make_response(jsonify({'Bad Request': parsed}), 400)
    else:
        (numResults, dataDict, ontologies) = parsed

    graphNames = []
    onts = view.getFullyInstalledOntologies()

    #print('onts: ' + str(onts))
    # print('ontologies: ' + str(ontologies))

    found = []
    # for ont in onts:
    #     # if ont[3] and ont[4]: # check if its installed
    #     if ont[4]: # Only check for in database
    #         if ont[1] in ontologies: # check if we need it
    #             found.append(ont[1])
    #             graphNames.append(ont[5])

    # Get the SDDGen graph names for the ontologies, these are the ontology iris with versioning info
    for ontIn in ontologies:
        for storedOnt in onts:
            if ontIn == storedOnt[1]: # graph IRI match
                if storedOnt[4]: # Check if installed in database
                    found.append(storedOnt[1])
                    graphNames.append(storedOnt[5])
                break # we found the ontology no need to keep looking

    # print('graphNames = ' + str(graphNames))

    if len(graphNames) != len(ontologies):
        print('Bad Request: missing ontology')

        def Diff(li1, li2):
            return (list(set(li1) - set(li2)))
        missing = Diff(ontologies, found)
        print('missing = ' + str(missing))

        return make_response(jsonify(
        {   'Bad Request': 'missing ontology',
            'Miss': missing
        }), 400)

    results = SDD(ontologies, sioLabels = True)
    results = sdd_aligner.transformerMatchWithOntoPriority(results, numResults, dataDict, graphNames, gloveMap, word2Id, model)
    # results = sdd_aligner.semanticLabelMatchWithOntoPriority(results, numResults, dataDict, graphNames, gloveMap)
    # results = sdd_aligner.semanticLabelMatch(results, numResults, dataDict, graphNames, gloveMap)
    # results = sdd_aligner.labelMatch(results, numResults, dataDict, graphNames)

    print(results.sdd)

    response = {}
    response['sdd'] = results.sdd
    return jsonify(response)

def checkTestRequest(req_data):
    data_path = 'data'
    if 'algorithm' not in req_data:
        return 'Missing algorithm'

    if type(req_data['algorithm']) is not str:
        return 'Algorithm must be a string'

    if 'ground-truth' not in req_data:
        return 'Missing ground truth'

    if type(req_data['ground-truth']) is not str:
        return 'Ground truth must be a path'

    gtPath = data_path + os.path.sep + req_data['ground-truth']
    if not os.path.exists(gtPath):
        return 'Ground truth must be a path to an sdd'

    if req_data['algorithm'] not in algorithms:
        return 'Unkown algorithm'

    tstPath = data_path  + os.path.sep + 'rpi' + os.path.sep + req_data['algorithm'] + '-test' + os.path.sep + datetime.datetime.now().strftime("%Y-%m-%d")

    return (gtPath, tstPath)



@app.route('/test-sdd', methods=['POST'])
def test_sdd():
    test_path = 'data'

    # Parse Input
    req_data = request.get_json()

    # Parse Arguments
    parsed = checkTestRequest(req_data)
    if isinstance(parsed, str):
        return make_response(jsonify({'Bad Request': parsed}), 400)
    else:
        (gtPath, tstPath) = parsed

    parsed = checkDDRequest(req_data)
    if isinstance(parsed, str):
        return make_response(jsonify({'Bad Request': parsed}), 400)
    else:
        (numResults, dataDict, ontologies) = parsed

    graphNames = []
    onts = view.getFullyInstalledOntologies()
    for ont in onts:
        if ont[3] and ont[4]: # check if its installed
            if ont[1] in ontologies: # check if we need it
                graphNames.append(ont[5])

    if len(graphNames) != len(ontologies):
        print('Bad Request: missing ontology')
        return make_response(jsonify({'Bad Request': 'missing ontology'}), 400)

    # Create test folder
    if not os.path.exists(tstPath):
        os.makedirs(tstPath)

    with open(tstPath + os.path.sep + 'request.json', 'w') as outfile:
        json.dump(req_data, outfile, indent=4, sort_keys=True)

    results = SDD(ontologies, sioLabels = True)
    # results = sdd_aligner.labelMatch(results, numResults, dataDict, graphNames)
    results = sdd_aligner.descriptionMatch(results, numResults, dataDict, graphNames)

    errors = results.generateAcc(gtPath)
    if isinstance(errors, str):
        return make_response(jsonify({'Bad Request': errors}), 400)


    with open(tstPath + os.path.sep + 'result.json', 'w') as outfile:
        json.dump(results.sdd, outfile, indent=4, sort_keys=True)

    response = {}
    response['sdd'] = results.sdd
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


if globals.httpsOn :
    if __name__ == "__main__":
        if eval(args['cert_name']): # if cert_name we try to open pks file
            with open('cert/' + eval(args['cert_name']), 'rb') as f:
                (
                    private_key,
                    certificate,
                    additional_certificates,
                ) = serialization.pkcs12.load_key_and_certificates(
                    f.read(), eval(args['cert_pass']).encode()
                )
            # key will be available in user readable temporary file for the time of the
            # program run (until key and cert get gc'ed)
            key = tempfile.NamedTemporaryFile()
            cert = tempfile.NamedTemporaryFile()
            key.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            key.flush()
            cert.write(
                certificate.public_bytes(serialization.Encoding.PEM),
            )
            cert.flush()

            args = None # delete the password
            app.run(host='0.0.0.0', ssl_context=(cert.name, key.name))

        else: # if cert_name not provided we go to adhoc we try to open pks file
            args = None # delete the password
            app.run(host='0.0.0.0', ssl_context='adhoc')
else:
    args = None # delete the password
    app.run(host='0.0.0.0')
