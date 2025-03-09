from views.gui import AppGUI
import pyvisa

if __name__ == "__main__":
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    app = AppGUI(resources)
    app.mainloop()
