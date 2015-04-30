import os
import dpl
import unittest
import tempfile
import json


Vaporizer = dict(name='Andrew Smith', nickname='Vaporizer', big='McLovin', year=2014)
Karu = dict(name='Kyle Halstead', nickname='Karu', big='Vaporizer', year=2012)
Sanctus = dict(name='Michael Higgins', nickname='Sanctus', big='Vaporizer', year=2013)
Dishficks = dict(name='Sebastian Espinosa', nickname='Dishficks', year=2017)


class DplTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, dpl.app.config['DATABASE'] = tempfile.mkstemp()
        dpl.app.config['DEBUG'] = True
        dpl.app.config['TESTING'] = True
        self.app = dpl.app.test_client()
        dpl.init_db()

    def tearDown(self):
        os.unlink(dpl.app.config['DATABASE'])

    def test_empty_db(self):
        response = self.app.get('/dpl/')
        expected = {}
        expected['brothers'] = []
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/Vaporizer')
        assert response.status_code == 404

    def test_add_brother(self):
        response = self.app.post('/dpl/', data=json.dumps(Vaporizer), content_type='application/json')
        expected = Vaporizer
        expected['littles'] = []
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/Vaporizer')
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.get('/dpl/')
        expected = dict(brothers=[expected])
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_delete_brother(self):
        self.app.post('/dpl/', data=json.dumps(Vaporizer), content_type='application/json')
        self.app.delete('/dpl/Vaporizer')
        response = self.app.get('/dpl/')
        expected = {}
        expected['brothers'] = []
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_littles(self):
        self.app.post('/dpl/', data=json.dumps(Vaporizer), content_type='application/json')
        self.app.post('/dpl/', data=json.dumps(Karu), content_type='application/json')
        self.app.post('/dpl/', data=json.dumps(Sanctus), content_type='application/json')
        response = self.app.get('/dpl/Vaporizer')
        expected = Vaporizer
        expected['littles'] = ['Karu', 'Sanctus']
        assert response.status_code == 200
        assert json.loads(response.data) == expected

    def test_add_little(self):
        self.app.post('/dpl/', data=json.dumps(Vaporizer), content_type='application/json')
        response = self.app.post('/dpl/', data=json.dumps(Dishficks), content_type='application/json')
        response = self.app.get('/dpl/Vaporizer')
        expected = Vaporizer
        expected['littles'] = []
        assert response.status_code == 200
        assert json.loads(response.data) == expected
        response = self.app.put('/dpl/add-little/Vaporizer', data=json.dumps(dict(little='Dishficks')), content_type='application/json')
        expected['littles'] = ['Dishficks']
        assert response.status_code == 200
        assert json.loads(response.data) == expected


if __name__ == '__main__':
    unittest.main()
