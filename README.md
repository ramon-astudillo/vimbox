VimBox
======

I use vim a lot, I keep a lot of notes across machines. `VimBox` was born as a
cheap way to sync those notes using dropbox while having a bit more control
than with their client, namely

* Manual sync: `vimbox /notes/cookbook` will download the remote file open it in `vim` and push it to remote upon closing.

* Minimal syncing: Can be set to keep zero files in the computer. Local files can be used to work offline.

* Merge operation: If there are discrepancies between local and remote `vimdiff` will be called instead of `vim`.

* Autocomplete: Folder browsing autocomplete with `TAB` as if folders were local. It uses `bash` `complete` command for this.

* Optional encryption in the dropbox side with `pycrypto`. Names will be hashed and content encripted.

* Comes with the expected `vimbox ls` (`rm` `cp` `mv`)

* Importable methods to use in other modules `from vimbox import edit, move`.

* Code is though to replace `vim` and `vimdiff` by other editors

* Code is though to add backends other than `dropbox` (paper is in sight)

* Works in OSX and Linux, uses dropbox v2 API.

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

Browse files using

    vimbox / + <TAB>

will autocomplete using local cache of registered folders. You can also use
`vimbox /path/` or `vimbox ls /path/` to browse remote folder content. In
offline mode this will use the local cache

To create files encrypted on the dropbox side, use `-e` instead of `-f`

    vimbox -e /path/to/file

you will be prompted for a password. It wont be stored anyway so remember it.
The rest of `vimbox` functionalities are retained after creation but you will
need to input the password for each `_pull` from the remote. Encryption uses
the `pycript` module.

# Install

Clone the repo and install it

    git clone git@gitlab.com:ramon-astudillo/vimbox.git
    sudo pip install vimbox/

Configure the back-end by calling the program for the first time.

    vimbox setup

The install menu will ask you for a dropbox acess token. Getting this is a
simple process In any computer with a browser, create a new app on your dropbox
account by visiting

    https://www.dropbox.com/developers/apps/create

and use following configuration

* `Dropbox API`

* Both `App folder` and `Full Dropbox` are possible. The former is better for a
  try-out

* Put a name. This is irrelevant, but `vimbox` may help you remeber

After this is done you will see a control pannel for the app. Use the
`Generated access token` botton to get an acess token that you can paste into
the install prompt.

# Upgrade

If you want to update to the latest version

    sudo pip install vimbox/ --upgrade

For development, you can work on a virtual environment

# Install Details

The vimbox installer will do two changes in your system. It will create a
`.vimbox` folder on your personal area. It will also add the following line to
your `.bashrc` to load the cache of remote folders

    complete -W "$(vimbox complete)" 'vimbox'

*NOTE:* If you use a virtualenv this changes will be performed inside of the
virtual environment. Deleting the virtualenv will undo this changes. See next
section for details.

# Develop

To develop the easiest is to use a virtual environment. Vimbox will detect this
and store ist `.vimbox` config folder in the same folder where the install is
carried out. As an example

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python setup.py develop

The `.vimbox` folder will be created in the foder from which pip is called.
*NOTE:* Vimbox will first look for pre-existing `.vimbox` installs in your
home. If you have a version installed and you do not want to use that config,
create an empty `.vimbox` folder locally, previously with

    mkdir .vimbox

# Troubleshooting

In OSx with macports, entry_points get installed in a folder not in the PATH.
It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /Users/$(whoami)/bin/vimbox

# Versions

Roadmap

* Proper paths for temporary files

* wrapper around vim (tunnel all options)
    :( forces to sync files by separate, big change of flow. Unfrequent use

* pipes `cat mylog | vimbox pipe -f /logs/mylog` and `vimbox cat /logs/mylog`

* Info that the user can screw-up (cache, hashes) should not be on config

* Add `find` semantics i.e. `vimbox /folder1/folder2/*` regexp will look
  downwards on the tree and return the matches if there is many, open directly
  if there is one

* Add fuzzy search mode `vimbox /folder/ regexp` open file in folder matching
  `regexp` print options otherwise.

* `vimbox sync` to sync entire cache
    - only makes sense with no local copy option

* `vimbox --cached ls /path/`

* Unit test with back-end and editor mock-ups

* Increased privacy: encrypt/decrypt inside `vim` using `vim -x`
    - differentiate editor-encryption from normal encryption
    - `vimbox -x`

* Back-end side encription with stored key on client side
    - how to handle already encripted files (two hash tables?)
    - `vimbox -k`

* Other backends e.g. `vimbox /evernote/notes/`
    - mockup back-end for testing
    - `dropbox paper` has an API, unclear how flexible
    - `CloudBlaze` is an alternative to dropbox
    - `evernote` seems accessible

* Set editors used in config

### Future v0.0.6

* Add specific help for commands

* Move all dropbox code to `dropbox client`

* Clean up namespaces of methods

###

* Handle installation in virtualenv
    - local `~/.vimbox/` and `.bash_profile`

* Update autocomplete from vimbox after new register (instead of `source`)

* Proper full installation
    - `setup.py` adds `complete` to `.bash_profile`

* Simulated bash in remote

    vimbox rm /logs/mylog
    vimbox cp /logs/mylog /path/
    vimbox cp /logs/mylog /path/mylog2
    vimbox mv /logs/mylog /path/mylog2

### v0.0.5

* More robust handling of remote behaviours

* Major refactor: isolate remote/local code. Add `pull()`

### v0.0.4

* Fix `vimbox -e /path/to/file` on existing files not allowed

* Major refactor edit() _push() functions probably better than VimBox class

### v0.0.3

* Optional encription on the Dropbox side
    - `vimbox -e /logs/private.log` to encript with password
    - Once created, file works as any other file
    - Display unencripted names locally with `vimbox ls`, in red.
    - Password not visible during input

* Fancy colored outputs print()s
