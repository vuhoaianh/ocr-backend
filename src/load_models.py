import json
import torch
from pymongo import MongoClient
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import sys
import docx
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from paddleocr import PaddleOCR, draw_ocr
import numpy as np
import warnings
from ultralytics import YOLO
from dotenv import load_dotenv
import cv2
from ocr_utils import (line_check, clean_text, check_key_similarity, find_similar_strings, check_date,
                        get_right_of_substring, CLS_MAP)
from template import TEMPLATE
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image
from detr.models import build_model
from src.settings import *
warnings.filterwarnings("ignore")
load_dotenv()
CLIENT = MongoClient(os.getenv('DB_HOST'), int(os.getenv('DB_PORT')))


def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_GCM)
    json_data = json.dumps(data)
    ciphertext, tag = cipher.encrypt_and_digest(json_data.encode('utf-8'))
    return ciphertext, cipher.nonce, tag

def VietOCR_model():
    # Load vietOCR model
    config = Cfg.load_config_from_name('vgg_transformer')
    config['weights'] = VIETOCR_MODEL
    config['cnn']['pretrained']=False
    config['device'] = 'cpu'
    config['predictor']['beamsearch']=False

    viet_ocr = Predictor(config)
    return viet_ocr


def PaddleOCR_model():
    # paddle_ocr = PaddleOCR(show_log=False)
    paddle_ocr = PaddleOCR(det=True, show_log=False, use_gpu=False)
    return paddle_ocr


def Table_structure_model():
    str_model_path = TSR_MODEL
    str_config_path = TSR_MODEL_CONFIG
    with open(os.path.join(current_dir, str_config_path), 'r') as f:
        str_config = json.load(f)
    str_args = type('Args', (object,), str_config)
    str_args.device = 'cpu'
    str_model, _, _ = build_model(str_args)
    print("Table Structure model initialized.")

    str_model.load_state_dict(torch.load(os.path.join(current_dir, str_model_path),
                                        map_location=torch.device('cpu')), strict=False)
    str_model.to('cpu')
    str_model.eval()
    return str_model


def Table_detection_model():
    det_model_path = TD_MODEL
    det_config_path = TD_MODEL_CONFIG
    with open(os.path.join(current_dir, det_config_path), 'r') as f:
        det_config = json.load(f)
    det_args = type('Args', (object,), det_config)
    det_args.device = 'cpu'
    det_model, _, _ = build_model(det_args)
    print("Table Detection model initialized.")
    det_model.load_state_dict(torch.load(os.path.join(current_dir, det_model_path),
                                        map_location=torch.device('cpu')), strict=False)
    det_model.to('cpu')
    det_model.eval()
    return det_model


