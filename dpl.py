import os
import csv
import sqlite3
from functools import wraps
from StringIO import StringIO
from flask import Flask, jsonify, request, abort, Response, make_response

app = Flask(__name__)


def getUsername():
    with open(os.path.join(app.root_path, '../data/username'), 'r') as f:
        username = f.read()
    return username


def getPassword():
    with open(os.path.join(app.root_path, '../data/password'), 'r') as f:
        password = f.read()
    return password


app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../data/brothers.db'),
    DEBUG=True,
    USERNAME=getUsername(),
    PASSWORD=getPassword()
))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS brothers (nickname TEXT PRIMARY KEY, name TEXT, big TEXT, year INT)')
    cur.close()
    conn.commit()
    conn.close()


def _get_conn():
    return sqlite3.connect(app.config['DATABASE'])


class Brother:
    def __init__(self, nickname='', name='', big='', year=0):
        self.name = name
        self.nickname = nickname
        self.big = big
        self.year = year
        self.littles = self.getLittles()
        self.weight = self.getWeight()

    def __lt__(self, other):
        return self.weight > other.weight

    def serialize(self):
        obj = {}
        obj['name'] = self.name
        obj['nickname'] = self.nickname
        obj['big'] = self.big
        obj['year'] = self.year
        obj['littles'] = []
        for i in self.littles:
            obj['littles'].append(i.serialize())
        return obj

    def create(self):
        conn = _get_conn()
        cur = conn.cursor()
        t = (self.nickname, self.name, self.big, self.year)
        cmd = 'INSERT INTO brothers (nickname, name, big, year) VALUES (?, ?, ?, ?)'
        cur.execute(cmd, t)
        cur.close()
        conn.commit()
        conn.close()
        self.littles = self.getLittles()
        return self

    def read(self):
        conn = _get_conn()
        cur = conn.cursor()
        t = (self.nickname,)
        cmd = 'SELECT * FROM brothers WHERE nickname = ?'
        cur.execute(cmd, t)
        data = cur.fetchone()
        cur.close()
        conn.close()
        if data:
            self.__init__(data[0], data[1], data[2], data[3])
            return self
        else:
            return None

    def update(self):
        conn = _get_conn()
        cur = conn.cursor()
        t = (self.name, self.big, self.year, self.nickname)
        cmd = 'UPDATE brothers SET name=?, big=?, year=? WHERE nickname=?'
        cur.execute(cmd, t)
        cur.close()
        conn.commit()
        conn.close()
        self.littles = self.getLittles()
        return self

    def delete(self):
        conn = _get_conn()
        cur = conn.cursor()
        t = (self.nickname,)
        cmd = 'DELETE FROM brothers WHERE nickname = ?'
        cur.execute(cmd, t)
        cur.close()
        conn.commit()
        conn.close()
        return True

    def getLittles(self):
        conn = _get_conn()
        cur = conn.cursor()
        t = (self.nickname,)
        cmd = 'SELECT * FROM brothers WHERE big = ?'
        cur.execute(cmd, t)
        res = cur.fetchall()
        cur.close()
        conn.close()
        littles = []
        for i in res:
            littles.append(Brother(i[0], i[1], i[2], i[3]))
        return self.sortLittles(littles)

    def sortLittles(self, littles):
        res = []
        littles.sort()
        for i, val in enumerate(littles):
            if i % 2:
                res.insert(0, val)
            else:
                res.append(val)
        return res

    def getWeight(self):
        weight = 1
        for i in self.littles:
            weight += i.weight
        return weight


def getAllBrothers():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM brothers')
    brothers = cur.fetchall()
    cur.close()
    conn.close()
    return brothers


@app.route('/dpl/search/<q>', methods=['GET'])
def search(q):
    conn = _get_conn()
    cur = conn.cursor()
    q = '%' + q + '%'
    t = (q, q, q, q)
    cmd = 'SELECT * FROM brothers WHERE nickname LIKE ? OR name LIKE ? OR big LIKE ? OR year LIKE ?'
    cur.execute(cmd, t)
    allBrothers = cur.fetchall()
    cur.close()
    conn.close()
    brothers = []
    for bro in allBrothers:
        brothers.append(Brother(bro[0], bro[1], bro[2], bro[3]).serialize())
    res = {}
    res['brothers'] = brothers
    return jsonify(res)


@app.route('/dpl/brothers/', methods=['GET'])
def readAll():
    allBrothers = getAllBrothers()
    brothers = []
    for bro in allBrothers:
        brothers.append(Brother(bro[0], bro[1], bro[2], bro[3]).serialize())
    res = {}
    res['brothers'] = brothers
    return jsonify(res)


@app.route('/dpl/brothers/', methods=['POST'])
@requires_auth
def create():
    req = request.get_json()
    nickname = req.get('nickname', '')
    name = req.get('name', '')
    big = req.get('big', '')
    year = req.get('year', '')
    if nickname and name:
        try:
            brother = Brother(nickname, name, big, year).create()
            return jsonify(brother.serialize())
        except Exception:
            abort(500)
    else:
        abort(400)


@app.route('/dpl/import/', methods=['POST'])
@requires_auth
def uploadCsv():
    file = request.files['file']
    ext = os.path.splitext(file.filename)[-1].lower()
    if file is not None and ext == '.csv':
        filestream = csv.DictReader(file)
        brothers = []
        for row in filestream:
            bro = Brother(row['Nickname'], row['Name'], row['Big'], row['Year'])
            if Brother(row['Nickname']).read() is None:
                bro.create()
            else:
                bro.update()
        return readAll()
    else:
        abort(400)


@app.route('/dpl/export/', methods=['GET'])
def downloadCsv():
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Nickname', 'Big', 'Year'])
    for row in getAllBrothers():
        writer.writerow([row[1], row[0], row[2], str(row[3])])
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=brothers.csv'
    return response


@app.route('/dpl/brothers/<nickname>', methods=['GET'])
def readOne(nickname):
    brother = Brother(nickname).read()
    if brother:
        return jsonify(brother.serialize())
    else:
        abort(404)


@app.route('/dpl/brothers/<nickname>', methods=['PUT'])
@requires_auth
def update(nickname):
    brother = Brother(nickname).read()
    if brother:
        req = request.get_json()
        name = req.get('name', '')
        big = req.get('big', '')
        year = req.get('year', '')
        if nickname and name:
            try:
                brother = Brother(nickname, name, big, year).update()
                return jsonify(brother.serialize())
            except Exception:
                abort(500)
        else:
            abort(400)
    else:
        abort(404)


@app.route('/dpl/brothers/<nickname>', methods=['DELETE'])
@requires_auth
def delete(nickname):
    brother = Brother(nickname).read()
    if brother:
        if brother.delete():
            return jsonify('')
        else:
            abort(500)
    else:
        abort(404)


# Special end point for adding littles to a big
# nickname is the nickname of the big
# expects little to be the nickname of the little
@app.route('/dpl/add-little/<nickname>', methods=['PUT'])
@requires_auth
def addLittle(nickname):
    req = request.get_json()
    little = req.get('little', None)
    big = Brother(nickname).read()
    brother = Brother(little).read()
    if big and little and brother:
        try:
            brother.big = nickname
            brother.update()
            return jsonify(big.read().serialize())
        except Exception:
            abort(500)
    else:
        abort(404)


def check_auth(username, password):
    return username == app.config['USERNAME'] and password == app.config['PASSWORD']


def authenticate():
    return Response(
        'Unauthorized', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers['Content-Type'] = 'text/json'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With,Content-Type, Accept, Authorization'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
