from difflib import SequenceMatcher
import io
import os
from base64 import b64encode
from pymongo import MongoClient
from init_models import paddle_ocr, viet_ocr
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from tqdm import tqdm
from table_detection import table_detect
from table_structure_rec import table_structure_recognize
import fitz  # Thư viện pymupdf
from src.encrypt import encrypt_data
dirname = os.path.dirname(__file__)


def up_keys_to_db(user_id, text, name=None):
    client = MongoClient('localhost', 27017)
    db = client[os.getenv('DB_KEY')]
    collection = db[user_id]
    keys = text.split(',')
    keys = [i.strip() for i in keys]
    temp = {'id': '', 'name': name, 'line': keys}  # Thêm trường 'name'
    ciphertext, nonce, tag = encrypt_data(temp)
    document = {
        'ciphertext': ciphertext,
        'nonce': nonce,
        'tag': tag
    }  
    collection.insert_one(document)


def convert_image_to_base64(pil_img):
    img_byte_arr = io.BytesIO()
    pil_img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    img_b64_string = b64encode(img_byte_arr).decode()
    img_b64_string = img_b64_string.replace('\n', '')
    img_b64_string = 'data:image/jpeg;base64,' + img_b64_string
    return img_b64_string


# Convert pdf to list of images and preprocess
def convert_pdf2images(pdf):
    print('CONVERT_PDF2IMAGES')
    doc = fitz.open("pdf", pdf)  # Mở file PDF bằng pymupdf
    images = []
    print('PREPROCESS IMAGES')
    for page_number in tqdm(range(doc.page_count)):
        page = doc.load_page(page_number)  # Lấy từng trang trong PDF
        img = page.get_pixmap()  # Trích xuất hình ảnh từ trang PDF
        pil_img = Image.frombytes("RGB", [img.width, img.height], img.samples)  # Chuyển đổi thành hình ảnh PIL
        images.append({'page': convert_image_to_base64(pil_img)})

    doc.close()  # Đóng tài liệu PDF sau khi xử lý xong
    return images


def ocr_image(image):
    image_array = np.array(image)
    paddle_rs = paddle_ocr.ocr(image_array)
    result = []
    for dets in paddle_rs:
        if not dets:
            return ""
        else:
            for det in dets:
                bbox = det[0]
                im_crop = image.crop((bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]))
                recognized_text = viet_ocr.predict(im_crop)
                result.append({'text': recognized_text, 'box': [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]]})
    return result


def remove_stamp_and_signature(img_array, write_on_terminal=True):
    # Load image, grayscale, Gaussian blur, Otsu's threshold
    if write_on_terminal:
        print('REMOVE STAMP AND SIGNATURE')
    img_remove = img_array.copy()
    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2HSV)

    # lower mask (0-10)
    lower_red = np.array([0,50,50])
    upper_red = np.array([10,255,255])
    mask_red_0 = cv2.inRange(img_array, lower_red, upper_red)

    # upper mask (170-180)
    lower_red = np.array([155,25,0])
    upper_red = np.array([179,255,255])
    mask_red_1 = cv2.inRange(img_array, lower_red, upper_red)

    # join masks_red
    mask_red = mask_red_0 + mask_red_1

    # lower mask (100-120) - Tương ứng với màu blue
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([120, 255, 255])
    mask_blue_0 = cv2.inRange(img_array, lower_blue, upper_blue)

    # upper mask (120-140) - Tương ứng với màu blue
    lower_blue = np.array([120, 25, 0])
    upper_blue = np.array([140, 255, 255])
    mask_blue_1 = cv2.inRange(img_array, lower_blue, upper_blue)

    # join masks_blue
    mask_blue = mask_blue_0 + mask_blue_1

    img_remove = (img_remove * (np.expand_dims(cv2.bitwise_not(mask_blue) / 255, axis=2)) + np.expand_dims(mask_blue, axis=2)).astype('uint8')
    img_remove = (img_remove*(np.expand_dims(cv2.bitwise_not(mask_red)/255, axis=2))+np.expand_dims(mask_red, axis=2)).astype('uint8')

    return img_remove

def sort_bbox_text_region(metadata):
    if len(metadata) != 0:
        # Sắp xếp metadata theo y và x
        sorted_metadata = sorted(metadata, key=lambda item: (item['text-region'][1], item['text-region'][0]), reverse=True)

        return sorted_metadata
    else:
        return metadata

# Get text region bounding box
def text_region_detection(img_array, blur_kernel = (7,7), dilate_kernel = (5,4)):
    img_remove_noise = remove_stamp_and_signature(img_array)
    gray = cv2.cvtColor(img_remove_noise, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, blur_kernel, 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Create rectangular structuring element and dilate
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilate_kernel)
    dilate = cv2.dilate(thresh, kernel, iterations=5)

    # Find contours and draw rectangle
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    metadata = []
    for c in enumerate(cnts):
        x,y,w,h = cv2.boundingRect(c[1])
        if w <= h:
          continue
        # cv2.rectangle(img_array, (x, y), (x + w, y + h), (0, 255, 0), 2)
        metadata.append({'text-region': (x, y, w, h)})
    sort_metadata = sort_bbox_text_region(metadata)
    return sort_metadata

