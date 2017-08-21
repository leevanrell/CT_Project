module.exports = function(app, db) {

	app.get('/', function(req, res){
		res.end('War Damn!');
	});

	app.post('/data', function(request, response){
		var data = request.body;
		var query = 'INSERT INTO data(time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)';
		var params = [data['time'], data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], data['rxl'], data['arfcn'], data['bsic'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']];
		db.execute(query, params, { prepare : true }, function(err){
			if (err) {
				response.status(400).send({message : 'error'});
				return console.log(err);
			} else {
				url = 'https://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=' + data['MCC'] + '&mnc=' +  data['MNC'] + '&lac=' + data['LAC'] + '&cellid=' + data['Cell_ID'];
				require('request').get(url, function(err,res){
					if(err){
						response.status(400).send({message : 'error'});
						return console.log(err);
					} else {
						var mylnikov = JSON.parse(res.body)
						var params = (mylnikov['result'] == 404) ? [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], false, 0, 0] : [data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], true, mylnikov['data']['lat'], mylnikov['data']['lon']];
						var query = 'INSERT INTO towers(MCC, MNC, LAC, Cell_ID, mylnikov, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)';
						db.execute(query, params, { prepare : true }, function(err){
							if (err) {
								response.status(400).send({message : 'error'});
								return console.log(err);
							} else {
								response.status(200).send({message : 'success'});
								return console.log('successfully added document to tables');
							};
						});
					};
				});
			};
		});
	});

	app.get('/towers', function(request, response){
		db.execute('SELECT MCC, MNC, LAC, Cell_ID, mylnikov FROM towers', function(err, res){
			var str = 'mcc-mnc-lac-cell_id\n'
			for(var row of res.rows) {
				temp = row['mcc'] + '-' + row['mnc'] + '-' + row['lac'] + '-' + row['cell_id']
				temp = temp + ((row['mylnikov']) ? ': registered in mylnikov\n' : ': not registered in mylnikov');
				var str = str + temp; 
			};
			response.end(str);
		});  
	});

	app.get('/tower', function(request, response) {
		var query = 'SELECT lat, lon, rxl FROM data WHERE MCC=\'' + request.query.mcc + '\' AND MNC=\''+ request.query.mnc + '\' AND lac=\'' + request.query.lac + '\' AND cell_id=\'' + request.query.cell_id + '\' ALLOW FILTERING;';
		db.execute(query, function(err, res){
			var table = res.rows;
			var o = {};
			var key = 'tower data';
			o[key] = [];

			for(var i = 0; i < table.length; i++) {
				var data = { 
					location: 'new google.mapsLatLng(' + table[i].lat + ', ' + table[i].lon + ')',
					weight: table[i].rxl
				};
				o[key].push(data);
			};
			output = JSON.stringify(o[key]).replace(/"/g,"");
			//str = new String();
			//str = output.toString().replace(/"/g,"");
			response.render('home', {
				center_in : '{lat: 32.607722, lng: -85.489545}',
				points_in : output
			});
		});
	});

	//TODO: replace {lat: 37.775, lng: -122.434} : center_in
	//TODO: replace data : points_in

};

