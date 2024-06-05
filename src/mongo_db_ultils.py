from pymongo import MongoClient
from encrypt import decrypt_data, encrypt_data
import json
from bson import ObjectId


client = MongoClient('mongodb://localhost:27017/')


def display_collection(db_name, user_id):
    if db_name not in ('db_text', 'db_key', 'db_cccd', 'db_document'):
        raise ValueError('db_name must be one of "db_text", "db_key", "db_cccd", "db_document"')
    else:
        db = client[db_name]
        collection = db[user_id]
        documents = collection.find({})
        rs = []
        for document in documents:
            id_ = document['_id']
            ciphertext = document['ciphertext']
            nonce = document['nonce']
            tag = document['tag']
            decrypted_dict = decrypt_data(ciphertext, nonce, tag)
            rs.append({"id_": str(id_), "document": decrypted_dict})
    return rs


def get_documents(db_name, user_id, document_id):
    if db_name not in ('db_text', 'db_key', 'db_cccd', 'db_document'):
        raise ValueError('db_name must be one of "db_text", "db_key", "db_cccd", "db_document"')
    
    if isinstance(document_id, str):
        try:
            document_id = ObjectId(document_id)
        except Exception as e:
            raise ValueError("Invalid document_id format. Must be a valid ObjectId string.")
    
    db = client[db_name]
    collection = db[user_id]
    document = collection.find_one({'_id': document_id})
    
    if document:
        ciphertext = document['ciphertext']
        nonce = document['nonce']
        tag = document['tag']
        decrypted_dict = decrypt_data(ciphertext, nonce, tag)
        return decrypted_dict
    else:
        raise ValueError("No document with id {}".format(document_id))


def edit_document(db_name, user_id, updated_data, document_id):
    updated = json.loads(updated_data)
    ciphertext, nonce, tag = encrypt_data(updated)
    document = {
        'ciphertext': ciphertext,
        'nonce': nonce,
        'tag': tag
    }
    if db_name not in ('db_text', 'db_key', 'db_cccd', 'db_document'):
        raise ValueError('db_name must be one of "db_text", "db_key", "db_cccd", "db_document"')
    else:
        if isinstance(document_id, str):
            try:
                document_id = ObjectId(document_id)
            except Exception as e:
                raise ValueError("Invalid document_id format. Must be a valid ObjectId string.")
        db = client[db_name]
        collection = db[user_id]
        result = collection.update_one({'_id': document_id}, {'$set': document})
        if result.modified_count > 0:
            print('Document has been successfully updated.')
            return True
        else:
            print('No document found with the given ID or no change in data.')
            return False



def delete_document(db_name, user_id, document_id):
    if db_name not in ('db_text', 'db_key', 'db_cccd', 'db_document'):
        raise ValueError('db_name must be one of "db_text", "db_key", "db_cccd", "db_document"')
    
    if isinstance(document_id, str):
        try:
            document_id = ObjectId(document_id)
        except Exception as e:
            raise ValueError("Invalid document_id format. Must be a valid ObjectId string.")
    
    db = client[db_name]
    collection = db[user_id]
    result = collection.delete_one({'_id': document_id})
    
    # Return True if a document was deleted, otherwise False
    return result.deleted_count > 0

