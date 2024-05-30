import io

from docx import Document
import pymongo


def query_name(name):
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    db = client["db_cccd"]

    collection = db["COLL_CCCD"]

    query = {"Họ và tên": name}
    result = collection.find(query)
    if result is not None:
        return result[0]
    else:
        "Khong tim thay du lieu"


def autofill(doc_file, name):
    query = query_name(name)
    name = query['Họ và tên']
    address = query['Nơi thường trú']
    dob = query['Ngày sinh']
    doc = Document(io.BytesIO(doc_file))
    for para in doc.paragraphs:
        # full_text.append(para.text)
        # text = '\n'.join(full_text)
        if name:
            para.text = para.text.replace('name_position', name)
        if address:
            para.text = para.text.replace('address_position', address)
        if dob:
            para.text = para.text.replace('dob_position', dob)
    texts = [i.text for i in doc.paragraphs]
    texts = '\n'.join(texts)
    doc.save(name + ".docx")
    return texts

#
# file = r"C:\Users\Sondv\Documents\sondv\backend-ocr-pdf-main\doc_temp\phieuchi_temp.docx"
# x = autofill(file, "Vũ đăng khoa")
# print(x)