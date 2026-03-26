# Keysight 33500B Waveform Generator Controller

A Python MVC application for controlling Keysight 33500B waveform generators through a shared backend that can now be accessed by both Tkinter GUI and a built-in Web console.

## Features

- **Dual Access Modes**: Tkinter GUI and built-in Web interface can access the same backend controller at the same time.
- **MVC Preserved**: `models`, `views`, and `controllers` remain separated while both views share the same controller/service logic.
- **Protected Device Control**: Device-changing operations require a control password in both GUI and Web views, while read-only status queries remain open.
- **Online User Count**: The Web dashboard shows current active Web users based on heartbeat sessions.
- **SQLite Config Cache**: Frequently used Keysight 33500B waveform configurations can be saved and loaded from a local SQLite database.
- **Test Sequences**: Run automated test sequences from Excel files.
- **Excel Template**: Generate customizable test sequence templates.

## Project Structure

- `main.py`: Starts the shared controller, background Web server, and Tkinter GUI.
- `controllers/controller.py`: Shared application controller and password-protected device operations.
- `models/waveform_generator.py`: VISA device communication model.
- `models/config_repository.py`: SQLite-backed cached waveform profile repository.
- `models/session_tracker.py`: Tracks active Web sessions.
- `views/gui.py`: Tkinter GUI view.
- `views/web.py`: Built-in HTTP Web view.

## Running

```bash
pip install -r requirements.txt
python main.py
```

Optional environment variables:

- `WAVEFORM_CONTROL_PASSWORD`: overrides the default control password (`admin123`).
- `WAVEFORM_WEB_HOST`: Web server bind host, default `127.0.0.1`.
- `WAVEFORM_WEB_PORT`: Web server bind port, default `8000`.

Then open the GUI normally and visit `http://127.0.0.1:8000` for the Web console.

## Demo

- Python 3.11 | Windows 10 | Keysight 33500B

![image-20260326200745421](.assets\image-20260326200745421.png)
