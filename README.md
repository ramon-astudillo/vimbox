VimBox
======

I use vim a lot. I keep a lot of notes across machines. `VimBox` was born as a
cheap way to sync those notes using Dropbox while having a bit more control
than with their client, namely

* Manual sync: `vimbox /notes/cookbook` will download the remote file open it in `vim` and push it to remote upon closing.

* Offline Model: Can work with no internet connection

* Minimal sync: Can be set to keep zero files locally (No offline mode).

* Merge operation: If there are discrepancies between local and remote, `vimdiff` will be called instead of `vim`.

* Path completion: Folder browsing autocomplete with `TAB` as if folders were local using the `complete` command.

* Optional encryption in the Dropbox side with `pycrypto`. Names will be `SHA-1` hashed and content `AES` encrypted.

* `virtualenv` friendly: stores config and file cache inside `virtualenv` folder.

* Comes with the expected `vimbox ls` (`rm` `cp` `mv`, `cat`, `mkdir`)

* Importable methods to use in other modules `from vimbox.remote.primitives import VimboxClient`.

* Editor factored out to replace `vim` and `vimdiff` by other editors

* Works in OSX and Linux, uses Dropbox v2 API (`python 2` and `3` supported).

* `StorageBackEnd` factored out to easily add new ones. Currently has full support for `Dropbox` and a dummy back-end for unit testing.

* Experimental support for a `Dropbox paper` back-end allowing to edit directly from paper URLs

# Examples

Create a new file on Dropbox or register locally a file created on other
machine

    vimbox -f /path/to/file

This will open a normal vim session, upon closing the content will be pushed to
Dropbox a local copy is kept by default but this can be unselected.

Edit an exiting file on Dropbox

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

To create files encrypted on the Dropbox side, use `-e` instead of `-f`

    vimbox -e /path/to/file

you will be prompted for a password. It wont be stored anyway so remember it.
The rest of `vimbox` functionalities are retained after creation but you will
need to input the password for each `_pull` from the remote. Encryption uses
the `pycripto` module.

There is also an experimental `edit from URL` functionality. The aim of this is
not to have an entire file system cached locally but just edit a remote file in
vim given the URL. You can use this as 

    vimbox https://paper.Dropbox.com/doc/Title--ID1-ID2

with an existing Dropbox paper URL. Note that this will not work with "App
Folder" type of permissions, it need full Dropbox access (see install notes
below)

# Install

Install from Github with pip.

    sudo pip install git+https://github.com/ramon-astudillo/vimbox.git

Configure the back-end by calling the program for the first time.

    vimbox setup

The install menu will ask you for a Dropbox access token. Getting this is a
simple process. In any computer with a browser, create a new app on your
Dropbox account by visiting

    https://www.Dropbox.com/developers/apps/create

and use following configuration

* `Dropbox API`

* Both `App folder` and `Full Dropbox` are possible. The former is better for a
  try-out. You will need Full Dropbox for paper URL editing.

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
the virtual environments. The  `activate` script will be used instead of
`.bashrc`. Deleting the `virtualenv` will undo this changes. See next section
for details.

# Develop

To develop the easiest is to use a virtual environment. Vimbox will detect this
and store the `.vimbox` config folder in the same folder where the install is
carried out. As an example

    git clone git@github.com:ramon-astudillo/vimbox.git
    cd vimbox
    virtualenv venv
    source venv/bin/activate
    pip install --editable . 

# Troubleshooting

Not having recent `pip` and `setuptools` can cause install errors. To upgrade
you can use 

    pip install pip setuptools --upgrade

In OSX with `macports`, python entry points get installed in a folder not in
the PATH. It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /Users/$(whoami)/bin/vimbox
    
A similar thing happens if you did a `pip --user` install. You will have too
look for the entry point in `/Users/$(whoami)/.local/` and link it to you `bin`
folder or add it to your `PATH` in the `.bashrc`
