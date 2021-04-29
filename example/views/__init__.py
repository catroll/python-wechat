import importlib
import os

from flask import Blueprint, current_app

MODULES = []
__all__ = 'MODULES', 'initialize'


def initialize():
    for i in os.listdir(os.path.dirname(__file__)):
        if i.startswith('_') or not i.endswith('.py'):
            continue
        mod = importlib.import_module('views.' + i[:-3], 'views')
        if mod in MODULES:
            continue
        MODULES.append(mod)
        current_app.register_blueprint(getattr(mod, 'app'))
        if hasattr(mod, 'initialize'):
            getattr(mod, 'initialize')()
