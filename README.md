VimBox
======

I use vim a lot. I keep a lot of notes across machines. `VimBox` was born as a
cheap way to sync those notes using dropbox while having a bit more control
than with their client, namely

* Manual sync: `vimbox /notes/cookbook` will download the remote file open it in `vim` and push it to remote upon closing.

* Minimal syncing: Can be set to keep zero files in the computer. Local files can be used to work offline.

* Merge operation: If there are discrepancies between local and remote, `vimdiff` will be called instead of `vim`.

* Autocomplete: Folder browsing autocomplete with `TAB` as if folders were local. It uses `bash` `complete` command for this.

* Optional encryption in the dropbox side with `pycrypto`. Names will be hashed and content encrypted.

* `virtualenv` friendly: stores config and file cache inside `virtualenv` folder.

* Comes with the expected `vimbox ls` (`rm` `cp` `mv`)

* Importable methods to use in other modules `from vimbox import edit, move`.

* Code is thought to replace `vim` and `vimdiff` by other editors

* Code is thought to add backends other than `dropbox` (`dropbox paper` is in sight)

* Works in OSX and Linux, uses dropbox v2 API (`python 2`!).

# Examples

Create a new file on dropbox or register locally a file created on other
machine

    vimbox -f /path/to/file

This will open a normal vim session, upon closing the content will be pushed to
dropbox a local copy is kept by default but this can be unselected.

Edit an exiting file on dropbox

    vimbox /path/to/file

If the local and remote copies differ `vimdiff` will be called instead of
`vim`. Default is always overwrite local with remote (right side)

Browse files in a folder using

    vimbox /path/to/

`VimBox` autocompletes folder with

    vimbox /path/ + <TAB>

This will use cache of registered folders load from your `~/.bashrc` via the
`complete` command. This means that new folder will only be available in the
cache the next time you open a window or if you `source`.

To create files encrypted on the dropbox side, use `-e` instead of `-f`

    vimbox -e /path/to/file

you will be prompted for a password. It wont be stored anyway so remember it.
The rest of `vimbox` functionalities are retained after creation but you will
need to input the password for each `_pull` from the remote. Encryption uses
the `pycripto` module.

# Install

Clone the repo and install it

    git clone git@gitlab.com:ramon-astudillo/vimbox.git
    sudo pip install vimbox/

Configure the back-end by calling the program for the first time.

    vimbox setup

The install menu will ask you for a dropbox access token. Getting this is a
simple process. In any computer with a browser, create a new app on your
dropbox account by visiting

    https://www.dropbox.com/developers/apps/create

and use following configuration

* `Dropbox API`

* Both `App folder` and `Full Dropbox` are possible. The former is better for a
  try-out

* Put a name. This is irrelevant, but `vimbox-<your name>` may help you remember

After this is done you will see a control pannel for the app. Use the
`Generated access token` botton to get an acess token that you can paste into
the install prompt.

# Upgrade

If you want to update to the latest version

    cd vimbox
    git pull origin master
    sudo pip install . --upgrade

For development, you can work on a virtual environment

# Install Details

The `vimbox setup` will do two changes in your system. It will create a
`.vimbox` folder on your personal area. It will also add the following line to
your `.bashrc` to load the cache of remote folders

    complete -W "$(vimbox complete)" 'vimbox'

**NOTE:** If you use a `virtualenv` this changes will be performed inside of
the virtual environments `activate` script. Deleting the `virtualenv` will undo
this changes. See next section for details.

# Develop

To develop the easiest is to use a virtual environment. Vimbox will detect this
and store the `.vimbox` config folder in the same folder where the install is
carried out. As an example

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python setup.py develop

# Troubleshooting

In OSX with `macports`, python entry points get installed in a folder not in
the PATH. It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /Users/$(whoami)/bin/vimbox

# Versions

### Desired Features

* Proper paths for temporary files

* wrapper around vim (tunnel all options)
    :( forces to sync files by separate, big change of flow. Unfrequent use

* Info that the user can screw-up (cache, hashes) should not be on config

* Add `find` semantics i.e. `vimbox /folder1/folder2/*` regexp will look
  downwards on the tree and return the matches if there is many, open directly
  if there is one

* Add fuzzy search mode `vimbox /folder/ regexp` open file in folder matching
  `regexp` print options otherwise.

* `vimbox sync` to sync entire cache
    - only makes sense with no local copy option

* `vimbox --cached ls /path/`

* Increased privacy: encrypt/decrypt inside `vim` using `vim -x`
    - differentiate editor-encryption from normal encryption
    - `vimbox -x` (`password is not None` no longer will be a good flag)

* Back-end side encryption with stored key on client side
    - how to handle already encrypted files (two hash tables?)
    - `vimbox -k`

* Update autocomplete from vimbox after new register (instead of `source`)

* Other backends e.g. `vimbox /evernote/notes/`
    [ ] Unit test with back-end and editor mock-ups
    - `dropbox paper` has an API, unclear how flexible
    - `CloudBlaze` is an alternative to dropbox
    - `evernote` seems accessible

* Import for virtualenv `vimbox setup --merge-config ~/.vimbox/config.yml`

* Set editors used in config

* Avoid two calls when working with remote

* Factor `remote.edit()` logic

* Move encripted files

* `vimbox mkdir /cosa/`. Right now this is achieved by creating a file inside

* Fix can not create encripted files at top level

* Fix `IV456` initialization and syncing across clients
    - Use a .vimbox/ folder in dropbox
    - OR just ask user for manual sync

### Upcoming v0.1.1

* pipes to allow for a cheap remote-local transfer, for example
    [ ] `cat mylog | vimbox pipe -f /logs/mylog`
        - needs Factor `remote.edit()` logic
    [x] `vimbox cat /logs/slides | pandoc -o slides.pdf`

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
