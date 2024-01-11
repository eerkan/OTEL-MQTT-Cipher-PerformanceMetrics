from warnings import filterwarnings
filterwarnings("ignore")

from xycrypto.ciphers import Camellia_ECB, CAST5_ECB, AES_ECB, Blowfish_ECB, IDEA_ECB, SEED_ECB, TripleDES_ECB


def encrypt(data, cipher_payload):
    if "key" not in cipher_payload or "algorithm" not in cipher_payload:
        return data
    key = cipher_payload["key"]
    if cipher_payload["algorithm"] == "AES":
        cipher = AES_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "Blowfish":
        cipher = Blowfish_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "Camellia":
        cipher = Camellia_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "CAST5":
        cipher = CAST5_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "IDEA":
        cipher = IDEA_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "SEED":
        cipher = SEED_ECB(key)
        return cipher.encrypt(data)
    elif cipher_payload["algorithm"] == "TripleDES":
        cipher = TripleDES_ECB(key)
        return cipher.encrypt(data)
    else:
        return data


def decrypt(data, cipher_payload):
    if "key" not in cipher_payload or "algorithm" not in cipher_payload:
        return data
    key = cipher_payload["key"]
    if cipher_payload["algorithm"] == "AES":
        cipher = AES_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "Blowfish":
        cipher = Blowfish_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "Camellia":
        cipher = Camellia_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "CAST5":
        cipher = CAST5_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "IDEA":
        cipher = IDEA_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "SEED":
        cipher = SEED_ECB(key)
        return cipher.decrypt(data)
    elif cipher_payload["algorithm"] == "TripleDES":
        cipher = TripleDES_ECB(key)
        return cipher.decrypt(data)
    else:
        return None
