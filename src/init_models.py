from load_models import (VietOCR_model, PaddleOCR_model, OCR_CCCD, OcrTemplate, Table_detection_model,
                          Table_structure_model)

viet_ocr = VietOCR_model()
paddle_ocr = PaddleOCR_model()
cccd_ocr = OCR_CCCD()
ocr_template = OcrTemplate()
td_model = Table_detection_model()
tsr_model = Table_structure_model()