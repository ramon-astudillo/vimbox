Design ideas

## vimbox.remote.primitives.VimboxClient
- wraps primitives of all the StorageBackEnd
- enforces path format: use / for folders    
- cares about path normalization issues when calling StorageBackEnd 
- provides additional local actions for primitives (create, delete move)
    - calls vimbox.local
- provides cache actions for primitives (add, is in cache, remove)
    - calls vimbox.local
- provides support for encryption
    - calls vimbox.local
    - calls vimbox.crypto
    - provides hash list actions for the primitives (add, is in cache, remove)

## vimbox.remote.primitives.NAME.StorageBackEnd
- wraps original API of service e.g. dropbox, fake-backend
