import json
from Crypto.Cipher import AES


def encrypt_data(data):
    with open('encrypted_key.bin', 'rb') as file:
        key = file.read()
    cipher = AES.new(key, AES.MODE_GCM)
    json_data = json.dumps(data)
    ciphertext, tag = cipher.encrypt_and_digest(json_data.encode('utf-8'))
    return ciphertext, cipher.nonce, tag


def decrypt_data(ciphertext, nonce, tag):
    with open('encrypted_key.bin', 'rb') as file:
        key = file.read()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    decrypted_json = decrypted_data.decode('utf-8')
    decrypted_dict = json.loads(decrypted_json)
    return decrypted_dict