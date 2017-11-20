VimBox
======

`VimBox` allows you to manually/programatically sync notes/logs across machines
while having as few files as possible locally (even none). Current features are

* No need for the dropbox client (uses the Python API v2)

* File browsing autocomplete with `TAB` as if folders were local

* Optional removal of local files after pushing to remote

* Offline mode keeps all functionalities

* Merge of local and remote discrepancies through `vimdiff`

* Importable methods to use in other modules

Upcoming v0.0.3

* Optional encription on the Dropbox side

Upcoming v0.0.3?

* Basic command line emulation on dropbox `ls` `mv` `rm`

# Examples

Create a new file on dropbox or register locally a file created on other
machine

    vimbox -f /path/to/file

This will open a normal vim session, upon closing the content will be pushed to
dropbox a local copy is kept by default but this can be unselected.

Edit an exiting file on dropbox

    vimbox /path/to/file

If the local and remote copies differ `vimdiff` will be called instead of
`vim`. Default is allways overwrite local with remote (right side)

Browse files using

    vimbox / + <TAB>

will autocomplete using local cache of registered folders. You can also use
`vimbox /path/` or `vimbox ls /path/` to browse remote folder content. In
offline mode this will use the local cache

# Install

## Install the python module

Clone

    git clone git@gitlab.com:ramon-astudillo/vimbox.git
    sudo pip install vimbox/

Upgrade after version change

    sudo pip install vimbox/ --upgrade

## Create App on Dropbox

Create the vimbox app

    https://www.dropbox.com/developers/apps/create

    Dropbox API
    Full Dropbox - Access ...
    Name vimbox

Generate Acess token, store in .env

    DROPBOX_TOKEN=<token>

Get dropbox directory tree

https://stackoverflow.com/questions/31485418/build-directory-tree-from-dropbox-api#31487098

To get folder autocomplete

    complete -W "$(vimbox cache)" 'vimbox'

# Troubleshooting

In OSx with macports, entry_points get installed in a folder not in the PATH.
It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /usr/bin/vimbox

# Versions

Roadmap

* Proper paths for temporary files

* wrapper around vim (tunnel all options)
    :( forces to sync files by separate, big change of flow. Unfrequent use

* Update autocomplete from vimbox after new register (instead of `source`)

* pipes `cat mylog | vimbox pipe -f /logs/mylog` and `vimbox cat /logs/mylog`

* File properties model to allow encripting folders or having files with no
  local copy

* Register dropbox app on first run

* `vimbox sync` to sync entire cache

* edit() _push() functions probably better than VimBox class 
    - config should be read once in import 
    - Info that the user can screw-up (cache, hashes) should not be on config

* simulated bash `vimbox rm /logs/mylog`, `vimbox cp /logs/mylog`

### Future 0.0.3

* File encription, see `feature/add-encription` ...
    - `vimbox -e /logs/private.log`

* Fancy colored outputs print()s  ... Done
