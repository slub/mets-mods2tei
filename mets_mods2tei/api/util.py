from importlib.resources import files

NS = {
    'alto': "http://www.loc.gov/standards/alto/ns-v4#",
    'dv': "http://dfg-viewer.de/",
    'mets': "http://www.loc.gov/METS/",
    'mods': "http://www.loc.gov/mods/v3",
    'tei': "http://www.tei-c.org/ns/1.0",
    'xlink': "http://www.w3.org/1999/xlink",
}
PX = {key: '{' + val + '}' for key, val in NS.items()}


def resource_filename(pkg, fname):
    return files(pkg) / fname
