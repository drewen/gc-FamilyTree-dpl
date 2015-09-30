import os
import dpl
import unittest
import tempfile
import json
from werkzeug.datastructures import Headers
from base64 import b64encode
from StringIO import StringIO

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
        expected = Vaporizer
        expected['littles'] = []
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/brothers/Vaporizer')
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/brothers/')
        expected = dict(brothers=[expected])
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
        expected = Vaporizer
        expected['littles'] = [Karu, Sanctus]
        expected['littles'][0]['littles'] = []
        expected['littles'][1]['littles'] = []
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
        expected = Vaporizer
        expected['littles'] = []
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
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_search(self):
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
        response = self.app.get('/dpl/search/Vaporizer')
        Karu['littles'] = []
        Sanctus['littles'] = []
        Vaporizer['littles'] = [Karu, Sanctus]
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
        Karu['littles'] = []
        Vaporizer['littles'] = [Karu]
        expected = dict(brothers=[Vaporizer, Karu])
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
        Vaporizer['name'] = 'Andrew Smoth'
        expected = dict(brothers=[Vaporizer, Karu])
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

    def test_bad_endpoints(self):
        response = self.app.post('/dpl/brothers/spam')
        assert response.status_code == 405
        response = self.app.put('/dpl/brothers/')
        assert response.status_code == 405
        response = self.app.delete('/dpl/brothers/')
        assert response.status_code == 405

if __name__ == '__main__':
    unittest.main()
