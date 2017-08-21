const express = require('express'),
  app = express(),
  port = process.env.PORT || 3000;


const path = require('path')
const bodyParser = require('body-parser');
const cassandra = require('cassandra-driver');
const exhbs = require('express-handlebars')


const CASS_IP = '127.0.0.1'
const KEYSPACE = 'auresearch'

const db = new cassandra.Client({contactPoints: [CASS_IP], keyspace: KEYSPACE});
//db.execute('DROP TABLE data')
//db.execute('DROP TABLE towers')
db.execute('CREATE TABLE IF NOT EXISTS data(time text,  MCC text, MNC text, LAC text, Cell_ID text, rxl int, arfcn text, bsic text, lat float, lon float, satellites int, gps_quality int, altitude float, altitude_units text, PRIMARY KEY(time, MCC, MNC, LAC, Cell_ID, rxl)) WITH CLUSTERING ORDER BY (MCC DESC, MNC ASC, LAC DESC, Cell_ID ASC, rxl DESC);');
db.execute('CREATE TABLE IF NOT EXISTS towers(MCC text, MNC text, LAC text, Cell_ID text, mylnikov boolean, lat float, lon float, PRIMARY KEY(Cell_ID, MCC, MNC, LAC));');

app.use(bodyParser.json());

app.engine('.hbs', exhbs({  
  defaultLayout: 'main',
  extname: '.hbs',
  layoutsDir: path.join(__dirname, 'api/layouts')
}))
app.set('view engine', '.hbs')  
app.set('views', path.join(__dirname, 'api'))  

require('./api/routes')(app, db);
app.listen(port);

console.log('server started on: ' + port);