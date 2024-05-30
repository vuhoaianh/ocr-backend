from PIL import Image
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd
from utils import *
from init_models import viet_ocr, paddle_ocr


# def ocr_image(image):
#     image_array = np.array(image)
#     paddle_rs = paddle_ocr.ocr(image_array)
#     result = []
#     for dets in paddle_rs:
#         if not dets:
#             return ""
#         else:
#             for det in dets:
#                 bbox = det[0]
#                 im_crop = image.crop((bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]))
#                 recognized_text = viet_ocr.predict(im_crop)
#                 result.append({'text': recognized_text, 'box': [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]]})
#     return result


# def process_template(output, template_id):
#     # print(output)
#     result = []
#     for idx in range(len(output)):
#         txt = output[idx]['text']
#         # print(txt)
#         points = output[idx]['box']
#         if txt in template_id['line']:
#             if line_check(output[idx+1]['box'], points):
#                 value = output[idx+1]['text']
#                 result.append({txt: clean_text(value)})
#         elif check_key_similarity(txt, template_id['line'], threshold=0.8) is not None:
#             key = check_key_similarity(txt, template_id['line'], threshold=0.8)
#             try:
#                 if line_check(output[idx + 1]['box'], points):
#                     value = output[idx + 1]['text']
#                     result.append({key: clean_text(value)})
#             except IndexError:
#                 pass
#         similar_list = find_similar_strings(template_id['line'], txt, threshold=0.8)
#         if check_date(txt):
#             if "Ngày tạo phiếu" in [list(i.keys())[0] for i in result]:
#                 pass
#             else:
#                 result.append({"Ngày tạo phiếu": txt})
#         if not similar_list:
#             continue
#         else:
#             key = similar_list[0]
#             value = get_right_of_substring(txt, key)
#             if key == "Nội dung thanh toán":
#                 for j in range(idx + 1, len(output)):
#                     if "Số tiền" in output[j]["text"]:
#                         break
#                     else:
#                         value += " {}".format(output[j]['text'])
#             if key in ["Nợ", "Có"]:
#                 if line_check(points, output[idx + 1]['box']):
#                     value += f"    {output[idx + 1]['text']}"
#             result.append({key: clean_text(value)})
#
#     result = [i for i in result if list(i.values())[0] != '']
#     result = [i for i in result if i not in [{'Số': 'tiền'}, {'Họ và tên người nhận': 'tiền'}]]
#
#     return result
#
#
# if __name__ == "__main__":
#     image_path = r"C:\Users\Sondv\Documents\sondv\code4fun\smart_ocr\demo_image.png"
#     image_pil = Image.open(image_path)
#     detection = ocr_image(image_pil)
#     rs = process_template(detection, template_id=1)
#     print(rs)