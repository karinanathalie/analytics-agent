from qpython import qconnection

q = qconnection.QConnection(host="localhost", port=6000)
q.open()
result = q.sendSync('select from trade')
print(result)