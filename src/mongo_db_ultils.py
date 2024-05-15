from pymongo import MongoClient
from utils import decrypt_data


client = MongoClient('mongodb://localhost:27017/')

# Hàm hiển thị danh sách documents trong collection
def display_collection(db_name, userId):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    collection = db[userId]
    documents = collection.find({})
    return documents

# Hàm chỉnh sửa một document trong collection
def edit_document(document_id, updated_data, db_name, userId):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    collection = db[userId]
    collection.update_one({'_id': document_id}, {'$set': updated_data})
    print('Document đã được chỉnh sửa thành công.')


# Hàm xóa một document trong collection
def delete_document(document_id):
    collection.delete_one({'_id': document_id})
    print('Document đã được xóa thành công.')

