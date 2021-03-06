## Data Persistence Layer/RESTful API for WPI Men's Glee Club Family Tree
#### Setting Up:
##### This assumes you have:
* Python 2.7+
* pip
* git

If you don't, look into getting those...

1. Run `git clone https://github.com/drewen/gc-FamilyTree-dpl`
2. Run `cd FamilyTree-dpl`
2. Run `pip install virtualenv`
3. Run `virtualenv venv`
4. Run `. venv/bin/activate`
5. Run `pip install -r requirements.txt`
6. Run `python init_db.py`

#### To start:
1. Make sure virtualenv is active
2. Run `python dpl.py`

Simple as that. Now it's running on 127.0.0.1:8051

#### Alternative through docker
1. Ensure you have docker and docker-compose
2. Create a folder for the data outside of the container (ie. `/Users/<your user>/data`)
3. Run `FAMILY_TREE_DB=<path from above> docker-compose up`. Alternatively, set `FAMILY_TREE_DB` to the path set above

#### Endpoints:

`/dpl/brothers/`:

GET: returns JSON of all brothers in the database

POST: creates a new brother from given parameters and returns the JSON for that brother

`/dpl/brothers/<nickname>`:

GET: returns JSON for brother with that nickname

PUT: updates a brother with that nickname and the given parameters

DELETE: deletes a brother with that nickname

`/dpl/add-little/<nickname>`:

PUT: adds the "little" provided via parameters to the brother with that nickname

Any malformed PUTs or POSTs will result in a 400 error, any use of the second two endpoints with a Brother that does not exist with result in a 404 error. Server errors are all 500 errors

A Brother looks like this:
```
{
  name: "Full Name",
  nickname: "Brother's Nickname (REQUIRED, UNIQUE, CANNOT CHANGE)",
  big: "Nickname of Big",
  year: 2014
}
"year" is graduation year
```
