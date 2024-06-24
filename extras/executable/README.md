# README

Steps to install PyInstaller and make Executable.

## Overview

- This repository provides instructions for installing PyInstaller and creating an executable to run a server.

## Prerequisites
- Python version 3.9 installed.
- Python Virtual Environment activated.

## How PyInstaller Works

PyInstaller is a powerful tool for converting Python scripts into standalone executable files. It allows you to distribute your Python applications as single, self-contained executables that can be run on different systems without the need for a Python interpreter or any external dependencies. Here's how PyInstaller works:

1. **Analysis Phase**:
   - PyInstaller starts by analyzing your Python script to determine its dependencies. It identifies all the Python modules and external packages that your script imports or uses.

2. **Collecting Dependencies**:
   - Once the analysis is complete, PyInstaller collects all the necessary files and modules. It bundles these dependencies into a single directory, often referred to as the "spec" directory, which is used to create the executable.

3. **Creating the Spec File**:
   - PyInstaller generates a spec file (usually with a .spec extension) that contains detailed information about the project's structure and dependencies. This spec file is used in the build process.

4. **Building the Executable**:
   - Using the spec file as a blueprint, PyInstaller compiles the Python interpreter, your script, and all its dependencies into a single executable file. The resulting executable is self-contained and can run on a target system without needing a separate Python installation.

5. **Customization and Configuration**:
   - PyInstaller allows for customization of the executable's behavior. In your provided command, you included options like `--onefile` to generate a single executable file, `--console` to run the script with a console window, and various `--add-data` options to include additional files and data.

6. **Distribution**:
   - Once the build process is complete, PyInstaller places the generated executable in the "dist" folder.

## Run PyInstaller

- Install PyInstaller
    - Open your terminal.
    - Execute the following command: "Pipenv install Pyinstaller".
- Run PyInstaller
    - In your terminal, use the following command to create the executable. This command includes necessary imports and files for compilation:
    - Command: pyinstaller  --onefile --console webdirect.py --add-data "static;static" --add-data "templates;templates" --add-data "webdirect.ini;." --add-data "key.pem;." --add-data "cert.pem;." --add-data "gclogin.pem;." --add-data ";." --hidden-import engineio.async_drivers.eventlet --hidden-import eventlet.hubs.epolls --hidden-import eventlet.hubs.selects --hidden-import eventlet.hubs.kqueue --hidden-import dns.rdtypes.ANY --hidden-import dns.rdtypes.IN --hidden-import dns.rdtypes.CH --hidden-import dns.rdtypes.dnskeybase --hidden-import dns.asyncbackend --hidden-import dns.dnssec --hidden-import dns.e164 --hidden-import dns.namedict --hidden-import dns.tsigkeyring --hidden-import dns.update --hidden-import dns.version --hidden-import dns.zone --hidden-import dns.asyncquery --hidden-import dns.versioned --hidden-import socketserver --hidden-import http.server --hidden-import threading
    - The executable will be generated in the "dist" folder.
    - NOTE: After making any modifications to the code, ensure that you regenerate the executable by executing the provided command in the terminal.

## Points to consider

- Ensure that the static folder is up-to-date and contains all the required files for WebDirect.
- Confirm the existence of a template folder that contains all the necessary files.
- Verify the presence of a complete "webdirect.ini" file that includes sections for [WEBDIRECT], [LOGGING], and [SERVERS].

## Running the WebDirect Executable?
- To run the executable, choose one of the following methods:
    - Double-click on the "webdirect.exe" file.
    - Open a command prompt in your current directory and enter "webdirect.exe."
