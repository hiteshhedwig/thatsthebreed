from fastai2.vision.all import *  
import yaml
import sys
from io import BytesIO
from typing import List, Dict, Union, ByteString, Any
import os
import flask
from flask import Flask
import requests
import torch
import json
from PIL import Image
import numpy

with open("src/config.yaml", 'r') as stream:
    APP_CONFIG = yaml.full_load(stream)

app = Flask(__name__)


def load_model(path_m):
    #path_m= '/home/username/10_WEbapp/thatsthebreed/models'
    model_name="final.pth"
    learn = load_learner(os.path.join(path_m, model_name))
    return learn


def load_image_url(url: str) -> Image:
    response = requests.get(url)
    img_url = numpy.asarray(Image.open(BytesIO(response.content)))
    img= PILImage(PILImage.create(img_url).resize((224,224)))
    return img


def load_image_bytes(raw_bytes: ByteString) -> Image:
 
    img_byt = numpy.asarray(Image.open(BytesIO(raw_bytes)).convert('RGB'))
    img= PILImage(PILImage.create(img_byt).resize((224,224)))
    return img


def predict(img, n: int = 3) -> Dict[str, Union[str, List]]:
    pred_class, pred_idx, outputs = model.predict(img)
    pred_probs = outputs / sum(outputs)
    pred_probs = pred_probs.tolist()
    print(pred_probs[pred_idx])
    predictions = [{"class":pred_class,"output": outputs.tolist()[pred_idx], "prob": pred_probs[pred_idx] }]
    '''
    for image_class, output, prob in zip(model.data.classes, outputs.tolist(), pred_probs):
        output = round(output, 1)
        prob = round(prob, 2)
        predictions.append(
            {"class": image_class.replace("_", " "), "output": output, "prob": prob}
        )
    '''
    #predictions = sorted(predictions, key=lambda x: x["output"], reverse=True)
    #predictions = predictions[0:n]
    return {"class": str(pred_class), "predictions": predictions}


@app.route('/api/classify', methods=['POST', 'GET'])
def upload_file():
    if flask.request.method == 'GET':
        url = flask.request.args.get("url")
        img = load_image_url(url)
    else:
        bytes = flask.request.files['file'].read()
        img = load_image_bytes(bytes)
    res = predict(img)
    return flask.jsonify(res)


@app.route('/api/classes', methods=['GET'])
def classes():
    classes = sorted(model.data.classes)
    return flask.jsonify(classes)


@app.route('/ping', methods=['GET'])
def ping():
    return "pong"


@app.route('/config')
def config():
    return flask.jsonify(APP_CONFIG)


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    response.cache_control.max_age = 0
    return response


@app.route('/<path:path>')
def static_file(path):
    if ".js" in path or ".css" in path:
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')


@app.route('/')
def root():
    return app.send_static_file('index.html')


def before_request():
    app.jinja_env.cache = {}


model = load_model('models')

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)

    if "prepare" not in sys.argv:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=False, host='0.0.0.0', port=port)
        # app.run(host='0.0.0.0', port=port)
