import datetime
import os
import json
import shutil
from flask import Response, request, jsonify, make_response, session
from flask_restful import Resource
from pymongo import MongoClient

from src.utils import convert_pdf2images, convert_image_to_base64, ocr_table
from PIL import Image
import cv2
import numpy as np
import uuid
from src.utils import seperate_image, ocr_text, up_keys_to_db
from src.init_models import cccd_ocr, ocr_template
from src.mongo_db_ultils import display_collection, edit_document, delete_document, get_documents
from src.table2excel import table2excel
from src.autofill import autofill
from src.process_token import access_profile


class PreprocessApi(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        if file.mimetype != 'application/pdf':
            return make_response("Upload file format is not correct", 400)
        response = file.read()
        image_metadata = convert_pdf2images(response)
        return make_response(jsonify(image_metadata), 200)


class OCRApi(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        response = file.read()
        img = cv2.imdecode(np.frombuffer(response, np.uint8), cv2.IMREAD_COLOR)
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
        return make_response(jsonify({'metadata': {'text_metadata': text_metadata, 'table_metadata': tables_metadata}}), 200)


class OcrCccdApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        response = file.read()
        img = cv2.imdecode(np.frombuffer(response, np.uint8), cv2.IMREAD_COLOR)
        ocr_data = cccd_ocr.ocr_process(img, user_id=username)
        return make_response(jsonify(ocr_data), 200)


class OcrTemplateApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        if 'template_id' not in request.form:
            return make_response("Name parameter missing", 400)
        response = file.read()
        template_id = request.form['template_id']
        img = cv2.imdecode(np.frombuffer(response, np.uint8), cv2.IMREAD_COLOR)
        ocr_data = ocr_template.process_template(img, template_id=template_id, user_id=username)
        file_name = 'result_template' + str(datetime.datetime.now().microsecond)
        shutil.copyfile("template.docx", f'static/{file_name}.docx')
        file_url = f'http://localhost:3502/static/{file_name}.docx'  # Assuming the file is accessible via Flask server at this URL
        response_data = {'file_url': file_url}
        return make_response(jsonify(response_data), 200)


class OcrCustomConfigApi(Resource):
    def post(self):
        username = str(session.get('username'))
        if 'file' not in request.files:
            return make_response("No file part", 400)
        file = request.files['file']
        if file.filename == '':
            return make_response("No selected file", 400)
        response = file.read()
        img = cv2.imdecode(np.frombuffer(response, np.uint8), cv2.IMREAD_COLOR)
        ocr_data = ocr_template.process_native(img, user_id=username)
        return make_response(jsonify(ocr_data), 200)


class SaveTableAPI(Resource):
    def post(self):
        if 'file' not in request.files:
            return make_response("No file part", 400)
        
        file = request.files['file']
        
        if 'filename' not in request.form:
            return make_response("Name parameter missing", 400)
        
        filename = request.form['filename']
        
        try:
            response = json.load(file)
            table2excel(response, filename=filename)
            file_name = 'result_table' + str(datetime.datetime.now().microsecond)
            shutil.copyfile(filename, f'static/{file_name}.xlsx')
            file_url = f'http://localhost:3502/static/{file_name}.xlsx'  # Assuming the file is accessible via Flask server at this URL
            response_data = {'file_url': file_url}
            return make_response(response_data, 200)
        except json.JSONDecodeError:
            return make_response("Invalid JSON file", 400)
        except Exception as e:
            return make_response(f"An error occurred: {str(e)}", 500)


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
        return jsonify(filled_data)


class UpKeyToDBApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        
        # Kiểm tra xem 'text' và 'name' có trong form data không
        if 'text' not in request.form or 'name' not in request.form:
            return make_response("text or name parameter missing", 400)
        
        text = request.form['text']
        name = request.form['name']  # Lấy giá trị của 'name'
        
        try:
            up_keys_to_db(user_id=username, text=text, name=name)  # Truyền 'name' vào hàm
            return make_response("Keys updated successfully", 200)
        except Exception as e:
            return make_response(f"An error occurred: {str(e)}", 500)



class DisplayDBApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        if 'db_name' not in request.form:
            return make_response("Name parameter missing", 400)

        db_name = request.form['db_name']
        docs = display_collection(db_name, username)
        return jsonify(docs)


class GetDocumentApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        if 'db_name' not in request.form:
            return make_response("Name parameter missing", 400)
        if 'document_id' not in request.form:
            return make_response("Name parameter missing", 400)
        db_name = request.form['db_name']
        doc_id = request.form['document_id']
        docs = get_documents(db_name, username, doc_id)
        return jsonify(docs)

class EditDBApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        if 'db_name' not in request.form:
            return make_response("db_name parameter missing", 400)
        if 'document_id' not in request.form:
            return make_response("document_id parameter missing", 400)
        if 'file' not in request.files:
            return make_response("No file part", 400)
        
        file = request.files['file']
        db_name = request.form['db_name']
        document_id = request.form['document_id']
        updated_data = file.read().decode('utf-8')  # Read and decode file content

        try:
            success = edit_document(db_name=db_name, user_id=username, updated_data=updated_data, document_id=document_id)
            if success:
                return make_response("Document updated successfully", 200)
            else:
                return make_response("No document found with the given ID or no change in data", 400)
        except ValueError as ve:
            return make_response(str(ve), 400)
        except Exception as e:
            return make_response("An error occurred: " + str(e), 500)

class DeleteDocumentApi(Resource):
    def post(self):
        profile_data = access_profile()
        username = profile_data["userId"]
        
        if 'db_name' not in request.form:
            return make_response("db_name parameter missing", 400)
        
        if 'document_id' not in request.form:
            return make_response("document_id parameter missing", 400)
        
        db_name = request.form['db_name']
        document_id = request.form['document_id']
        
        try:
            success = delete_document(db_name=db_name, user_id=username, document_id=document_id)
            if success:
                return make_response("Document deleted successfully", 200)
            else:
                logging.error(f"Failed to delete document with id: {document_id}")
                return make_response("Document deletion failed", 500)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return make_response(f"An error occurred: {str(e)}", 500)