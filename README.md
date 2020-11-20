# Stacker
This is a Python package uses to stack rectangles in a grid. 

# Setup on Windows

## MongoDB
This package uses MongoDB as database to store the rectangles and grids. To install this on Windows, download the .msi package from: https://www.mongodb.com/try/download/community?tck=docs_server. To be able to use MongoDB with the command line, in the package dropdown menu select .zip. Inside this .zip are the command line tools "mongod" and "mongo".

## Python packages
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

# Run tests
To run the test navigate inside the 2d_rectangle_packing folder and execute the following command:

```
python -m unittest discover tests
```

This should run all the test and show OK for each test

# Useful links
https://askubuntu.com/questions/842592/apt-get-fails-on-16-04-or-18-04-installing-mongodb