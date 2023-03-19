from src.sniffer.network import launch_in_thread
from src.mitm.mitm import launch_mitm
from src.modules.base import DofusModule
import importlib


class Manager:
    def __init__(self, modules, type="sniffer"):
        self.modules = modules
        self.current_module: DofusModule = None
        self.stop = None
        self.type = type

    def set_current_module(self, module, class_name):
        module_file = importlib.import_module(f"src.modules.{module}")
        module_class = getattr(module_file, class_name)
        self.current_module = module_class()
        return "ok"

    def run(self):
        if self.type == "sniffer":
            self.stop = launch_in_thread(self.current_module.handle_packet)
            print("Sniffer launched")
        elif self.type == "attach":
            self.stop = launch_mitm(self.current_module.handle_packet)
            print("Bridge launched")

    def stop(self):
        if self.stop is not None:
            self.stop()

    def switch_type(self):
        if self.stop is not None:
            self.stop()

        if self.type == "sniffer":
            self.type = "attach"
        else:
            self.type = "sniffer"

        print(f"Type set to {self.type}")
