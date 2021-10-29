### Setting up the virtual environment

Run this on the command line to install the virtual environment:

`python3 -m venv env`

Then run these commands to activate the virtual environment and install the required packages:

`source env/bin/activate`
`pip install -r requirements.txt`

The app can then be run using:

`flask run --host=0.0.0.0`

and accessed in the browser as http://db.cse.nd.edu:5000/cse30246/collegecalculator/
