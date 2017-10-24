const CASS_IP = '127.0.0.1';
const KEYSPACE = 'auresearch';
const logDir = './utils/log/';

//gets ip
var os = require('os');
var interfaces = os.networkInterfaces();
var addresses = [];
for (var k in interfaces) {
    for (var k2 in interfaces[k]) {
        var address = interfaces[k][k2];
        if (address.family === 'IPv4' && !address.internal) {
            addresses.push(address.address);
        };
    };
};

const express = require('express'),
  app = express(),
  port = process.env.PORT || 3000;
  //ip = process.env.IP || addresses[0];
  ip = process.env.IP || '127.0.0.1'

//setting up connection to cassandra server
const cassandra = require('cassandra-driver')
const db = new cassandra.Client({contactPoints: [CASS_IP], keyspace: KEYSPACE});
//db.execute('DROP TABLE data')
//db.execute('DROP TABLE towers')
db.execute('CREATE TABLE IF NOT EXISTS data(time text,  MCC text, MNC text, LAC text, Cell_ID text, rxl int, arfcn text, bsic text, lat float, lon float, satellites int, gps_quality int, altitude float, altitude_units text, PRIMARY KEY(time, MCC, MNC, LAC, Cell_ID, rxl)) WITH CLUSTERING ORDER BY (MCC DESC, MNC ASC, LAC DESC, Cell_ID ASC, rxl DESC);');
db.execute('CREATE TABLE IF NOT EXISTS towers(MCC text, MNC text, LAC text, Cell_ID text, mylnikov boolean, lat float, lon float, PRIMARY KEY(Cell_ID, MCC, MNC, LAC));');

//setting up logger
const winston = require('winston');
require('winston-daily-rotate-file');
const moment = require('moment');
const fs = require('fs');
const env = process.env.NODE_ENV || 'development';
const time = function() { return moment().format('MM-DD-YYYY HH:mm:ss');}
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}
const tsFormat = () => (new Date()).toLocaleTimeString();
const logger = new (winston.Logger)({
  transports: [
    new (winston.transports.Console)({
      timestamp: time,
      colorize: true,
      level: env === 'development' ? 'debug' : 'info',
    }),
    new (winston.transports.File)({
      filename: `${logDir}/all.log`,
      timestamp: time,
      level: env === 'development' ? 'debug' : 'info',
      json: false
    }),
    new (winston.transports.DailyRotateFile)({
    	filename: logDir + '-results.log',
    	timestamp: time,
    	datePattern: 'yyyy-MM-dd',
    	prepend: true,
    	level: env === 'development' ? 'debug' : 'info',
    	json: false
    })
  ],
  exitOnError: false
});

//setting layout for get /tower
const exhbs = require('express-handlebars')
const path = require('path')
app.engine('.hbs', exhbs({  
  defaultLayout: 'main',
  extname: '.hbs',
  layoutsDir: path.join(__dirname, 'utils/layouts')
}))
app.set('view engine', '.hbs')  
app.set('views', path.join(__dirname, 'utils'))  

//parser for post request body
const bodyParser = require('body-parser');
app.use(bodyParser.json());

//importing routes
require('./utils/routes')(app, db, logger);

//starts server
app.listen(port, ip);
logger.info('server started on: ' + ip + ':' + port);