class OCR_CCCD:
    def __init__(self) -> None:
        self.client = CLIENT
        self.db_cccd = self.client[os.getenv('DB_CCCD')]
        self.corner_detection_model = YOLO(CORNER_DETECTION_MODEL)
        self.text_detection_model = YOLO(TEXT_DETECTION_MODEL)
        # self.corner_detection_model.to("cuda")
        # self.text_detection_model.to("cuda")
        config = Cfg.load_config_from_name('vgg_transformer')
        config['cnn']['pretrained'] = False
        config['device'] = 'cpu'
        config['weights'] = VIETOCR_MODEL
        self.text_recognition_model = Predictor(config)

    # def load_db_collection(self, username):
    #     cccd_coll = self.db_cccd[username]
    #     return cccd_coll
    def detect_corners(self, image):
        if isinstance(image, str):
            img_raw = cv2.imread(image, cv2.IMREAD_COLOR)
            # img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
        else:
            img_raw = image
        # ori_img = img_raw.copy()
        img = np.float32(img_raw)
        det = self.corner_detection_model(img)
        if det[0]:
            dets = det[0]
        boxes = dets.boxes.xyxy.cpu().numpy().tolist()
        cls = dets.boxes.cls.cpu().numpy().tolist()
        temp_dict = {}
        x_coords = []
        y_coords = []
        for i in range(len(cls)):
            c = int(cls[i])
            xmin = int(boxes[i][0])
            ymin = int(boxes[i][1])
            xmax = int(boxes[i][2])
            ymax = int(boxes[i][3])
            temp_dict.update({str(c): ymin})

            x_coords.append(xmin)
            x_coords.append(xmax)
            y_coords.append(ymin)
            y_coords.append(ymax)
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        return min_x, min_y, max_x, max_y, temp_dict, img_raw

    @staticmethod
    def process_output(out_dict):
        hoten = out_dict['Họ và tên'] if 'Họ và tên' in out_dict else ''
        idx = out_dict['ID'] if 'ID' in out_dict else ''
        ns = out_dict['Ngày sinh'] if 'Ngày sinh' in out_dict else ''
        gt = out_dict['Giới tính'] if 'Giới tính' in out_dict else ''
        qt = out_dict['Quốc tịch'] if 'Quốc tịch' in out_dict else ''
        qq = out_dict['Quê quán'] if 'Quê quán' in out_dict else ''
        date = out_dict['Có giá trị đến'] if 'Có giá trị đến' in out_dict else ''
        tt = out_dict['Nơi thường trú'] if 'Nơi thường trú' in out_dict else ''
        return (f"Họ và tên: {hoten}\n"
                f"ID num : {idx}\n"
                f"Giới tính: {gt}\n"
                f"Quốc tịch: {qt}\n"
                f"Ngày sinh: {ns}\n"
                f"Quê quán: {qq}\n"
                f"Có giá trị đến: {date}\n"
                f"Nơi thường trú: {tt}"
                )

    def ocr_process(self, image, user_id, show=False):

        out_dict = {}
        min_x, min_y, max_x, max_y, temp_dict, ori_image = self.detect_corners(image)
        # print(ori_image)
        cropped_img = ori_image[min_y:max_y, min_x:max_x]
        crop_h, crop_w = cropped_img.shape[:2]
        if crop_h > crop_w:
            try:
                if temp_dict['0'] > temp_dict['2']:
                    rotated = cv2.rotate(cropped_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                else:
                    rotated = cv2.rotate(cropped_img, cv2.ROTATE_90_CLOCKWISE)
            except KeyError as e:
                rotated = cropped_img
        else:
            rotated = cropped_img
        # save_name = os.path.basename(image)
        # cv2.imwrite(os.path.join("./crop_imgs", save_name), rotated)
        dets = self.text_detection_model(rotated, conf=0.1)
        if not dets:
            "No detection"
        for det in dets:
            cls = det.boxes.cls.cpu().numpy().astype(int).tolist()
            bboxes = det.boxes.xyxy.cpu().numpy().astype(int).tolist()
            for bbox, c in zip(bboxes, cls):
                crop = rotated[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                crop = Image.fromarray(crop)
                text = self.text_recognition_model.predict(crop)
                out_dict.update({CLS_MAP[c]: text})
                cv2.rectangle(ori_image, (int(bbox[0] + min_x), int(bbox[1] + min_y)),
                              (int(bbox[2] + min_x), int(bbox[3] + min_y)), (0, 255, 0), 2)
                cv2.putText(ori_image, text, (int(bbox[0] + min_x), int(bbox[1] + min_y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            if show:
                cv2.imshow("Prediction", ori_image)
                cv2.waitKey(0)
        tt1 = out_dict['thuong_tru_1'] if 'thuong_tru_1' in out_dict else ''
        tt2 = out_dict['thuong_tru_2'] if 'thuong_tru_2' in out_dict else ''
        tt_merge = tt1 + ' ' + tt2
        out_dict.update({"Nơi thường trú": tt_merge})
        coll_name = "cccd_" + str(user_id)
        coll = self.db_cccd[coll_name]
        key = get_random_bytes(16)
        ciphertext, nonce, tag = encrypt_data(out_dict, key)
        document = {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'tag': tag
        }
        coll.insert_one(document)
        return out_dict


class OcrTemplate:
    def __init__(self):
        self.paddle_ocr = PaddleOCR_model()
        self.viet_ocr = VietOCR_model()
        self.client = CLIENT
        self.db_key = self.client[os.getenv('DB_KEY')]
        self.collection_text = None
        self.collection_keys = self.db_key[os.getenv('COLL_KEY')]

    def load_key_collection(self, username):
        self.collection_text = self.db_key[username]

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
            # img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
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

    def process_template(self, image, template_id):
        if isinstance(int(template_id), int):
            template_id = int(template_id)
        else:
            raise "template_id must be an integer"
        template = [i for i in TEMPLATE if i['id'] == template_id]
        if not template:
            raise Exception('No doc_temp found')
        else:
            template = template[0]
        output = self.ocr_image(image)
        # print(output)
        result = []
        for idx in range(len(output)):
            txt = output[idx]['text']
            # print(txt)
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
        coll = self.collection_text
        key = get_random_bytes(16)
        ciphertext, nonce, tag = encrypt_data(result_dict, key)
        document = {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'tag': tag
        }
        coll.insert_one(document)
        self.save_docx(result_dict)
        return result

    def process_native(self, image):
        template = self.collection_keys.find_one(sort=[('_id', -1)])
        if not template:
            raise "Khong tim thay danh sach key"
        output = self.ocr_image(image)
        result = []
        for idx in range(len(output)):
            txt = output[idx]['text']
            # print(txt)
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
        coll = self.collection_text
        key = get_random_bytes(16)
        ciphertext, nonce, tag = encrypt_data(result_dict, key)
        document = {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'tag': tag
        }
        coll.insert_one(document)
        self.save_docx(result)
        return result