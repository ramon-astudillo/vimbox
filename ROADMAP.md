# Ideas

* New entry point `bim <local path>` stores backups in backend
  - Remote path is concatenation of hashes for (user, machine, file name) and
    (full path)  
  - Path should be decryptable with key  

* Put comments on yamls config fields automatically

# Versions

### Desired Features

* Add `vimbox find` or `vimbox walk` generator

* Set editors used in config

* separate entry point `vimbox-cache `for `complete` call to ensure speed and
  stability

* Input pipes `cat mylog | vimbox pipe -f /logs/mylog`
    - [x] needs Programatic edit operations

* `vimbox share` to get shareble URL (dropbox only)

* Simple use in other Python code 
    - config auto completion?
    - Alias in the base `from vimbox import list, move, remove`

* Other backends e.g. `vimbox /evernote/notes/`
    - `Google Drive`, see https://developers.google.com/drive/api/v3/quickstart/python
    - `dropbox paper`, see https://www.dropbox.com/developers/documentation/http/documentation#paper 
    - `CloudBlaze` 
    - How to organize, protocols? `vimbox cp db:/notes/old gd:/notes/`

* Replace deprecated pycrypto by pycryptodome, see
    - see https://github.com/dlitz/pycrypto/issues/173 
    - see https://github.com/Legrandin/pycryptodome

* Uniform scheme to turn exceptions into `print + exit(1)`

* Wildcards in commands `vimbox mv /notes/* /old_notes/`

* Update autocomplete from vimbox after new register (instead of `source`)
    - [x] update function with submodule
    - [ ] create bash script to set complete

- Refactor argument parsing with`click`
    - Really missing `vimbox -O` but does not seem easy

* Clean-up `list_folder` code

* Add `vimbox local` to get local path of files

* Proper unit tests with pytest

- [ ] local encryption: `vim -x` with `vimbox -x`
    - Should imply using the auto-encryption token
- [ ] auto-encryption token:
    - created on vimbox setup 
    - Should be used if password left empty when decrypting

- [ ] Nicer error handling
    - Move but target exists throws not nice error

* Rename `vimbox.remote.primitives` to `vimbox.remote.__init__`

- [ ] Fix `remote_root` actually not implemented

- [ ] Fix local not updated after edits

- [ ] Remove use of exits at multiple depths implement ordered exit

### Ongoing v0.4

- [x] Fix display of encrypted files not in order when listing
- [x] display folders in different color (blue?) in `vimbox ls`
- [x] Fix viewing files but not editing them does not trigger delete locally
- [x] Refactor `edit` as injecting an edit operation on a `sync` 
    - This deprecates `edit(diff_mode=True)` in favour of `sync`
- [x] Programatic edit operations. `edit` is now `sync` with `edit` argument
  set. This argument is a function, see edit for examples.
- [x] automerge: optionally append or insert can be done automatically. Set 
    one document as reference, disallow losing info by following primitives
    - append/prepend to ref
    - append/prepend to lines of ref
    - insert to ref
    - Custom line merge (this MAY remove info from ref)   
        - custom equal operator `(A) Cosa` same as `(B) Cosa` 

- [ ] Upgrade folder primitives
    - [x] Add `vimbox mkdir`
    - [x] Replace ambiguous `is_file` by `file_type` in client and back-end
      clients
        - Avoid using `api-error` from Dropbox unless it is really unknown
    - [x] Fix and Re-allow `vimbox mv with folders` 
        - [x] Fix `vimbox mv /one/folder /other/` not disallowed
        - also local removal will die since it is not empty
        - [x] add specific unit tests
    - [x] remove use of api-error, not indicative enough
    - [x] Fix root files start with slash
    - [ ] Fix creating files with same name as folders 

- [ ] Upgrade handling of encrypted files
    - [x] Move encrypted files
    - [ ] Fix collision of hashed and unhashed names when moving files
    - [x] Fix can not create encrypted files at top level in dropbox
    - [ ] MD5 hashing does not count as encryption, use SHA-1 from hashlib
    - [x] hash only file name, rather than path
    - [x] When creating file or folder, we could have an encrypted version

- [ ] Remove uncontrolled use of ApiError. Should either die or recognize valid
  api-error and coresponding state 

### v0.3.1

- [x] Fix Python3 compatibility 
- [x] Add dropbox backend integration-test
- [x] Add unit-test fake backend
- [x] Refactor backend client into a class with dropbox as a particular case
- [x] `vimbox -f /path/to/file "some text"` for file initialization
- [x] Add bash source function (no comand yet uses it)

### v0.3.0

- [x] Python3 compatibility (in beta)
- Minor fixes

### v0.2.0

- [x] Fix `vimbox mv` does not update `path_hashes`
    - disallowed move on encrypted files
- [x] Avoid two calls when working with remote
- [x] Fix `IV` initialization and syncing across clients
    - big change as if can screw up old encrypted files

### v0.1.1

* pipes to allow for a cheap remote-local transfer, for example
    - [x] `vimbox cat /logs/slides | pandoc -o slides.pdf`

* Fix inconsistent cache: When altered I one client does not update on other clients
    - Using `vimbox ls` now updates cache

### v0.1.0

* Bug fix for encripted files `vimbox rm`.

* Fix cache add/remove
    [x] `rm` seems not to unregister
    [x] `ls` should register

* Move all dropbox code to `dropbox client` to factor out back-end code

* `vimbox /tentative/path/file` tests also if the MD5 exists
    - allows to guess encrypted file names
    - no more name collision when creating unencrypted with same name

* `vimbox -f `allowed on existing files (just opens)
    - Helps solving bug above

* Clean up namespaces of methods
    - [x] use module names at the begining of method calls
    - [x] move edit to `remote`

* Fix opening encrypted file does not register it

* Handle error when trying to create file on root

* Add specific help for commands

* Handle installation in virtualenv
    - local `~/.vimbox/` and `.bash_profile`

* Proper full installation
    - `setup.py` adds `complete` to `.bash_profile`

* Simulated bash in remote

    - `vimbox rm /logs/mylog`
    - `vimbox cp /logs/mylog /path/`
    - `vimbox cp /logs/mylog /path/mylog2`
    - `vimbox mv /logs/mylog /path/mylog2`

### v0.0.5

* More robust handling of remote behaviours

* Major refactor: isolate remote/local code. Add `pull()`

### v0.0.4

* Fix `vimbox -e /path/to/file` on existing files not allowed

* Major refactor edit() _push() functions probably better than VimBox class

### v0.0.3

* Optional encryption on the Dropbox side
    - `vimbox -e /logs/private.log` to encrypt with password
    - Once created, file works as any other file
    - Display unencrypted names locally with `vimbox ls`, in red.
    - Password not visible during input

* Fancy colored outputs print()s
