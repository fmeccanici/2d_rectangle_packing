# Stacker
This is a Python package used to stack rectangles in a grid in 2D, which is tested on Python 3.9.0. 

## Setup on Windows
First this package should be cloned somewhere on your harddisk:
```
git clone https://github.com/fmeccanici/2d_rectangle_packing.git
```
Then proceed with the following steps.

### MongoDB
This package uses MongoDB as database to store the rectangles and grids. To install this on Windows, download the .msi package from: https://www.mongodb.com/try/download/community?tck=docs_server. To be able to use MongoDB with the command line, in the package dropdown menu select .zip. Inside this .zip are the command line tools "mongod" and "mongo".

### Python packages
After MongoDB is present, the required Python dependencies should be installed. Create a virtual environment inside the 2d_rectangle_packing folder:
```
python -m venv venv
```
Then activate this virtual environment:
```
.\venv\Scripts\activate
```
And install the required Python packages using the following command:
```
pip install -r requirements.txt
```

### Running the application 
To run the application double click on the Stacker shortcut present inside the 2d_rectangle_packing folder, which starts the GUI. This shortcut can be moved to the Desktop for convenience. On the desktop a folder "paklijsten" should be created, where the paklijst is stored that is used to load the orders in the GUI.

To start the GUI via the command line "cd" into the 2d_rectangle_packing folder and execute:

```
python main.py
```
## Run tests
To run the test navigate inside the 2d_rectangle_packing folder and execute the following command:

```
python -m unittest discover tests
```

This should run all the test and show OK for each test. To run a single test use, e.g. test_stacker.py, execute the following command:
```
python -m unittest tests.test_stacker
```


## Useful links
https://askubuntu.com/questions/842592/apt-get-fails-on-16-04-or-18-04-installing-mongodb