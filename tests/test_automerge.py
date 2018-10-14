from vimbox.remote.primitives import VimboxClient

client = VimboxClient()
import ipdb;ipdb.set_trace(context=30)

client.edit('/tmp/test', force_creation=True)