def paddle_text_region_detection(img_array):
    result = paddle_ocr.ocr(img_array, rec=False)
    metadata = []
    for line in result:
        for bbox in line:
            left = bbox[0][0]
            top = bbox[0][1]
            right = bbox[2][0]
            bot = bbox[2][1]
            if (right - left) <= (bot - top):
                continue
            metadata.append({'text-region': (int(left), int(top), int(right - left), int(bot - top))})
    sort_metadata = sort_bbox_text_region(metadata)
    return sort_metadata

# Seperate image into two part: Text image and Table images
def seperate_image(image, write_on_terminal=True):
    if write_on_terminal:
        print('SEPERATE IMAGE')
    pil_image = Image.fromarray(image.copy())
    tables = table_detect(pil_image)  # includes NMS
    image_to_crop = image.copy()
    image_text = image.copy()
    table_images = []
    if len(tables)!=0:
        for table in tables:
            x0 = int(table["bbox"][0])
            y0 = int(table["bbox"][1])
            x1 = int(table["bbox"][2])
            y1 = int(table["bbox"][3])
            table_images.append({'table_coordinate': [x0, y0, x1-x0, y1-y0], 'image': image_to_crop[y0:y1, x0:x1]})
            image_text = cv2.rectangle(image_text, (x0, y0), (x1, y1), (255, 255, 255), -1)
    # text_metadata = text_region_detection(image_text)
    text_metadata = paddle_text_region_detection(image_text)
    return {'image': image,'texts': text_metadata, 'tables': table_images}

def ocr_text(image, text_metadata):
    new_text_metadata = []
    print('GET LINE REGION AND OCR')
    for metadata in tqdm(text_metadata):
        x_text = metadata['text-region'][0]
        y_text = metadata['text-region'][1]
        w_text = metadata['text-region'][2]
        h_text = metadata['text-region'][3]
        text_region = image[y_text:y_text+h_text, x_text:x_text+w_text]
        text_region_pil = Image.fromarray(text_region)
        # text_of_metadata = ocr_image(text_region_pil)
        text_of_metadata = viet_ocr.predict(text_region_pil)
        new_text_metadata.append({'text-region': metadata['text-region'], 'text': text_of_metadata})

    return new_text_metadata


def get_cells(object_table, table_coordinates):
    table_columns = sorted([obj for obj in object_table if obj['label'] in ['table column', 'table column header']], key=lambda obj: obj['bbox'][0], reverse=False)
    table_rows = sorted([obj for obj in object_table if obj['label'] in ['table row', 'table projected row header']], key=lambda obj: obj['bbox'][1], reverse=False)
    # print(table_columns)
    columns = []
    rows = []
    cells = []
    for column_num, column in enumerate(table_columns):
        columns.append({'column_id': column_num, 'label': column['label'],
                        'coordinates': [column['bbox'][0] + table_coordinates[0],
                                        column['bbox'][1] + table_coordinates[1],
                                        column['bbox'][2] - column['bbox'][0],
                                        column['bbox'][3] - column['bbox'][1]]})
    for row_num, row in enumerate(table_rows):
        rows.append({'row_id': row_num, 'label': row['label'],
                        'coordinates': [row['bbox'][0] + table_coordinates[0],
                                        row['bbox'][1] + table_coordinates[1],
                                        row['bbox'][2] - row['bbox'][0],
                                        row['bbox'][3] - row['bbox'][1]]})
    for row in table_rows:
        cells_row = []
        for column in table_columns:
            cells_row.append([column['bbox'][0], row['bbox'][1], column['bbox'][2], row['bbox'][3]])
        cells.append(cells_row)
    return cells, columns, rows

def generate_table(image_table, cells, columns, rows):
    table_data = {
        "columns_coordinates": columns,
        "column_number": len(cells[0]),
        "row_number": len(cells),
        "rows_coordinates": rows,
        "rows": []
    }

    for cells_row in cells:
        list_text_row = []
        for cell in cells_row:
            img_cell = image_table.crop(cell)
            text_of_cell = ocr_image(img_cell)
            # text_of_cell = ' '.join(text_of_cell)
            list_text_row.append(text_of_cell)

        table_data["rows"].append(list_text_row)

    return table_data


def ocr_table(table_metadata):
    image = table_metadata['image']
    pil_image = Image.fromarray(image.copy())
    table_structure = table_structure_recognize(pil_image)
    cells, columns, rows = get_cells(table_structure, table_metadata["table_coordinate"])

    table_data = generate_table(pil_image, cells, columns, rows)

    return table_data
            

