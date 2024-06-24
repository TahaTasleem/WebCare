# WebDirect

# README

Steps to get development of this application up and running.

## What is this repository for?

- Provide a web-based replacement for WinGem.

## How do I get set up?

- Install and configure [Python version 3.9](https://www.python.org/downloads/)
  - Install [virtualenv](https://virtualenv.pypa.io/) - [package](https://pypi.python.org/pypi/virtualenv)
- Install and configure [VS Code](https://code.visualstudio.com/)
  - Install VS Code Extensions
    - Required
      - [Python language extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
      - [Beautify](https://marketplace.visualstudio.com/items?itemName=HookyQR.beautify)
    - Recommended
      - [Code Outline](https://marketplace.visualstudio.com/items?itemName=patrys.vscode-code-outline)
      - [Local History](https://marketplace.visualstudio.com/items?itemName=xyz.local-history)
  - Configuration
- Install Node.js
  - Install Node packages
    - In the root directory of project
    - npm install
- Install and Configure Virtual Environment
  - From project folder
    - Create new virtual environment
      - virtualenv .pyenv
    - Install Requirements
      - pipenv install --dev
  - In VS Code
    - Open project
    - Open command palette
    - Run "Reload Window"
- How to run tests
  - Unit Tests
    - VS Code
      - Click "Run Tests" in status bar of IDE (uses nose, not nose2)
    - Standard (from Terminal)
      - nose2 (from project root)
    - Coverage (from Terminal)
      - nose2 --with-coverage --coverage-report html
- Deployment instructions
  - Reference:
    - [Packaging and Distributing Projects](https://packaging.python.org/tutorials/distributing-packages/)
    - [Hosting your own simple repository](https://packaging.python.org/guides/hosting-your-own-index/)
    - [Installing from other Indexes](https://packaging.python.org/tutorials/installing-packages/#installing-from-other-indexes)
  - Ensure latest build tools are installed:
    - python -m pip install --upgrade pip setuptools wheel
  - Update version # in setup.py
  - Make any other changes, if necessary, to:
    - [setup.py](https://github.com/pypa/sampleproject/blob/master/setup.py)
    - [setup.cfg](https://github.com/pypa/sampleproject/blob/master/setup.cfg)
  - Build
    - Build a Test Install (optional)
      - Can open the .tar.gz file and verify the components it selected
      - python setup.py sdist
    - Build Python 3 install
      - From the Python 3 virtual environment:
        - python setup.py bdist_wheel
  - Deploy
    - From the dist folder, copy webdirect-\*.tar.gz to repository on WebLive
      - \\\\cmwls-pweblive.csi.campana.com\\inetpub\\axial.campana.com\\pydist\\webdirect
  - Install
    - Package can now be installed in a destination location by executing the following command from the destination Python environment:
      - pip install webdirect --extra-index-url https://axial.campana.com/pydist

## Changing JS/CSS

Tasks available under Terminal > Run Task in VS Code

  - minify webdirect.css and webdirect.js for production
    - npm: gulp
  - Compile React components - dev
    - npm: devbuild
  - Compile React components - prod (minified)
    - npm: prodbuild
    
## Contribution guidelines

- Writing tests
- Code review
- Other guidelines

## Who do I talk to?

- Clayton Boucher
- Jeff Holtham
- Aaron Cartier
- Mike Hulls

## Helpful Links

- [VS Code Python Help](https://code.visualstudio.com/docs/languages/python)
- [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo/src)
