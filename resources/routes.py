from .source_api import *



def initialize_routes(api):
    api.add_resource(PreprocessApi, '/api/preprocess')
    api.add_resource(OCRApi, '/api/ocr')
    api.add_resource(OcrCccdApi, '/api/ocr_cccd')
    api.add_resource(OcrTemplateApi, '/api/ocr_temp')
    api.add_resource(SaveTableAPI, '/api/table/save_table')
    api.add_resource(AutoFillAPI, '/api/ocr_temp/autofill')
    api.add_resource(UpKeyToDBApi, '/api/up_key')
    api.add_resource(DisplayDBApi, '/api/db/display')
    api.add_resource(GetDocumentApi, '/api/db/get_document')
    api.add_resource(EditDBApi, '/api/db/edit_document')
    api.add_resource(DeleteDocumentApi, '/api/db/delete_document')