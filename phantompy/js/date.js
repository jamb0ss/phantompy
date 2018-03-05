// based on https://github.com/plaa/TimeShift-js

function __getMockDate__() {

	var OriginalDate = Date;

	var __mockDate__ = {};

	var currentTime = undefined;
	var timezoneOffset = new OriginalDate().getTimezoneOffset();

	function currentDate() {
		if (currentTime) {
			return new OriginalDate(currentTime);
		} else {
			return new OriginalDate();
		}
	}

	function realLocalToUtc(realLocal) {
		return new OriginalDate(realLocal.getTime() - realLocal.getTimezoneOffset()*60*1000 + timezoneOffset*60*1000);
	}
	function utcToLocal(utc) {
		return new OriginalDate(utc.getTime() - timezoneOffset*60*1000);
	}
	function localToUtc(local) {
		return new OriginalDate(local.getTime() + timezoneOffset*60*1000);
	}
	function twoDigit(n) {
		if (n < 10) {
			return "0" + n;
		} else {
			return "" + n;
		}
	}
	function timezoneName() {
		var zone = "GMT";
		var offset = Math.abs(timezoneOffset);
		if (timezoneOffset < 0) {
			zone = zone + "+";
		} else if (timezoneOffset > 0) {
			zone = zone + "-";
		} else {
			return zone;
		}
		return zone + twoDigit(Math.floor(offset/60)) + twoDigit(offset%60);
	}

	__mockDate__.getTimezoneOffset = function() {
		return timezoneOffset;
	}

	__mockDate__.setTimezoneOffset = function(offset) {
		timezoneOffset = offset;
	}

	__mockDate__.getTime = function() {
		return currentTime;
	}

	__mockDate__.setTime = function(time) {
		currentTime = time;
	}

	__mockDate__.OriginalDate = OriginalDate;

	__mockDate__.Date = function() {

		var isConstructor = false;
		if (this instanceof __mockDate__.Date && !this.__previouslyConstructedBy__mockDate__) {
			isConstructor = true;
			this.__previouslyConstructedBy__mockDate__ = true;
		}
		if (!isConstructor) {
			return (new __mockDate__.Date()).toString();
		}

		switch (arguments.length) {
		case 0:
			this.utc = currentDate();
			break;
		case 1:
			this.utc = new OriginalDate(arguments[0]);
			break;
		case 2:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1]));
			break;
		case 3:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1], arguments[2]));
			break;
		case 4:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1], arguments[2], arguments[3]));
			break;
		case 5:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4]));
			break;
		case 6:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4], arguments[5]));
			break;
		default:
			this.utc = realLocalToUtc(new OriginalDate(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4], arguments[5], arguments[6]));
			break;
		}
	}

	__mockDate__.Date.prototype.getDate = function() { return utcToLocal(this.utc).getUTCDate(); }
	__mockDate__.Date.prototype.getDay = function() { return utcToLocal(this.utc).getUTCDay(); }
	__mockDate__.Date.prototype.getFullYear = function() { return utcToLocal(this.utc).getUTCFullYear(); }
	__mockDate__.Date.prototype.getHours = function() { return utcToLocal(this.utc).getUTCHours(); }
	__mockDate__.Date.prototype.getMilliseconds = function() { return utcToLocal(this.utc).getUTCMilliseconds(); }
	__mockDate__.Date.prototype.getMinutes = function() { return utcToLocal(this.utc).getUTCMinutes(); }
	__mockDate__.Date.prototype.getMonth = function() { return utcToLocal(this.utc).getUTCMonth(); }
	__mockDate__.Date.prototype.getSeconds = function() { return utcToLocal(this.utc).getUTCSeconds(); }

	__mockDate__.Date.prototype.getUTCDate = function() { return this.utc.getUTCDate(); }
	__mockDate__.Date.prototype.getUTCDay = function() { return this.utc.getUTCDay(); }
	__mockDate__.Date.prototype.getUTCFullYear = function() { return this.utc.getUTCFullYear(); }
	__mockDate__.Date.prototype.getUTCHours = function() { return this.utc.getUTCHours(); }
	__mockDate__.Date.prototype.getUTCMilliseconds = function() { return this.utc.getUTCMilliseconds(); }
	__mockDate__.Date.prototype.getUTCMinutes = function() { return this.utc.getUTCMinutes(); }
	__mockDate__.Date.prototype.getUTCMonth = function() { return this.utc.getUTCMonth(); }
	__mockDate__.Date.prototype.getUTCSeconds = function() { return this.utc.getUTCSeconds(); }

	__mockDate__.Date.prototype.setDate = function() { var d = utcToLocal(this.utc); d.setUTCDate.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setFullYear = function() { var d = utcToLocal(this.utc); d.setUTCFullYear.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setHours = function() { var d = utcToLocal(this.utc); d.setUTCHours.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setMilliseconds = function() { var d = utcToLocal(this.utc); d.setUTCMilliseconds.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setMinutes = function() { var d = utcToLocal(this.utc); d.setUTCMinutes.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setMonth = function() { var d = utcToLocal(this.utc); d.setUTCMonth.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }
	__mockDate__.Date.prototype.setSeconds = function() { var d = utcToLocal(this.utc); d.setUTCSeconds.apply(d, Array.prototype.slice.call(arguments, 0)); this.utc = localToUtc(d); }

	__mockDate__.Date.prototype.setUTCDate = function() { this.utc.setUTCDate.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCFullYear = function() { this.utc.setUTCFullYear.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCHours = function() { this.utc.setUTCHours.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCMilliseconds = function() { this.utc.setUTCMilliseconds.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCMinutes = function() { this.utc.setUTCMinutes.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCMonth = function() { this.utc.setUTCMonth.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }
	__mockDate__.Date.prototype.setUTCSeconds = function() { this.utc.setUTCSeconds.apply(this.utc, Array.prototype.slice.call(arguments, 0)); }

	__mockDate__.Date.prototype.getYear = function() { return this.getFullYear() - 1900; }
	__mockDate__.Date.prototype.setYear = function(v) { this.setFullYear(v + 1900); }

	__mockDate__.Date.prototype.getTime = function() { return this.utc.getTime(); }
	__mockDate__.Date.prototype.setTime = function(v) { this.utc.setTime(v); }

	__mockDate__.Date.prototype.getTimezoneOffset = function() { return timezoneOffset; }

	__mockDate__.Date.prototype.toDateString = function() { return utcToLocal(this.utc).toDateString(); }  // Wrong
	__mockDate__.Date.prototype.toLocaleDateString = function() { return utcToLocal(this.utc).toLocaleDateString(); }  // Wrong

	__mockDate__.Date.prototype.toISOString = function() { return this.utc.toISOString(); }
	__mockDate__.Date.prototype.toGMTString = function() { return this.utc.toGMTString(); }
	__mockDate__.Date.prototype.toUTCString = function() { return this.utc.toUTCString(); }

	__mockDate__.Date.prototype.toString = function() {
		var wkdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
		var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
		var d = utcToLocal(this.utc);
		return wkdays[d.getUTCDay()] + " " + months[d.getUTCMonth()] + " " + twoDigit(d.getUTCDate()) + " " + d.getUTCFullYear() +
			" " + twoDigit(d.getUTCHours()) + ":" + twoDigit(d.getUTCMinutes()) + ":" + twoDigit(d.getUTCSeconds()) + " " + timezoneName();
	}
	__mockDate__.Date.prototype.toLocaleString = function() { return this.toString(); }  // Wrong
	__mockDate__.Date.prototype.toLocaleTimeString = function() { return this.toString(); }  // Wrong
	__mockDate__.Date.prototype.toTimeString = function() { return this.toString(); }  // Wrong

	__mockDate__.Date.prototype.toJSON = function() { return this.utc.toJSON(); }
	__mockDate__.Date.prototype.valueOf = function() { return this.utc.getTime(); }


	__mockDate__.Date.now = function() { return currentDate().getTime(); }
	__mockDate__.Date.parse = OriginalDate.parse;  // Wrong
	__mockDate__.Date.UTC = OriginalDate.UTC;

	__mockDate__.Date.prototype.desc = function() {
		return "utc=" + this.utc.toUTCString() + "   local=" + utcToLocal(this.utc).toUTCString() + "   offset=" + timezoneOffset;
	};

	return __mockDate__

};


