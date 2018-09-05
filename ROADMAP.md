# Versions

### Desired Features

* Info that the user can screw-up (cache, hashes) should not be on config

* Add `find` semantics i.e. `vimbox /folder1/folder2/*` regexp will look
  downwards on the tree and return the matches if there is many, open directly
  if there is one

* Increased privacy: encrypt/decrypt inside `vim` using `vim -x`
    - differentiate editor-encryption from normal encryption
    - `vimbox -x` (`password is not None` no longer will be a good flag)

* Back-end side encryption with stored key on client side
    - how to handle already encrypted files (two hash tables?)
    - `vimbox -k`

* Import for virtualenv `vimbox setup --merge-config ~/.vimbox/config.yml`

* Set editors used in config

* Move encripted files

* `vimbox mkdir /cosa/`. Right now this is achieved by creating a file inside

* Fix can not create encripted files at top level

* Fix viewing files but not editing them does not trigger delete locally

* Fix undeleted local files conflict when creating folders of same name

- [ ] Fix virtualenv not storing the files inside it

* Update autocomplete from vimbox after new register (instead of `source`)

* Input pipes `cat mylog | vimbox pipe -f /logs/mylog`
    - needs Programatic edit operations

* Put comments on yamls config fields automatically

- [ ] Support optional encryption `vim -x` with `vimbox -x`
    - Should imply using the auto-encryption token
- [ ] Auto encryption token on vimbox creation
    - Should be used if password left empty when decrypting

* Other backends e.g. `vimbox /evernote/notes/`
    - `dropbox paper` has an API, unclear how flexible
    - `CloudBlaze` is an alternative to dropbox
    - `evernote` seems accessible

- [ ] Programatic edit operations

### v0.3.1

- [ ] Add unit-test fake backend
- [x] Abstract backend client into a class (with dropbox as a particular case)
- [x] `vimbox -f /path/to/file "some text"` for file initialization

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
