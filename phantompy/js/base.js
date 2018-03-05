// TODO: css/images partial download


// inject configuration
page.__config__ = %(__config__)s;


// (in milli-secs) defines the timeout after which any resource requested
// will stop trying and proceed with other parts of the page
page.settings.resourceTimeout = page.__config__['resource_timeout'];

// User-Agent HTTP header
// page.settings.userAgent = page.__config__['navigator']['userAgent'];

// JavaScript
page.settings.javascriptEnabled = page.__config__['javascript_enabled'];

// images
page.settings.loadImages = page.__config__['load_images'];


// INIT ::

// TODO: onInitialized is invoked multiple times
page.onInitialized = function() {

	// inject helpers
	page.evaluate(function(__toString__, __toNaitiveFunc__, __patchObject__) {
		window.__toString__ = __toString__;
		window.__toNaitiveFunc__ = __toNaitiveFunc__;
		window.__patchObject__ = __patchObject__;
	}, __toString__, __toNaitiveFunc__, __patchObject__);

	// navigator
	page.setNavigator(page.__config__['navigator']);

	// screen
	page.setScreen(page.__config__['screen']);

	// Flash plugin
	if (page.__config__['spoof_flash_plugin']) {
		page.spoofFlashPlugin(page.__config__['flash_plugin']);
	};

	// Java plugin
	if (page.__config__['spoof_java_plugin']) {
		page.spoofJavaPlugin();
	};

	// HTML5 media
	if (page.__config__['spoof_html5_media']) {
		page.spoofHTML5Media();
	};

	// timezone
	if (page.__config__['timezone_offset'] != null) {
		page.setTimezone(page.__config__['timezone_offset']);

	};

	// PhantomJS fingerprints
	page.removeFingerprints();

};


// HTTP meta container
page.httpMeta = {};
page.httpMeta.request = {};
page.httpMeta.response = {};


// REQUEST ::

// request:callbacks
page.onResourceRequestedCallbacks = [];

// page requests a resource
page.onResourceRequested = function(requestData, request) {
	for (i = 0; i < page.onResourceRequestedCallbacks.length; i++) {
		page.onResourceRequestedCallbacks[i](requestData, request);
	};

	if (requestData.url === page.httpMeta.request.url) {
		page.httpMeta.request.method = requestData.method;
		page.httpMeta.request.headers = requestData.headers;
	};

};

// navigation event
page.onNavigationRequested = function(url, type, willNavigate, main) {
	// TODO: wft? (https://whoer.net/#extended)
	if (url !== 'about:blank') {
		page.httpMeta.request = {};
		page.httpMeta.response = {};
		page.httpMeta.request.url = url;
	};
};

// page starts the loading
// page.onLoadStarted = function() {
// };


// RESPONSE ::

// response:callbacks
// var page.onResourceReceivedCallbacks = [];

// a resource requested by the page is received
page.onResourceReceived = function(response) {
	// for (i = 0; i < page.onResourceReceivedCallbacks.length; i++) {
	// 	page.onResourceReceivedCallbacks[i](response);
	// };

	// TODO: start or end?
	if (response.url === page.httpMeta.request.url && response.stage === 'start') {
		page.httpMeta.response.url = response.url;
		page.httpMeta.response.status_code = response.status;
		page.httpMeta.response.headers = response.headers;
	};

};

// page finishes the loading
page.onLoadFinished = function(status) {
	if (status === 'fail') {
		page.httpMeta.response = null;
	};
};



// HELPERS ::

// callbacks
page.addCallback = function(callbacks, callback) {
	if (callbacks.indexOf(callback) > -1) {
		return false;
	} else {
		callbacks.push(callback);
		return true;
	};
};

page.removeCallback = function(callbacks, callback) {
	var index = callbacks.indexOf(callback);
	if (index > -1) {
		callbacks.splice(index, 1);
		return true;
	} else {
		return false;
	};
};


// update HTTP headers
// page.updateHeaders = function(headers) {
// 	for (var key in headers) {
// 		if (headers.hasOwnProperty(key)) {
// 			var val = headers[key];
// 			if (val === null) {
// 				delete page.customHeaders[key]
// 			} else {
// 				page.customHeaders[key] = val;
// 			};
// 		};
// 	};
// };


// set navigator
page.setNavigator = function(config) {
	page.evaluate(function(config) {
		navigator = __patchObject__(navigator, config);
	}, config);
};


// set proxy
page._setProxy = function(proxy) {
	phantom.setProxy(proxy.host, proxy.port, proxy.type, proxy.user, proxy.passwd);
};

// reset proxy
page._resetProxy = function() {
	phantom.setProxy("");
};


// screen
page.setScreen = function(config) {
	page.evaluate(function(config) {
		window.screen = __patchObject__(window.screen, config['window.screen']);
		[].forEach.call(
			Object.getOwnPropertyNames(config['window']),
			function(prop) {
				window[prop] = config['window'][prop];
			}
		);
	}, config);
};


