Create the vimbox app

    https://www.dropbox.com/developers/apps/create

    Dropbox API
    Full Dropbox - Access ...
    Name vimbox

Gnerate Acess token, store in .env

    DROPBOX_TOKEN=<token>

Get dropbox directory tree

https://stackoverflow.com/questions/31485418/build-directory-tree-from-dropbox-api#31487098

To get folder autocomplete

    complete -W "$(vimbox -l)" 'vimbox'

# Troubleshooting

In OSx with macports, entry_points get installed in a folder not int the PATH.
It is necessary to manually link this as

    sudo ln -s /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/vimbox /usr/bin/vimbox

# Versions

To think

* Encription, see `feature/add-encription`. Need to design interfacting

Desired

* Register dropbox app on first run

* `vimbox -o` and `vimbox -O`

* Fancy colored outputs print()s
