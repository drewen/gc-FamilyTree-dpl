import os
import dpl
import unittest
import tempfile
import json
from datetime import date
from werkzeug.datastructures import Headers
from base64 import b64encode
from StringIO import StringIO
from copy import deepcopy

Vaporizer = dict(
    name='Andrew Smith',
    nickname='Vaporizer',
    big='McLovin\'',
    year=2014
)
Karu = dict(
    name='Kyle Halstead',
    nickname='Karu',
    big='Vaporizer',
    year=2012
)
Sanctus = dict(
    name='Michael Higgins',
    nickname='Sanctus',
    big='Vaporizer',
    year=2013
)
Dishficks = dict(
    name='Sebastian Espinosa',
    nickname='Dishficks',
    year=2017
)
DumpsterTurtle = dict(
    name='Jeremy Filteau',
    nickname='Dumpster Turtle',
    big='Dishficks',
    # This ensures any lines with Dumpster Turtle are "active" for test purposes
    year=date.today().year
)
DoubleAgent = dict(
    name='Cory Lauer',
    nickname='Double Agent',
    big='Vaporizer',
    year=2013
)

class DplTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, dpl.app.config['DATABASE'] = tempfile.mkstemp()
        dpl.app.config['DEBUG'] = True
        dpl.app.config['TESTING'] = True
        dpl.app.config['USERNAME'] = 'admin'
        dpl.app.config['PASSWORD'] = 'password'
        self.app = dpl.app.test_client()
        self.auth = {'Authorization': 'Basic ' + b64encode('admin:password')}
        dpl.init_db()

    def tearDown(self):
        os.unlink(dpl.app.config['DATABASE'])

    def test_empty_db(self):
        response = self.app.get('/dpl/brothers/')
        expected = {}
        expected['brothers'] = []
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/Vaporizer')
        assert response.status_code == 404

    def test_auth(self):
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json'
        )
        expected = 401
        assert response.status_code == expected
        response = self.app.put(
            '/dpl/add-little/Vaporizer',
            data=json.dumps(dict(little='Dishficks')),
            content_type='application/json'
        )
        assert response.status_code == expected

    def test_add_brother(self):
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        expected = deepcopy(Vaporizer)
        expected['littles'] = []
        expected['activeBranch'] = False
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/brothers/Vaporizer')
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/brothers/')
        expected = dict(brothers=[expected])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_update_brother(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        VaporizerEditted = dict(
            name='Andrew Smorf',
            nickname='Vaporizer',
            big='Steve',
            year=2010,
            littles=[],
            activeBranch=False
        )
        response = self.app.put(
            '/dpl/brothers/Vaporizer',
            data=json.dumps(VaporizerEditted),
            content_type='application/json',
            headers=self.auth
        )
        expected = VaporizerEditted
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/brothers/Vaporizer')
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_delete_brother(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.delete(
            '/dpl/brothers/Vaporizer',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/')
        expected = {}
        expected['brothers'] = []
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_littles(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/Vaporizer')
        expected = deepcopy(Vaporizer)
        expected['activeBranch'] = False
        expected['littles'] = [deepcopy(Karu), deepcopy(Sanctus)]
        expected['littles'][0]['littles'] = []
        expected['littles'][0]['activeBranch'] = False
        expected['littles'][1]['littles'] = []
        expected['littles'][1]['activeBranch'] = False
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_littles_with_active_branch(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Dishficks),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(DumpsterTurtle),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/Vaporizer')
        # Vaporizer, Dishficks, and Dumpster Turtle are active due to Dumpster Turtle; Sanctus is inactive
        expected = deepcopy(Vaporizer)
        expected['activeBranch'] = True
        expected['littles'] = [deepcopy(Dishficks), deepcopy(Sanctus)]
        expectedDumpsterTurtle = deepcopy(DumpsterTurtle)
        expectedDumpsterTurtle['littles'] = []
        expectedDumpsterTurtle['activeBranch'] = True
        expected['littles'][0]['littles'] = [expectedDumpsterTurtle]
        expected['littles'][0]['activeBranch'] = True
        expected['littles'][1]['littles'] = []
        expected['littles'][1]['activeBranch'] = False
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_add_little(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Dishficks),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/Vaporizer')
        expected = deepcopy(Vaporizer)
        expected['littles'] = []
        expected['activeBranch'] = False
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.put(
            '/dpl/add-little/Vaporizer',
            data=json.dumps(dict(little='Dishficks')),
            content_type='application/json',
            headers=self.auth
        )
        expected['littles'] = [Dishficks]
        expected['littles'][0]['littles'] = []
        expected['littles'][0]['big'] = 'Vaporizer'
        expected['littles'][0]['activeBranch'] = False
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_change_nickname(self):
        # Add a brother and a little
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.put(
            '/dpl/brothers/Vaporizer',
            data=json.dumps(dict(nickname='Vaporizo')),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 200
        KaruEditted = dict(
            name='Kyle Halstead',
            nickname='Karu',
            big='Vaporizo',
            year=2012,
            littles=[],
            activeBranch=False
        )
        VaporizerEditted = dict(
            name='Andrew Smith',
            nickname='Vaporizo',
            big='McLovin\'',
            year=2014,
            littles=[KaruEditted],
            activeBranch=False
        )
        assert json.loads(response.data) == VaporizerEditted
        response = self.app.get('/dpl/brothers/Karu')
        assert response.status_code == 200
        assert json.loads(response.data) == KaruEditted
        # Brother by old name no longer exists
        response = self.app.get('/dpl/brothers/Vaporizer')
        assert response.status_code == 404


    def test_sort_littles(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Dishficks),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(DumpsterTurtle),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(DoubleAgent),
            content_type='application/json',
            headers=self.auth
        )
        self.app.put(
            '/dpl/add-little/Vaporizer',
            data=json.dumps(dict(little='Dishficks')),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/Vaporizer')
        expected = deepcopy(Vaporizer)
        expKaru = deepcopy(Karu)
        expKaru['littles'] = []
        expKaru['activeBranch'] = False
        expSanctus = deepcopy(Sanctus)
        expSanctus['littles'] = []
        expSanctus['activeBranch'] = False
        expDumpsterTurtle = deepcopy(DumpsterTurtle)
        expDumpsterTurtle['littles'] = []
        expDumpsterTurtle['activeBranch'] = True
        expDoubleAgent = deepcopy(DoubleAgent)
        expDoubleAgent['littles'] = []
        expDoubleAgent['activeBranch'] = False
        expDishficks = deepcopy(Dishficks)
        expDishficks['littles'] = [expDumpsterTurtle]
        expDishficks['activeBranch'] = True
        # heaviest in the middle, other two sorted by insertion order around center
        expected['littles'] = [expDoubleAgent, expDishficks, expSanctus, expKaru]
        expected['activeBranch'] = True
        assert json.loads(response.data) == expected
        self.app.delete(
            '/dpl/brothers/Sanctus',
            headers=self.auth
        )
        response = self.app.get('/dpl/brothers/Vaporizer')
        expected['littles'] = [expKaru, expDishficks, expDoubleAgent]
        assert json.loads(response.data) == expected

    def test_search_with_query(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?q=Vapor')
        expected = dict(brothers=[Vaporizer, Karu, Sanctus])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?q=201')
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?q=Andr')
        assert response.status_code == 200
        expected = dict(brothers=[Vaporizer])
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?q=McL')
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_search_with_year(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?year=201')
        expected = dict(brothers=[Vaporizer, Karu, Sanctus])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?year=2014')
        assert response.status_code == 200
        expected = dict(brothers=[Vaporizer])
        assert json.loads(response.data) == expected

    def test_search_with_big(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?big=i')
        expected = dict(brothers=[Vaporizer, Karu, Sanctus])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?big=McL')
        assert response.status_code == 200
        expected = dict(brothers=[Vaporizer])
        assert json.loads(response.data) == expected

    def test_search_with_big_and_year(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?big=Vaporizer&year=2012')
        expected = dict(brothers=[Karu])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_search_with_big_year_and_query(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(DoubleAgent),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?big=Vaporizer&year=2013&q=Sanc')
        expected = dict(brothers=[Sanctus])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_search_with_sort(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Sanctus),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/search?sort=nickname')
        expected = dict(brothers=[Karu, Sanctus, Vaporizer])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?sort=-nickname')
        expected = dict(brothers=[Vaporizer, Sanctus, Karu])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

        response = self.app.get('/dpl/search?sort=big&sort=+nickname')
        expected = dict(brothers=[Vaporizer, Karu, Sanctus])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_csv_upload(self):
        csvString = 'Name,Nickname,Big,Year\nAndrew Smith,Vaporizer,McLovin\',2014\nKyle Halstead,Karu,Vaporizer,2012'
        response = self.app.post('/dpl/import/')
        assert response.status_code == 401
        response = self.app.post('/dpl/import/', headers=self.auth)
        assert response.status_code == 400
        response = self.app.post(
            '/dpl/import/',
            data=dict(file=(StringIO(csvString), 'upload.txt')),
            content_type='multipart/form-data',
            headers=self.auth
        )
        assert response.status_code == 400
        response = self.app.post(
            '/dpl/import/',
            data=dict(file=(StringIO(csvString), 'upload.csv')),
            content_type='multipart/form-data',
            headers=self.auth
        )
        expKaru = deepcopy(Karu)
        expKaru['littles'] = []
        expKaru['activeBranch'] = False
        expVaporizer = deepcopy(Vaporizer)
        expVaporizer['littles'] = [expKaru]
        expVaporizer['activeBranch'] = False
        expected = dict(brothers=[expVaporizer, expKaru])
        assert response.status_code == 200
        assert response.data == 'All rows imported successfully!'
        response = self.app.get('/dpl/brothers/')
        assert json.loads(response.data) == expected
        csvString = 'Nickname,Name,Year,Big\nVaporizer,Andrew Smoth,2014,McLovin\''
        response = self.app.post(
            '/dpl/import/',
            data=dict(file=(StringIO(csvString), 'upload.csv')),
            content_type='multipart/form-data',
            headers=self.auth
        )
        expVaporizer['name'] = 'Andrew Smoth'
        expected = dict(brothers=[expVaporizer, expKaru])
        assert response.status_code == 200
        assert response.data == 'All rows imported successfully!'
        response = self.app.get('/dpl/brothers/')
        assert json.loads(response.data) == expected

    def test_csv_download(self):
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        response = self.app.get('/dpl/export/')
        assert response.status_code == 200
        expected = ['Name,Nickname,Big,Year',
                    'Andrew Smith,Vaporizer,McLovin\',2014']
        assert response.data.splitlines() == expected

    def test_bad_request(self):
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(dict(nickname='Vaporizer')),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 400
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(dict(name='Andrew Smith')),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 400
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )

    def test_resource_not_found(self):
        response = self.app.get(
            '/dpl/brothers/spam',
            headers=self.auth
        )
        assert response.status_code == 404
        response = self.app.put(
            '/dpl/brothers/spam',
            headers=self.auth
        )
        assert response.status_code == 404
        response = self.app.delete(
            '/dpl/brothers/spam',
            headers=self.auth
        )
        assert response.status_code == 404
        response = self.app.put(
            '/dpl/add-little/spam',
            data=json.dumps(dict(little='Dishficks')),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 404

    def test_method_not_allowed(self):
        response = self.app.post('/dpl/brothers/spam')
        assert response.status_code == 405
        response = self.app.put('/dpl/brothers/')
        assert response.status_code == 405
        response = self.app.delete('/dpl/brothers/')
        assert response.status_code == 405

    def test_server_error(self):
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Karu),
            content_type='application/json',
            headers=self.auth
        )
        os.chmod(dpl.app.config['DATABASE'], 0400)
        response = self.app.delete(
            '/dpl/brothers/Vaporizer',
            headers=self.auth
        )
        assert response.status_code == 500
        response = self.app.put(
            '/dpl/brothers/Vaporizer',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 500
        response = self.app.post(
            '/dpl/brothers/',
            data=json.dumps(Vaporizer),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 500
        response = self.app.put(
            '/dpl/add-little/Vaporizer',
            data=json.dumps(dict(little='Karu')),
            content_type='application/json',
            headers=self.auth
        )
        assert response.status_code == 500

        csvString = 'Name,Nickname,Big,Year\nAndrew Smith,Vaporizer,McLovin\',2014\nSebastian Espinosa,Dishficks,Vaporizer,2017'
        response = self.app.post(
            '/dpl/import/',
            data=dict(file=(StringIO(csvString), 'upload.csv')),
            content_type='multipart/form-data',
            headers=self.auth
        )
        expected = '\n'.join([
            'Errors found with this import:',
            'attempt to write a readonly database',
            'attempt to write a readonly database'])
        assert response.data == expected

if __name__ == '__main__':
    unittest.main()