// timezone
// TODO: check if !== local timezone
page.setTimezone = function(timezone_offset) {
	page.evaluate(function(timezone_offset) {
		if (window.__Date__ === undefined) {
			// inject __getMockDate__
			%(__getMockDate__)s
			__Date__ = __getMockDate__();
		};
		Date = __toNaitiveFunc__(__Date__.Date, 'Date');
		__Date__.setTimezoneOffset(-1 * timezone_offset);
	}, timezone_offset);
};

// reset timezone (Date object)
page.resetTimezone = function() {
	page.evaluate(function() {
		if (window.__Date__ !== undefined) {
			Date = __Date__.OriginalDate;
		};
	});
};


// CSS files
page.skipCSS = function(requestData, request) {
	if (
		(/https?:\/\/.+?\.css/gi).test(requestData.url) ||
		requestData.headers['Content-Type'] == 'text/css'
	) {
		request.abort();
		// request.cancel();
	};
};


// remove PhantomJS fingerprints
page.removeFingerprints = function() {
	page.evaluate(function() {
		delete window._phantom;
		delete window.callPhantom;
	});
};


// spoof HTML video & audio
page.spoofHTML5Media = function() {
	page.evaluate(function() {
		var __createElement__ = document.createElement;
		document.createElement = __toNaitiveFunc__(
			function createElement(tag_name) {
				var elem = __createElement__.call(document, tag_name);
				if (tag_name === 'video' || tag_name === 'audio') {
					elem.canPlayType = __toNaitiveFunc__(
						function canPlayType() {
							return 'probably';
						}
					);
				};
				return elem;
			}
		);
	});
};


// spoof JAVA plugin
page.spoofJavaPlugin = function() {
	page.evaluate(function() {
		navigator = __patchObject__(
			navigator,
			{
				javaEnabled: __toNaitiveFunc__(
					function javaEnabled() {
						return true;
					}
				)
			}
		);
	});
};


// spoof Flash plugin
page.spoofFlashPlugin = function(flash_plugin) {
	page.evaluate(function(flash_plugin) {

		var mimeTypes;
		var plugins;
		var mime;
		var plugin;

		mime = {
			'description': 'Shockwave Flash',
			'suffixes': 'swf',
			'type': 'application/x-shockwave-flash'
		};

		plugin = {
			'name': 'Shockwave Flash',
			'description': flash_plugin.description,
			'filename': flash_plugin.filename,
			'0': mime,
			'length': 1
		};

		mime['enabledPlugin'] = plugin;

		// TODO: [object MimeTypeArray]
		mimeTypes = __patchObject__(navigator.mimeTypes, {
			'application/x-shockwave-flash': mime,
			'length': 1,
			'0': mime
		}, 'MimeTypeArray');

		// TODO: [object PluginArray]
		plugins = __patchObject__(navigator.plugins, {
			'Shockwave Flash': plugin,
			'length': 1,
			'0': plugin
		}, 'PluginArray');

		// TODO: Navigator
		navigator = __patchObject__(navigator, {
			'plugins': plugins,
			'mimeTypes': mimeTypes
		});

		HTMLObjectElement.prototype.GetVariable = HTMLEmbedElement.prototype.GetVariable = __toNaitiveFunc__(
			function GetVariable(name) {
				if (name === '$version') {
					return flash_plugin.version;
				};
			}
		);
	}, flash_plugin);
};


// spoof toString
function __toString__(name, isObj) {
	function toString() {
    	if (isObj === undefined) {
			return 'function ' + name + '() { [native code] }';
		} else {
			return '[object ' + name + ']';
		}
	};
	toString.toString = function() {
		return 'function toString() { [native code] }';
	};
	toString.toString.toString = toString.toString;
	return toString;
}


// [native code] (TODO: arguments)
function __toNaitiveFunc__(func, name) {
    if (name === undefined) {
		name = func.name;
	};
	func.toString = __toString__(name);
	return func;
};


// patch a given object
function __patchObject__(object, patch, name) {

	var override = Object.keys(patch);
	var prototype = Object.create(Object.getPrototypeOf(object));
	var constructor = __toNaitiveFunc__(function() {}, object.constructor.name);
	constructor.prototype = prototype;
	var new_object = new constructor();
	if (name !== undefined) {
		new_object.toString = __toString__(name, true);
	};

	[].forEach.call(
		Object.getOwnPropertyNames(object),
		function(prop) {
			if (override.indexOf(prop) === -1) {
				Object.defineProperty(
					new_object,
					prop,
					Object.getOwnPropertyDescriptor(object, prop)
				);
			};
		}
	);

	[].forEach.call(
		override,
		function(prop) {

			var descriptor = Object.getOwnPropertyDescriptor(object, prop);

			if (descriptor) {
				delete descriptor.get;
				delete descriptor.set;
			} else {
				descriptor = {
					'writable': true,
					'enumerable': true,
					'configurable': true,
				};
			};

			descriptor.value = patch[prop];
			Object.defineProperty(new_object, prop, descriptor);
		}
	);

	return new_object;
};



