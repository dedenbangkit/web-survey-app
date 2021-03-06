from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from lxml import etree
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import pandas as pd
import requests as r
import sqlite3
import xmltodict
import json
import os

app = Flask(__name__)
CORS(app)
instance_list = './data/flow-survey-amazon-aws.csv'

def readxml(xmlpath):
    with open(xmlpath) as survey:
        encoding = etree.parse(survey)
        encoding = encoding.docinfo.encoding
    with open(xmlpath) as survey:
        survey = xmltodict.parse(survey.read(),encoding=encoding,attr_prefix='',cdata_key='text')
        survey = json.loads(json.dumps(survey).replace('"true"','true').replace('"false"','false'))
        response = survey['survey']
    return response

@app.route('/')
def index():
    instances = pd.read_csv(instance_list)
    instances = instances.to_dict("records")
    return render_template('index.html', instances=instances)

@app.route('/<instance>/<surveyId>/<lang>')
def survey(instance,surveyId,lang):
    ziploc = './static/xml/'+ instance
    if not os.path.exists(ziploc):
        instances = pd.read_csv(instance_list)
        endpoint = list(instances[instances['instances'] == instance]['names'])[0]
        zipurl = r.get(endpoint+surveyId+'.zip', allow_redirects=True)
        print(zipurl)
        z = ZipFile(BytesIO(zipurl.content))
        z.extractall(ziploc)
    response = readxml(ziploc + '/' +surveyId + '.xml')
    if not os.path.exists(ziploc):
        cascadeList = []
        for groups in response["questionGroup"]:
            for q in groups["question"]:
                if q["type"] == "cascade":
                    cascadeList.append(endpoint + q["cascadeResource"] + ".zip")
        for cascade in cascadeList:
            zipurl = r.get(cascade, allow_redirects=True)
            z = ZipFile(BytesIO(zipurl.content))
            z.extractall(ziploc)
    ### Dropdown
    #instances = pd.read_csv(instance_list)
    #instances = instances.to_dict("records")
    ## Current Endpoint
    ## url = '/'+instance+'/'+surveyId+'/'+lang
    ## return render_template('survey.html', data=response, instances=instances, url=url, lang=lang)
    return jsonify(response)

@app.route('/cascade/<instance>/<sqlite>/<lv>')
def cascade(instance,sqlite,lv):
    casloc = './static/xml/'+ instance +'/'+ sqlite
    conn = sqlite3.connect(casloc)
    table = pd.read_sql_query("SELECT * FROM nodes;", conn)
    result = table[table['parent'] == int(lv)].sort_values(by="name").to_dict('records')
    return jsonify(result)

@app.route('/submit-form', methods=['POST'])
def submit():
    rec = request.get_json()
    questionId = rec['questionId'].split(',')
    answerType = rec['answerType'].split(',')
    data = []
    form = {
        "questionId": -1,
        "answerType": "META_NAME",
        "value": rec['_dataPointName'],
        "iteration": 0
    }
    data.append(form)
    for i, ids in enumerate(questionId):
        try:
            if answerType[i] == "OPTION":
                val = [{"text":rec[ids]}]
            else:
                val = rec[ids]
            form = {
                "questionId": ids,
                "answerType": answerType[i],
                "value": val,
                "iteration": 0
            }
            data.append(form)
        except:
            pass
    startdate = datetime.fromtimestamp(int(rec["_submissionStart"])/1000)
    enddate = datetime.fromtimestamp(int(rec["_submissionStop"])/1000)
    duration = enddate - startdate
    duration = round(duration.total_seconds())
    results = {
        "dataPointId": rec['_dataPointId'],
        "deviceId": rec['_deviceId'],
        "duration": duration,
        "formId": rec['_formId'],
        "formVersion": rec['_version'],
        "responses": data,
        "submissionDate": rec['_submissionStop'],
        "username": "Deden Akvo",
        "uuid": rec['_uuid']
    }
    with open('data.json','w') as f:
        json.dump(results, f)
    zip_name = rec['_uuid'] + '.zip'
    zip_file = ZipFile(zip_name, 'w')
    zip_file.write('data.json', compress_type=ZIP_DEFLATED)
    zip_file.close()
    if os.path.isfile('data.json'):
        os.remove('data.json')
    if not os.path.exists('./tmp'):
        os.mkdir('./tmp')
    os.rename(zip_name, './tmp/' + zip_name)
    #foldername = './tmp/' + rec['_uuid']
    #filename = foldername + '/data.json'
    #if not os.path.exists(foldername):
    #    os.mkdir(foldername)
    #with open(foldername + '/data.json','w') as f:
    #    json.dump(results, f)
    #zip_file = ZipFile(foldername + '.zip', 'w')
    #zip_file.write(foldername + '/data.json', compress_type=ZIP_DEFLATED)
    #zip_file.close()
    #if os.path.isfile(filename):
    #    os.remove(filename)
    #if os.path.exists(foldername):
    #    os.rmdir(foldername)
    return jsonify(results)

if __name__=='__main__':
    app.config.update(
            DEBUG=True,
            TEMPLATES_AUTO_RELOAD=True
    )
    app.run()
