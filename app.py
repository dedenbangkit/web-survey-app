from flask import Flask, jsonify, render_template
import pandas as pd
import requests as r
import xmltodict
import json

app = Flask(__name__)
instance_list = './data/flow-survey-amazon-aws.csv'

@app.route('/')
def index():
    instances = pd.read_csv(instance_list)
    instances = instances.to_dict("records")
    return jsonify(instances)
    return render_template('index.html', instances=instances)

@app.route('/<instance>/<surveyId>')
def survey(instance,surveyId):
    instances = pd.read_csv(instance_list)
    endpoint = list(instances[instances['instances'] == instance]['names'])[0]
    survey = r.get(endpoint+surveyId+'.xml')
    survey.encoding = survey.apparent_encoding
    survey = survey.text
    survey = xmltodict.parse(survey,attr_prefix='',cdata_key='text')
    survey = json.loads(json.dumps(survey).replace('"true"','true').replace('"false"','false'))
    response = survey['survey']
    return jsonify(response)


if __name__=='__main__':
    app.config.update(DEBUG=True)
    app.run()



