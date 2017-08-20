# noinspection PyPackageRequirements
from string import lstrip

from Crypto.Cipher import AES
import base64
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class Password(object):
    def __init__(self):
        self.password = Password.decode_password()

    @staticmethod
    def encode_password():
        # Get password from ENV.
        # Get secret from ENV.
        # print encoded password to stdout.
        password = os.environ.get('PASSWORD').rjust(32)
        secret_key = os.environ.get('SECRET')

        cipher = AES.new(secret_key, AES.MODE_ECB)
        encoded = base64.b64encode(cipher.encrypt(password))
        print encoded

    @staticmethod
    def decode_password():
        password = os.environ.get('PASSWORD')
        secret_key = os.environ.get('SECRET')

        cipher = AES.new(secret_key, AES.MODE_ECB)

        decoded = lstrip(cipher.decrypt(base64.b64decode(password)))
        return decoded


PASSWORD = Password()