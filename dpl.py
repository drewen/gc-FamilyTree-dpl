from flask import Flask, jsonify, request, abort
import sqlite3
import os


app = Flask(__name__)


app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'brothers.db'),
    DEBUG=False
))


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('CREATE TABLE brothers (nickname TEXT PRIMARY KEY, name TEXT, big TEXT, year INT)')
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

    def serialize(self):
        obj = {}
        obj['name'] = self.name
        obj['nickname'] = self.nickname
        obj['big'] = self.big
        obj['year'] = self.year
        obj['littles'] = self.littles
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
        cmd = 'SELECT nickname FROM brothers WHERE big = ?'
        cur.execute(cmd, t)
        res = cur.fetchall()
        cur.close()
        conn.close()
        littles = []
        for i in res:
            littles.append(i[0])
        return littles


def getAllBrothers():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM brothers')
    brothers = cur.fetchall()
    cur.close()
    conn.close()
    return brothers


def search(q):
    conn = _get_conn()
    cur = conn.cursor()
    q = '%' + q + '%'
    t = (q, q, q)
    cmd = 'SELECT * FROM brothers WHERE nickname LIKE ? OR name LIKE ? OR year LIKE ?'
    cur.execute(cmd, t)
    res = cur.fetchall()
    cur.close()
    conn.close()
    return res


@app.route('/dpl/', methods=['GET'])
def readAll():
    allBrothers = getAllBrothers()
    brothers = []
    for bro in allBrothers:
        brothers.append(Brother(bro[0], bro[1], bro[2], bro[3]).serialize())
    res = {}
    res['brothers'] = brothers
    return jsonify(res)


@app.route('/dpl/', methods=['POST'])
def create():
    req = request.get_json()
    nickname = req.get('nickname', '')
    name = req.get('name', '')
    big = req.get('big', '')
    year = req.get('year', '')
    if nickname and name and year:
        try:
            brother = Brother(nickname, name, big, year).create()
            return jsonify(brother.serialize())
        except Exception:
            abort(500)
    else:
        abort(400)


@app.route('/dpl/<nickname>', methods=['GET'])
def readOne(nickname):
    brother = Brother(nickname).read()
    if brother:
        return jsonify(brother.serialize())
    else:
        abort(404)


@app.route('/dpl/<nickname>', methods=['PUT'])
def update(nickname):
    brother = Brother(nickname).read()
    if brother:
        req = request.get_json()
        nickname = req.get('nickname', '')
        name = req.get('name', '')
        big = req.get('big', '')
        year = req.get('year', '')
        if nickname and name and year:
            try:
                brother = Brother(nickname, name, big, year).update()
                return jsonify(brother.serialize())
            except Exception:
                abort(500)
        else:
            abort(400)
    else:
        abort(404)


@app.route('/dpl/<nickname>', methods=['DELETE'])
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
