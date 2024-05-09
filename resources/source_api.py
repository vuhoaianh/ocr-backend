import os
import json
from flask import Response, request, jsonify, make_response, session
from flask_restful import Resource
from pymongo import MongoClient

from src.utils import convert_pdf2images, convert_image_to_base64, ocr_table
from PIL import Image
import cv2
import numpy as np
import uuid
from src.utils import seperate_image, ocr_text
from src.init_models import cccd_ocr, ocr_template
from src.table2excel import table2excel
from src.autofill import autofill


class PreprocessApi(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        if file.mimetype!='application/pdf':
            return make_response("Upload file format is not correct", 400)
        response = file.read()
        image_metadata = convert_pdf2images(response)
        return make_response(image_metadata, 200)
        
class OCRApi(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        # if file.mimetype != 'image/jpg':
        #     return make_response("Upload file format is not correct", 400)
        response = file.read()
        img = cv2.imdecode(np.fromstring(response, np.uint8), cv2.IMREAD_COLOR)
        results = seperate_image(img)
        text_metadata = ocr_text(results['image'], results['texts'])
        tables_metadata = []
        if len(results['tables']) != 0:
            for table in results['tables']:
                base64_table = convert_image_to_base64(Image.fromarray(table['image']))
                id = uuid.uuid1()
                table_data = ocr_table(table)
                tables_metadata.append({'table_id': id, 'table_coordinate': table['table_coordinate'],
                                         'table_image': base64_table, 'table_data': table_data})
        return make_response({'metadata': {'text_metadata': text_metadata, 'table_metadata': tables_metadata}}, 200)


class OcrCccdApi(Resource):
    def get(self):
        # Retrieve user_id from session
        user_id = session.get('username')
        return {'user_id': user_id}, 200
    # def post(self):
    #     username = session.get('user_id')
    #     # if 'file' not in request.files:
    #     #     return make_response("No file part", 400)
    #     # file = request.files['file']
    #     # if file.filename == '':
    #     #     return make_response("No selected file", 400)
    #     # # if file.mimetype!='image/jpeg':
    #     # #     return make_response("Upload file format is not correct", 400)
    #     # response = file.read()
    #     # img = cv2.imdecode(np.fromstring(response, np.uint8), cv2.IMREAD_COLOR)
    #     # ocr_data = cccd_ocr.ocr_process(img, user_id=username)
    #     test = {"username": username}
    #     return make_response(test, 200)


class SessionResource(Resource):
    def get(self):
        # Retrieve user_id from session
        user_id = session.get('username')
        # app.logger.info('GET Request: Session data - %s', session)
        # app.logger.info('GET Request: User ID - %s', user_id)
        return {'user_id': session}, 200

    def post(self):
        # Set user_id in session
        data = request.get_json()
        user_id = data.get('user_id')
        session['user_id'] = user_id
        # app.logger.info('POST Request: Session data - %s', session)
        # app.logger.info('POST Request: User ID - %s', user_id)
        return {'message': 'Session updated'}, 200

class OcrTemplateApi(Resource):
    def post(self):
        username = str(session.get('username'))
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        # if file.mimetype!='image/jpeg':
        #     return make_response("Upload file format is not correct", 400)
        if 'template_id' not in request.form:
            return make_response("Name parameter missing", 400)
        response = file.read()
        template_id = request.form['template_id']
        img = cv2.imdecode(np.fromstring(response, np.uint8), cv2.IMREAD_COLOR)
        ocr_data = ocr_template.process_template(img, template_id=template_id)
        return make_response(ocr_data, 200)


class OcrCustomConfigApi(Resource):
    def post(self):
        username = str(session.get('username'))
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        # if file.mimetype!='image/jpeg':
        #     return make_response("Upload file format is not correct", 400)
        response = file.read()
        img = cv2.imdecode(np.fromstring(response, np.uint8), cv2.IMREAD_COLOR)
        ocr_data = ocr_template.process_native(img)
        return make_response(ocr_data, 200)


class SaveTableAPI(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if 'filename' not in request.form:
            return make_response("Name parameter missing", 400)
        response = json.load(file)
        filename = request.form['filename']
        table2excel(response, filename=filename)


class AutoFillAPI(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)

        file = request.files['file']
        if 'name' not in request.form:
            return make_response("Name parameter missing", 400)

        name = request.form['name']
        response = file.read()
        filled_data = autofill(response, name)
        return filled_data


def up_keys_to_db():
    client = MongoClient('localhost', 27017)
    db = client[os.getenv('DB_KEY')]
    collection = db[os.getenv('COLL_KEY')]
    try:
        # Get the text from the form submission
        text = request.form.get('text')
        keys = text.split(',')
        keys = [i.strip() for i in keys]
        temp = {'id': '', 'name': 'Customer config', 'line': keys}
        # Check if text is provided
        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # Insert text into MongoDB
        text_id = collection.insert_one(temp).inserted_id

        return jsonify({'message': 'Text uploaded successfully', 'text_id': str(text_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

