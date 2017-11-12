import os
from math import ceil
#
try:
    from Crypto.Cipher import AES
    from Crypto.Hash import MD5
except:
    #print("\nMissing module pycrypto, no encription available")
    pass

# ACHTUNG: Changing this may yield incorrect dencription errors!
HEADER = '# this was encripted'


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


def encript_content(text, password):

    obj = AES.new(password, AES.MODE_CBC, 'This is an IV456')

    # Create header to be a multiple of 16
    old_length = len(HEADER + text)
    new_length = int(16*ceil(old_length*1./16))
    padded_header = HEADER + (' ' * (new_length - old_length - 1))
    # Add header
    headed_text = "%s\n%s" % (padded_header, text)
    return obj.encrypt(headed_text)


def decript_content(text_cipher, password):

    obj = AES.new(password, AES.MODE_CBC, 'This is an IV456')
    headed_text = obj.decrypt(text_cipher)

    # Separate header from body, return also check that decription worked
    items = headed_text.split('\n')
    header = items[0]
    text = "\n".join(items[1:])
    return text, header.rstrip() == HEADER.rstrip()



def get_path_hash(path_str, pasword):

    dirname = os.path.dirname(path_str)
    basename = os.path.basename(path_str)
    #
    h = MD5.new()
    h.update(basename)
    return "%s/.%s" % (dirname, h.hexdigest())