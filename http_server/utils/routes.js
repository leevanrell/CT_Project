module.exports = function(app, db, logger) {
	//debugging
	app.get('/', function(req, res){
		logger.debug (req.ip + ': GET /');
		res.end('War Damn!');
	});

	//handles data from detectors
	app.post('/data', function(request, response){
		logger.debug(request.ip + ': POST /data');
		var data = request.body;
		var data_query = 'INSERT INTO data(time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)';
		var params = [data['time'], data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], data['rxl'], data['arfcn'], data['bsic'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']];
		db.execute(data_query, params, { prepare : true }, function(err){
			if (err) {
				response.status(400).send({message : 'error'});
				return logger.warn(err);
			} else {
				logger.info('added to data table');
				var towers_query = 'SELECT count(*) FROM towers WHERE MCC = \'' + data['MCC'] + '\' AND MNC = \'' + data['MNC'] + '\' AND LAC = \'' + data['LAC'] + '\' AND Cell_ID = \'' + data['Cell_ID'] + '\';';
				db.execute(towers_query, function(err, res){
					if(err) {
						response.status(400).send({message : 'error'});
						return logger.warn(err);
					} else if(res.rows[0].count.low == 0) {
						logger.info('adding cell info to towers table');
						url = 'https://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=' + data['MCC'] + '&mnc=' +  data['MNC'] + '&lac=' + data['LAC'] + '&cellid=' + data['Cell_ID'];
						require('request').get(url, function(err ,res){
							if(err){
								response.status(400).send({message : 'error'});
								return logger.warn(err);
							} else {
								logger.info('added to tower table');
								var mylnikov = JSON.parse(res.body);
								var params = (mylnikov['result'] == 404) ? [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], false, 0, 0] : [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], true, mylnikov['data']['lat'], mylnikov['data']['lon']];
								var query = 'INSERT INTO towers(MCC, MNC, LAC, Cell_ID, mylnikov, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)';
								db.execute(query, params, { prepare : true }, function(err){
									(err) ? response.status(400).send({message : 'error'}) : response.status(200).send({message : 'success'});
									return ((err) ? logger.warn(err) : logger.info('successfully added document to tables'));
								});
							};
						});
					} else {
						response.status(200).send({message : 'success'});
						logger.info('tower already in towers table');
					};
				});
			};
		});
	});

	//sends list of towers in database
	app.get('/towers', function(request, response){
		logger.debug(request.ip + ': GET /towers')
		db.execute('SELECT MCC, MNC, LAC, Cell_ID, mylnikov FROM towers;', function(err, res){
			if (err) {
				response.status(400).send({message : 'error'});
				return logger.warn(err);
			}
			else {
				var str = 'mcc-mnc-lac-cell_id\n';
				for(var row of res.rows) {
					temp = row['mcc'] + '-' + row['mnc'] + '-' + row['lac'] + '-' + row['cell_id'] + ((row['mylnikov']) ? ': registered in mylnikov' : ': not registered in mylnikov');
					var str = str + temp + '\n'; 
				};
				response.end(str);
				logger.info('returned towers');
			};
		});  
	});
	
	var getTowers = function(callback) {
		db.execute('SELECT MCC, MNC, LAC, Cell_ID, mylnikov, lat, lon FROM towers;', function(err, res){
			if (err) {
				logger.warn(err);
				return callback('err');
			} else {
				var table = res.rows;
				var json = [];
				for(var i = 0; i < table.length; i++) {
					if(table[i].mylnikov) {
						var marker = 'var marker' + i + ' = new google.maps.Marker({\n';
						marker = marker + '\tposition: ' + '{' + table[i].lat + ',' + table[i].lon + '};\n';
					    marker = marker + '\tmap: map,\n';
					    marker = marker + '\ttitle: ' + table[i].mcc + '-' + table[i].mnc + '-' + table[i].lac + '-' + table[i].cell_id + '\n';
					    marker = marker + '});';
					    json.push(marker);
					};
				};
				callback(JSON.stringify(json).replace(/"/g,""));
			};
		});		
	};

	var getTower = function(tower, callback) {
		var query = 'SELECT lat, lon, rxl FROM data WHERE MCC=\'' + tower.mcc + '\' AND MNC=\''+ tower.mnc + '\' AND lac=\'' + tower.lac + '\' AND cell_id=\'' + tower.cell_id + '\' ALLOW FILTERING;';
		db.execute(query, function(err, res){
			if(err) {
				logger.warn(err);
				return callback('err');
			} else {
				var table = res.rows;
				var json = [];
				for(var i = 0; i < table.length; i++) {
					var data = { 
						location: 'new google.mapsLatLng(' + table[i].lat + ', ' + table[i].lon + ')',
						weight: table[i].rxl
					};
					json.push(data);
				};
				callback(JSON.stringify(json).replace(/"/g,""));
			};
		});
	};
	
	//sends html page using google api with data from database
	app.get('/tower', function(request, response, next) {
		logger.debug(request.ip + ': GET /tower');
		getTowers(function(Markers) {
			if(Markers == 'err') {
				return response.status(400).send({message : 'error'});
			} else {
				getTower(request.query, function(Points){
					if(Points == 'err') {
						return response.status(400).send({message : 'error'});
					} else {
						GPS = '{lat: ' + request.query.lat + ', lng: ' + request.query.lon + '}'
						//logger.debug(GPS)
						//logger.debug(Markers.slice(1, -1))
						//logger.debug(Points);
						response.render('home', {
							center_in : GPS,
							points_in : Points,
							markers_in : Markers.slice(1, -1)
						});
						logger.info('returned tower');
					};
				});
			};
		});
	});
};