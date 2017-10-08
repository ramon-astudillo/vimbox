import yaml


def write_config(file_path, config):
    with open(file_path, 'w') as fid:
        yaml.dump(config, fid, default_flow_style=False)


def read_config(file_path):
    with open(file_path, 'r') as fid:
        config = yaml.load(fid)
    return config


def write_file(file_path, content):
    with open(file_path, 'w') as fid_local:
        fid_local.write(content)


def read_file(file_path):
    with open(file_path, 'r') as fid_local:
        return fid_local.read()
