from importlib.metadata import Distribution, PackageNotFoundError


try:
    _pkg = Distribution.from_name(__package__)
    __version__ = _pkg.version
except PackageNotFoundError:
    __version__ = "unknown"
