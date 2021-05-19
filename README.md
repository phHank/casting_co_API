# Casting Co API: Movies and Actors
A web app which allows the employees, with three levels of varying privileges, of a film production company to create, read, update, or delete the movies and actors with which the company is engaged. 

## Getting Started

##### Testing Heroku app

Go to `https://capstoneph.herokuapp.com/` and log in using one of following accounts:

email                     password
`assistant@fakemail.kz`  `Assistant1`
`director@fakemail.kz`   `Director1`
`executive@fakemail.kz`  `Executive1`

You can then use the Postam suite `api.postman_collection.json` to test the endpoints. Depending on which account you are running and which endpoints you would like to test, you may have to provide Postman with a different JWT which corresponds to that level of access. The relevant JWT for each account can be retrieved from `https://capstoneph.herokuapp.com/jwt` after successfully logging in.

### Running the local app: Installing Dependencies

#### Python 3.7

Follow instructions to install python 3.7 for your platform in the [python docs](https://www.python.org/downloads/release/python-372/)

#### Virtual Enviornment

We recommend working within a virtual environment whenever using Python for this project. This keeps your dependencies for each project separate and organaized. Instructions for setting up a virual enviornment for your platform can be found in the [python docs](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

#### PIP Dependencies

Once you have your virtual environment setup and running, install dependencies by naviging to the `/files` directory and running:

```bash
pip install -r requirements.txt
```

This will install all of the required packages we selected within the `requirements.txt` file.

## Running the server locally

Firstly, you will have to provide environment variables in `setup.sh`.

Required variables in "setup.sh" are:
```bash
export DATABASE_URL='YOUR//LOCAL:DATABASE@URI:GOES/HERE'
export TEST_DATABASE_URL='YOUR//LOCAL:TEST_DATABASE@URI:GOES/HERE' # (If you prefer to use the 'dev' database for tests too, set this variable equal to the same URI as DATABASE_URI)
export AUTH0_DOMAIN='app_name.region.auth0.com' # (set app_name and region to the same as those defined in your Auth0 dashboard - https://manage.auth0.com/dashboard/)
export ALGORITHMS=['RS256'] # (or same as defined in your Auth0 settings)
export API_AUDIENCE='audience' # (set api audience to the same as those defined in your Auth0 dashboard - https://manage.auth0.com/dashboard/)
export CLIENT_ID='abde12345ghijklmnop' # (set as same as client id as defined in your Auth0 dashboard - https://manage.auth0.com/dashboard/)
export LOGIN_URI='http://localhost:8080/login' # (set same as those defined in your Auth0 dashboard - https://manage.auth0.com/dashboard/)
```

```bash
cd casting_co_API
. setup.sh
flask db upgrade
python app.py
```

The command `flask db upgrade` only needs to be ran the first time to setup the schema and seed the database.

Go to `http://localhost:8080/` in a browser to log into the app. 


## Testing

The local and heroku GET endpoints `/actors` `/actors/<id>` `/movies` `/movies/<id>` and `/jwt` can be accessed and tested in browser afer log in. The remaiming endpoints can be tested with a Postman suite or by running `test_app.py`, which can be configured first for testing on a test database should that be necessary **NB** If using a test database; don't forget to run `flask db migrate && flask db upgrade` to setup and seed the test database before running the tests. 

Run the following command to test the local POST, PATCH and DELETE endpoints:

```bash
. setup.sh
python test_app.py
```

You will be prompted to give a access level, either `assistant, director, or executive`. Then a corresponding and valid JWT will be requested, which can be retrieved by going to `/jwt` after logging in either locally or via Heroku.  

24 tests in total run to test the endpoints for expected behaviour and errors. To test with a different access level rerun the test and provide a valid JWT which correspondes to the newly chosen access level. 