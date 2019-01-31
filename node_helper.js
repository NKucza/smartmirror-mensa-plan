var NodeHelper = require('node_helper');
var request = require('request');
const {PythonShell} = require('python-shell');

module.exports = NodeHelper.create({
	start: function () {
		console.log('MMM-JsonTable helper started...');
	},

	getJson: function (mensa_parser, hour_offset) {
		const self = this;

		self.pyshell = new PythonShell('modules/' + this.name + '/mensa_requests/' + mensa_parser, { mode: 'json', args: hour_offset});

		self.pyshell.on('message', function (message) {

            if (message.hasOwnProperty('MensaPlan')) {
            	obj_string = JSON.parse(JSON.stringify(message.MensaPlan))
				self.sendSocketNotification("smartmirror-mensa-plan_JSON_RESULT", {mensa_parser: mensa_parser, data: obj_string});
            }

        });
	},

	//Subclass socketNotificationReceived received.
	socketNotificationReceived: function (notification, arg) {
		if (notification === "smartmirror-mensa-plan_GET_JSON") {
			this.getJson(arg[0], arg[1]);
		}
	},

	stop: function() {
		const self = this;
		self.pyshell.childProcess.kill('SIGKILL');
		self.pyshell.end(function (err) {
           	if (err){
        		//throw err;
    		};
    		console.log('finished');
		});
	}
});

