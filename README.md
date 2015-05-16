## Data Persistence Layer/RESTful API for WPI Men's Glee Club Family Tree
#### Setting Up:
#####This assumes you have:
* Python 2.7+
* pip
* git

If you don't, look into getting those...

1. Run `git clone https://github.com/drewen/gc-FamilyTree-dpl`
2. Run `cd FamilyTree-dpl`
2. Run `pip install virtualenv`
3. Run `virtualenv venv`
4. Run `. venv/bin/activate`
5. Run `pip install flask`

#### To start:
1. Make sure virtualenv is active
2. Run `python dpl.py`

Simple as that.

Endpoints:

`/dpl/`:

GET: returns JSON of all brothers in the database

POST: creates a new brother from given parameters and returns the JSON for that brother

`/dpl/<nickname>`:

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

TODO:

[ ] Cleanup readme

[ ] Expose search endpoint

[ ] Add .csv upload

[ ] Add authorization/password security