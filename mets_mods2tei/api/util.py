from importlib.resources import files

def resource_filename(pkg, fname):
    return files(pkg) / fname
