#
import sys
sys.path.append('./vimbox/')
#
from crypto import (
#from vimbox.crypto import (
    validate_password,
    encript_content,
    decript_content
)

if __name__ == '__main__':

    text = (
        'This is some text to be encripted.\n'
        'It has three sentences of different lengths\n'
        'It is therefore kind of self-referential'
    )
    password = 'cacadevaca'

    # Ecription/Decription process
    password = validate_password(password)
    cyphered_text = encript_content(text, password)
    decripted_text, sucess = decript_content(cyphered_text, password)

    assert sucess, "Decription failed"

    print("")
    print(cyphered_text)
    print("")
    print(decripted_text)
    print("")
