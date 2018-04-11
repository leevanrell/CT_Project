module.exports = function(app, db, logger) {

	//debugging
	app.get('/', function(req, res){
		logger.debug (req.ip + ': GET /');
		res.end('War Damn!');
	});

	//handles data from detectors
	app.post('/data', function(request, response){
		logger.debug(request.ip + ': POST /data');
		var data = request.body; //data from detector, contains tower meta data and gps coords
		var data_query = 'INSERT INTO data(time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)';
		var params = [data['time'], data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], data['rxl'], data['arfcn'], data['bsic'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']];
		db.execute(data_query, params, { prepare : true }, function(err){ //inserts into data table
			if (err) {
				response.status(400).send({message : 'error'});
				return logger.warn(err);
			};
			var towers_query = 'SELECT count(*) FROM towers WHERE MCC = \'' + data['MCC'] + '\' AND MNC = \'' + data['MNC'] + '\' AND LAC = \'' + data['LAC'] + '\' AND Cell_ID = \'' + data['Cell_ID'] + '\';';
			db.execute(towers_query, function(err, res){ //checks if tower is in towers table
				if(err) {
					response.status(400).send({message : 'error'});
					return logger.warn(err);
				} else if(res.rows[0].count.low == 0) { //if low is zero tower is not in table 
					url = 'https://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=' + data['MCC'] + '&mnc=' +  data['MNC'] + '&lac=' + data['LAC'] + '&cellid=' + data['Cell_ID'];
					require('request').get(url, function(err ,res){ //checks if tower is in mylnikov database
						if(err){
							response.status(400).send({message : 'error'});
							return logger.warn(err);
						} else {
							var mylnikov = JSON.parse(res.body);
							var params = (mylnikov['result'] == 404) ? [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], false, 0, 0] : [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], true, mylnikov['data']['lat'], mylnikov['data']['lon']];
							var query = 'INSERT INTO towers(MCC, MNC, LAC, Cell_ID, mylnikov, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)';
							db.execute(query, params, { prepare : true }, function(err){ //adds tower to towers table
								(err) ? response.status(400).send({message : 'error'}) : response.status(200).send({message : 'success'});
								(err) ? logger.warn(err) : logger.info('successfully added document to tables');
							});
						};
					});
				} else { //tower is already in db and doesn't need to be added
					response.status(200).send({message : 'success'});
					logger.info('document is already in towers table');
				};
			});
		});
	});

	//sends list of towers in database
	app.get('/towers', function(request, response){
		logger.debug(request.ip + ': GET /towers')
		db.execute('SELECT MCC, MNC, LAC, Cell_ID, mylnikov FROM towers;', function(err, res){ //gets list of towers from table
			if (err) {
				response.status(400).send({message : 'error'});
				return logger.warn(err);
			}
			var str = 'mcc-mnc-lac-cell_id\n';
			for(var row of res.rows) {
				temp = row['mcc'] + '-' + row['mnc'] + '-' + row['lac'] + '-' + row['cell_id'] + ((row['mylnikov']) ? ': registered in mylnikov' : ': not registered in mylnikov');
				var str = str + temp + '\n'; 
			};
			response.end(str); //sends list of towers to client
			logger.info('returned towers to: ' + request.ip);
		});  
	});
	
	var getTowers = function(callback) {
		db.execute('SELECT MCC, MNC, LAC, Cell_ID, mylnikov, lat, lon FROM towers;', function(err, res){
			if (err) {
				logger.warn(err);
				return callback('err');
			}
			var table = res.rows;
			var json = [];
			for(var i = 0; i < table.length; i++) {
				if(table[i].mylnikov) {
					var marker = 'var marker' + i + ' = new google.maps.Marker({\n';
					marker = marker + '\tposition: ' + '{' + table[i].lat + ',' + table[i].lon + '};\n';
				    marker = marker + '\tmap: map,\n';
				    marker = marker + '\ttitle: ' + table[i].mcc + '-' + table[i].mnc + '-' + table[i].lac + '-' + table[i].cell_id + '\n';
				    marker = marker + '});';
				    json.push(marker); //adds data to json array
				};
			};
			callback(JSON.stringify(json).replace(/"/g,"")); //removes " from json string and returns to /tower
		});		
	};

	var getTower = function(tower, callback) {
		var query = 'SELECT lat, lon, rxl FROM data WHERE MCC=\'' + tower.mcc + '\' AND MNC=\''+ tower.mnc + '\' AND lac=\'' + tower.lac + '\' AND cell_id=\'' + tower.cell_id + '\' ALLOW FILTERING;';
		db.execute(query, function(err, res){
			if(err) {
				logger.warn(err);
				return callback('err');
			}
			var table = res.rows;
			var json = [];
			for(var i = 0; i < table.length; i++) {
				var data = { 
					location: 'new google.mapsLatLng(' + table[i].lat + ', ' + table[i].lon + ')',
					weight: table[i].rxl
				};
				json.push(data); //adds data to json array
			};
			callback(JSON.stringify(json).replace(/"/g,"")); //removes " from json string
		});
	};
	
	//sends html page using google api with data from database
	app.get('/tower', function(request, response, next) {
		logger.debug(request.ip + ': GET /tower');
		getTowers(function(Markers) { //gets markers for each tower
			if(Markers == 'err') {
				response.status(400).send({message : 'error'});
				return logger.warn('getTowers failed');
			}
			getTower(request.query, function(Points){ //gets tower heatmap data
				if(Points == 'err') {
					response.status(400).send({message : 'error'});
					return logger.warn('getTower failed');
				}
				GPS = '{lat: ' + request.query.lat + ', lng: ' + request.query.lon + '}'
				//logger.debug(GPS)
				//logger.debug(Markers.slice(1, -1))
				//logger.debug(Points);
				response.render('home', {
					center_in : GPS,
					points_in : Points, //heatmap data
					markers_in : Markers.slice(1, -1) //tower markers
				});
				logger.info('returned tower heatmap to: ' + request.ip);
			});
		});
	});
	
};