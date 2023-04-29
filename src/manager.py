from src.sniffer.network import launch_in_thread
from src.mitm.mitm import launch_mitm
from src.modules.base import DofusModule
from src.mitm.mitm import bridges
from src.sniffer.check import check_for_update
import importlib


class Manager:
    def __init__(self, modules, type="sniffer"):
        self.modules = modules
        self.current_module: DofusModule = None
        self.stop = None
        self.type = type
        self.bridge = None
        check_for_update()

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
            httpd, bridges = launch_mitm(self.current_module.handle_packet)
            self.stop = httpd.shutdown
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

    def send_message(self, message):
        if self.bridge is None and len(bridges) > 0:
            self.bridge = bridges[0]

        if self.bridge is not None:
            self.bridge.send_message(message)