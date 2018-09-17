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

* Comes with the expected `vimbox ls` (`rm` `cp` `mv`, `cat`)

* Importable methods to use in other modules `from vimbox.remote import edit, move`.

* Code is thought to replace `vim` and `vimdiff` by other editors

* Code is thought to add backends other than `dropbox` 

* Works in OSX and Linux, uses dropbox v2 API (`python 2` and `3` supported).

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

Install from github with pip

    sudo pip install git+https://github.com/ramon-astudillo/vimbox.git

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

After this is done you will see a control panel for the app. Use the
`Generated access token` button to get an aces token that you can paste into
the install prompt.

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

    git clone git@github.com:ramon-astudillo/vimbox.git
    cd vimbox
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python setup.py develop

# Troubleshooting

In OSX with `macports`, python entry points get installed in a folder not in
the PATH. It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /Users/$(whoami)/bin/vimbox
