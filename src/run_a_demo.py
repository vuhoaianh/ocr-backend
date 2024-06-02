# from utils import seperate_image, ocr_table
# import cv2
# import json
# from table2excel import table2excel


# # image = r"C:\Users\Sondv\Documents\sondv\code4fun\smart_ocr\demo_image.png"
# image = r"dd.png"
# img = cv2.imread(image)
# results = seperate_image(img)
# tables_metadata = []
# if len(results['tables']) != 0:
#     for table in results['tables']:
#         table_data = ocr_table(table)
#         tables_metadata.append({'table_id': "id", 'table_coordinate': table['table_coordinate'],
#                                 'table_image': 'test', 'table_data': table_data})
# dm = tables_metadata[0]
# print(dm)
# table2excel(data=dm, filename="table.xlsx")

from ocr_utils import (line_check, clean_text, check_key_similarity, find_similar_strings, check_date,
                        get_right_of_substring, CLS_MAP)
from table2excel import table2excel
import cv2
import json
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image
import numpy as np
import docx

# Define the TEMPLATE constant
TEMPLATE = [
    {
        "id": 1,
        "template_name": "Giấy đề nghị thanh toán",
        "line": ["Đơn vị", "Bộ phận", "Họ và tên người đề nghị thanh toán",
                 "Bộ phận (hoặc địa chỉ)", "Nội dung thanh toán", "Số tiền", "Viết bằng chữ", "Phương thức thanh toán",
                 "Nguồn kinh phí", "Họ, tên người đề nghị thanh toán", "Mã số đề tài"],
        "block": [],
    },
    {
        "id": 2,
        "template_name": "Giấy thu",
        "line": ["Đơn vị", "Địa chỉ", "Ngày", "tháng", "năm", "Quyển số", "Nợ", "Số", "Có", "Họ và tên người nộp tiền",
                 "Địa chỉ", "Lý do nộp", "Số tiền", "Viết bằng chữ", "Đã nhận đủ số tiền", "Kèm theo",
                 "Tỉ giá ngoại tệ (vàng bạc, đá quý)", "Số tiền quy đổi"],
        "block": []
    },
    {
        "id": 3,
        "template_name": "Phiếu chi",
        "line": ["Quyển số", "Số", "Nợ", "Có", "Họ và tên người nhận tiền", "Họ và tên người nhận", "Địa chỉ",
                 "Lý do chi",
                 "Số tiền", "Bằng chữ", "Kèm theo", "Đã nhận đủ số tiền (viết bằng chữ)"],
        "block": []
    }
]

class OcrTemplate:
    def __init__(self):
        self.paddle_ocr = self.PaddleOCR_model()
        self.viet_ocr = self.VietOCR_model()

    @staticmethod
    def PaddleOCR_model():
        paddle_ocr = PaddleOCR(det=True, show_log=False, use_gpu=False)
        return paddle_ocr

    @staticmethod
    def VietOCR_model():
        config = Cfg.load_config_from_name('vgg_transformer')
        config['weights'] = 'path/to/vietocr/weights'  # Update with the correct path to your VietOCR weights
        config['cnn']['pretrained'] = False
        config['device'] = 'cpu'
        viet_ocr = Predictor(config)
        return viet_ocr

    @staticmethod
    def save_docx(result, filename="template.docx"):
        txt = ''
        for i in result:
            if i == "doc_temp":
                pass
            else:
                txt += i + " : " + result[i] + '\n'
        doc = docx.Document()
        doc.add_paragraph(txt)
        doc.save(filename)

    def ocr_image(self, image):
        if isinstance(image, str):
            img_raw = cv2.imread(image, cv2.IMREAD_COLOR)
        else:
            img_raw = image
        pil_img = Image.fromarray(img_raw)
        image_array = np.array(img_raw)
        paddle_rs = self.paddle_ocr.ocr(image_array)
        result = []
        for dets in paddle_rs:
            for det in dets:
                bbox = det[0]
                im_crop = pil_img.crop((bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]))
                recognized_text = self.viet_ocr.predict(im_crop)
                result.append({'text': recognized_text, 'box': [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]]})
        return result

def test_process_template(image, template_id):
    if isinstance(int(template_id), int):
        template_id = int(template_id)
    else:
        raise "template_id must be an integer"
    
    template = [i for i in TEMPLATE if i['id'] == template_id]
    if not template:
        raise Exception('No doc_temp found')
    else:
        template = template[0]
    
    ocr = OcrTemplate()
    output = ocr.ocr_image(image)
    result = []

    for idx in range(len(output)):
        txt = output[idx]['text']
        points = output[idx]['box']
        if txt in template['line']:
            if line_check(output[idx + 1]['box'], points):
                value = output[idx + 1]['text']
                result.append({txt: clean_text(value)})
        elif check_key_similarity(txt, template['line'], threshold=0.8) is not None:
            key = check_key_similarity(txt, template['line'], threshold=0.8)
            try:
                if line_check(output[idx + 1]['box'], points):
                    value = output[idx + 1]['text']
                    result.append({key: clean_text(value)})
            except IndexError:
                pass
        similar_list = find_similar_strings(template['line'], txt, threshold=0.8)
        if check_date(txt):
            if "Ngày tạo phiếu" in [list(i.keys())[0] for i in result]:
                pass
            else:
                result.append({"Ngày tạo phiếu": txt})
        if not similar_list:
            continue
        else:
            key = similar_list[0]
            value = get_right_of_substring(txt, key)
            if key == "Nội dung thanh toán":
                for j in range(idx + 1, len(output)):
                    if "Số tiền" in output[j]["text"]:
                        break
                    else:
                        value += " {}".format(output[j]['text'])
            if key in ["Nợ", "Có"]:
                if line_check(points, output[idx + 1]['box']):
                    value += f"    {output[idx + 1]['text']}"
            result.append({key: clean_text(value)})

    result = [i for i in result if list(i.values())[0] != '']
    result = [i for i in result if i not in [{'Số': 'tiền'}, {'Họ và tên người nhận': 'tiền'}]]
    result_dict = {'doc_temp': template['template_name']}
    for d in result:
        result_dict.update(d)

    OcrTemplate.save_docx(result_dict, filename="test_template.docx")
    return result

if __name__ == "__main__":
    # Process the table from the image
    image = r"sample.png"


    # Process the template from the image
    test_template_id = 1  # Replace with the appropriate template ID
    result = test_process_template(image, test_template_id)
    print(result)
