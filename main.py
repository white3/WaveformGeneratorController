import os

import pyvisa

from controllers.controller import Controller
from views.gui import AppGUI
from views.web import WebServer


def build_resources():
    rm = pyvisa.ResourceManager()
    return rm.list_resources()


if __name__ == "__main__":
    resources = build_resources()
    controller = Controller(resources=resources, 
        control_password=os.getenv("WAVEFORM_CONTROL_PASSWORD", "admin123"))
    web_server = WebServer(controller, 
        host=os.getenv("WAVEFORM_WEB_HOST", "127.0.0.1"), 
        port=int(os.getenv("WAVEFORM_WEB_PORT", "8001")))
    web_address = web_server.start()
    app = AppGUI(controller, web_address=web_address)
    try:
        app.mainloop()
    finally:
        web_server.stop()
