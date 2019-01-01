# General

Class hierachy and functionality

    VimboxClient
        # - Provide support for higher functionalities e.g. encryption
        # - raise VimboxClientError for ordered exit at entry points
        # - print messages in command line
        StorageBackEnd
            # - Provide homogeneus behaviour to VimboxClient
            # - Provide basic set of primitives across all back-ends
            # - Handle connection behaviour
            External API (e.g. dropbox)


# StorageBackEnd methods

Scenarios:

- online but ressource does not exist (and the method assumed it did)
    - need to double check for encrypted
    - `response` should be `False` 
    - PROBLEM: methods that create should allways check for encrypted file
- online but ressource is not the type assumed in the method (folder / file)
    - `response` should be `False` 
- online but unknown api-error
    - raise VimboxClientError
    - `response` should be `None` 
- online and ok    
    - planned `response` including `None` 

- offline


# Encryption pain

- have to assume you don't know if a file-name is used encrypted in the remote
- checking for both encrypted and un-encrypted name all times is expensive
    - If fetch, but files does not exist, then try encrypted/unecrypted:w
    - If copy, also need to check for target existing

# Offline pain

- `pull` with no remote should raise, to avoid uncontrolled states 
