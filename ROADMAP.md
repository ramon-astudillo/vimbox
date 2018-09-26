# Ideas

* New entry point `bim <local path>` stores backups in backend
  - Remote path is concatenation of hashes for (user, machine, file name) and
    (full path)  
  - Path should be decryptable with key  

* Put comments on yamls config fields automatically

# Versions

### Desired Features

* Add `vimbox find` 

* Set editors used in config

* Fix `pomot edit` still syncs everything

* `vimbox mkdir /cosa/`. Right now this is achieved by creating a file inside

* separate entry point `vimbox-cache `for `complete` call to ensure speed and
  stability

* Simple use in other Python code 
    - config auto completion?

```
from vimbox.remote.primitives import VimboxClient
client = VimboxClient(dropbox_token='some-alphanumeric-sequence')
client.move()
```

* Other backends e.g. `vimbox /evernote/notes/`
    - `dropbox paper` 
    - `CloudBlaze` 
    - `evernote` 

* Replace deprecated pycrypto by pycryptodome, see
    - see https://github.com/dlitz/pycrypto/issues/173 
    - see https://github.com/Legrandin/pycryptodome

* Input pipes `cat mylog | vimbox pipe -f /logs/mylog`
    - needs Programatic edit operations

* Programatic edit operations

* Update autocomplete from vimbox after new register (instead of `source`)
    - [x] update function with submodule
    * update command

- [ ] Fix viewing files but not editing them does not trigger delete locally
- [ ] Fix virtualenv not storing the files inside it

- [ ] Fix creating files with same name as folders 
    - api-error not indicative enough

- [ ] local encryption: `vim -x` with `vimbox -x`
    - Should imply using the auto-encryption token
- [ ] auto-encryption token:
    - created on vimbox setup 
    - Should be used if password left empty when decrypting
- [ ] Upgrade handling of encrypted files
    - [ ] Move encrypted files
    - [ ] Fix collision of hashed and unhashed names when moving files
    - [ ] Fix can not create encrypted files at top level in dropbox
    - hash only file name, rather than path?

- [ ] automerge: optionally append or insert can be done automatically
    - For append/prepend
        - len(modified) > len(original)
        - EOF tokenization
        - modified[:len(original)] == original
        - modified[-len(original):] == original
    - For insert
        - EOF tokenization
        - len(modified) > len(original)
        - Linear search over len(modified) + len(original)
    - Custom line merge    
        - custom equal operator `(A) Cosa` same as `(B) Cosa` or `Cosa` 
        - this treats original and edites by separate, may be limiting

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
