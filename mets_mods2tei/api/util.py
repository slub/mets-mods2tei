# cannot use importlib.resources until we move to 3.9+ for importlib.resources.files
import sys
if sys.version_info < (3, 10):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

def resource_filename(pkg, fname):
    return importlib_resources.files(pkg) / fname
