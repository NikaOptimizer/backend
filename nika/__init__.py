"""Share the nika namespace with independently installed domain packages."""
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
