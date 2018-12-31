import os
import sys
import re
from math import ceil
#
from Crypto.Cipher import AES
from Crypto.Hash import MD5

# ACHTUNG: Changing this may yield incorrect dencryption errors!
HEADER = '# this was encrypted'


def validate_password(password):
    """
    AES key must be either 16, 24, or 32 bytes long

    We pad to those lengths when possible

    We choose whitespace as padding symbol (forbidden in passwords)
    """

    if any([x == ' ' for x in password]):
        print("Password can not contain any white spaces")
        exit()

    # Padd to 16, 24 or 32
    pass_length = len(password)
    if pass_length < 16:
        password += (' '*(16 - pass_length))
    elif 16 < pass_length < 24:
        password += (' '*(24 - pass_length))
    elif 24 < pass_length < 32:
        password += (' '*(32 - pass_length))
    elif pass_length > 32:
        print("Maximum pasword length is 32 bytes")
        exit()

    return password


def encrypt_content(text, password):

    # Generate IV
    if sys.version_info[0] > 2:
        # Python3
        iv = os.urandom(16)
    else:
        # Python2
        iv = str(os.urandom(16))
    obj = AES.new(password, AES.MODE_CBC, iv)

    # Create header to be a multiple of 16
    old_length = len("%s\n%s" % (HEADER, text))
    new_length = int(16*ceil(old_length*1./16))
    if old_length != new_length:
        padded_header = HEADER + (' ' * (new_length - old_length))
    else:
        padded_header = HEADER
    # Add header and encrypt
    headed_text = "%s\n%s" % (padded_header, text)
    return iv + obj.encrypt(headed_text)


def decript_content(text_cipher, password):

    # Recover IV
    iv = text_cipher[:16]
    text_cipher_body = text_cipher[16:]
    # Decrypt
    obj = AES.new(password, AES.MODE_CBC, iv)
    headed_text = obj.decrypt(text_cipher_body)
    # Separate header from body, return also check that decription worked
    if sys.version_info[0] > 2:
        # Python3
        try:
            items = headed_text.decode("utf-8").split('\n')
            header = items[0].rstrip()
            text = "\n".join(items[1:])
        except UnicodeDecodeError:
            items = None
            header = None
            text = headed_text
    else:
        # Python2
        items = headed_text.split('\n')
        header = items[0].rstrip()
        text = "\n".join(items[1:])

    return text, (
        header == HEADER or
        header == "# this was encripted"  # Hack pre v0.0.6, autofix
    )


def get_path_hash(path_str):

    dirname = os.path.dirname(path_str)
    basename = os.path.basename(path_str)
    #
    h = MD5.new()
    if sys.version_info[0] > 2:
        # Python3
        h.update(basename.encode("utf-8"))
    else:
        # Python2
        h.update(basename)
    if dirname != '/':
        return "%s/.%s" % (dirname, h.hexdigest())
    else:
        return "/.%s" % h.hexdigest()


def is_encrypted_path(path_str):
    """Check if path is that of an encrypted file"""
    basename = os.path.basename(path_str)
    return re.match('\.[a-z0-9]', basename) and len(basename) == 33
