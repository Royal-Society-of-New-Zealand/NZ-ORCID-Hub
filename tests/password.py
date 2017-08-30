# noinspection PyPackageRequirements

from Crypto.Cipher import AES
import base64
import os
from os.path import join, dirname
from dotenv import load_dotenv
import logging


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class Password(object):
    def __init__(self):
        try:
            self.password = Password.decode_password()
        except:
            logging.exception("Failed to decript the password.")
            self.password = None

    @staticmethod
    def encode_password():
        # Get password from ENV.
        # Get secret from ENV.
        # print encoded password to stdout.
        password = os.environ.get('PASSWORD', "p455w0rd").rjust(16)
        secret_key = os.environ.get('SECRET', "H6K74NG64M8GB6L3").ljust(16)

        cipher = AES.new(secret_key, AES.MODE_ECB)
        encoded = base64.encodebytes(cipher.encrypt(password))
        print(encoded)

    @staticmethod
    def decode_password():
        password = os.environ.get('PASSWORD')
        secret_key = os.environ.get('SECRET')

        cipher = AES.new(secret_key, AES.MODE_ECB)
        print(password)

        decoded = cipher.decrypt(base64.decodebytes(password.encode())).decode().strip()
        return decoded



if __name__ == "__main__":
    Password.encode_password()
else:
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    PASSWORD = Password()

