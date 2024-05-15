from Crypto.Cipher import AES
import os

# Generate a random key
key = os.urandom(16)  # 16 bytes key for AES-128

with open('encrypted_key.bin', 'wb') as file:
    file.write(key)