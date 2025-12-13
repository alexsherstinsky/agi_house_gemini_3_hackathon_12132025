"""Dynamic loading utilities copied from conversation_analysis/util.py.

Copied from: platform/conversation_analysis/conversation_analysis/util.py
Date: 2025-12-13
Modified for hackathon project independence
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any


def verify_dynamic_loading_support(
    module_name: str, package_name: str | None = None
) -> None:
    """Verify that a module can be dynamically loaded.

    Args:
        module_name: Possibly relative module name.
        package_name: Optional package name containing the module.
    """
    # noinspection PyUnresolvedReferences
    module_spec: importlib.machinery.ModuleSpec | None
    try:
        # noinspection PyUnresolvedReferences
        module_spec = importlib.util.find_spec(module_name, package=package_name)
    except ModuleNotFoundError:
        module_spec = None

    if not module_spec:
        if not package_name:
            package_name = ""

        message: str = f"""No module named "{package_name + module_name}" could be found in the repository. Please \
make sure that the file, corresponding to this package and module, exists and that dynamic loading of code modules, \
templates, and assets is supported in your execution environment.  This error is unrecoverable.
        """
        raise FileNotFoundError(message)


def import_library_module(module_name: str) -> ModuleType | None:
    """Import a module by name.

    Args:
        module_name: Fully qualified module name.

    Returns:
        Module object or None if it cannot be imported.
    """
    module_obj: ModuleType | None

    try:
        module_obj = importlib.import_module(module_name)
    except ImportError:
        module_obj = None

    return module_obj


def load_class(class_name: str, module_name: str) -> type:
    """Load a class from a module.

    Args:
        class_name: Name of the class to load.
        module_name: Fully qualified module name.

    Returns:
        The class object.

    Raises:
        FileNotFoundError: If the module cannot be found.
        AttributeError: If the class cannot be found in the module.
    """
    if class_name is None:
        raise TypeError("class_name must not be None.")
    if not isinstance(class_name, str):
        raise TypeError("class_name must be a string.")
    if module_name is None:
        raise TypeError("module_name must not be None.")
    if not isinstance(module_name, str):
        raise TypeError("module_name must be a string.")
    try:
        verify_dynamic_loading_support(module_name=module_name)
    except FileNotFoundError:
        raise FileNotFoundError(f"Module not found: {module_name}")

    module_obj: ModuleType | None = import_library_module(module_name=module_name)

    if module_obj is None:
        raise FileNotFoundError(f"Module not found: {module_name}")

    try:
        klass_: Any = getattr(module_obj, class_name)
    except AttributeError:
        raise AttributeError(
            f"Class '{class_name}' not found in module '{module_name}'"
        )

    return klass_

