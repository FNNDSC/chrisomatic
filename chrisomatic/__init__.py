from importlib.metadata import Distribution

_pkg = Distribution.from_name(__package__)
__version__ = _pkg.version
