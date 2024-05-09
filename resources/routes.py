from .source_api import PreprocessApi, OCRApi, OcrCccdApi, SaveTableAPI, AutoFillAPI, OcrTemplateApi, SessionResource


def initialize_routes(api):
    api.add_resource(PreprocessApi, '/api/preprocess')
    api.add_resource(OCRApi, '/api/ocr')
    api.add_resource(OcrCccdApi, '/api/ocr_cccd')
    api.add_resource(OcrTemplateApi, '/api/ocr_temp')
    api.add_resource(SaveTableAPI, '/api/table/save_table')
    api.add_resource(AutoFillAPI, '/api/doc_temp/autofill')
    api.add_resource(SessionResource, '/api/source')