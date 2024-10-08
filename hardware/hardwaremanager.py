
import sys
import os

from measurement.task_base import Singleton
import importlib
class HardwareManager(metaclass=Singleton):
    _hardware_instances = dict()

    def add(self, name, path_controller, class_controller, args=[], kwargs={}):

        spec = importlib.util.spec_from_file_location(class_controller, path_controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ClassController = getattr(module, class_controller)

        class_controller_name = ClassController.__name__
        if class_controller_name in self._hardware_instances:
            raise ValueError(f"Hardware Controller '{class_controller_name}' already exists")
        
        setattr(self, name, ClassController(*args, **kwargs))
        self._hardware_instances[class_controller_name] = getattr(self, name)

        
    def get(self, name):
        return getattr(self, name)
