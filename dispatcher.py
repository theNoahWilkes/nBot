"""
Plugin dispatcher.

Discovers all modules in the plugins/ directory and calls each one's handle()
function in alphabetical order until one returns a non-None response.

Plugin interface:
    def handle(text: str, sender: dict, space: str) -> str | None:
        ...

- text:   the raw message text from the user
- sender: the sender object from the Google Chat event
          (keys: name, displayName, email, type)
- space:  the space resource name, e.g. "spaces/AAAA1234"

Return a string to reply, or None to pass to the next plugin.
"""

import importlib
import logging
import pkgutil
import plugins

logger = logging.getLogger(__name__)

_plugins: list = []


def _load_plugins() -> None:
    for finder, name, _ in pkgutil.iter_modules(plugins.__path__):
        module_name = f"plugins.{name}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "handle"):
                _plugins.append(module)
                logger.info("Loaded plugin: %s", module_name)
            else:
                logger.warning("Plugin %s has no handle() function, skipping", module_name)
        except Exception:
            logger.exception("Failed to load plugin: %s", module_name)


_load_plugins()


def dispatch(text: str, sender: dict, space: str) -> str | None:
    for plugin in _plugins:
        try:
            result = plugin.handle(text, sender, space)
            if result is not None:
                logger.info("Plugin %s handled message", plugin.__name__)
                return result
        except Exception:
            logger.exception("Plugin %s raised an exception", plugin.__name__)
    return None
