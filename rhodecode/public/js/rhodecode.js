/**
RhodeCode JS Files
**/

if (typeof console == "undefined" || typeof console.log == "undefined"){
	console = { log: function() {} }
}


function str_repeat(i, m) {
	for (var o = []; m > 0; o[--m] = i);
	return o.join('');
}

/**
 * INJECT .format function into String
 * Usage: "My name is {0} {1}".format("Johny","Bravo")
 * Return "My name is Johny Bravo"
 * Inspired by https://gist.github.com/1049426
 */
String.prototype.format = function() {
	  
	  function format() {
	    var str = this;
	    var len = arguments.length+1;
	    var safe = undefined;
	    var arg = undefined;
	    
	    // For each {0} {1} {n...} replace with the argument in that position.  If 
	    // the argument is an object or an array it will be stringified to JSON.
	    for (var i=0; i < len; arg = arguments[i++]) {
	      safe = typeof arg === 'object' ? JSON.stringify(arg) : arg;
	      str = str.replace(RegExp('\\{'+(i-1)+'\\}', 'g'), safe);
	    }
	    return str;
	  }

	  // Save a reference of what may already exist under the property native.  
	  // Allows for doing something like: if("".format.native) { /* use native */ }
	  format.native = String.prototype.format;

	  // Replace the prototype property
	  return format;

}();


/**
 * SmartColorGenerator
 *
 *usage::
 *	var CG = new ColorGenerator();
 *  var col = CG.getColor(key); //returns array of RGB
 *  'rgb({0})'.format(col.join(',')
 * 
 * @returns {ColorGenerator}
 */
function ColorGenerator(){
	this.GOLDEN_RATIO = 0.618033988749895;
	this.CURRENT_RATIO = 0.22717784590367374 // this can be random
	this.HSV_1 = 0.75;//saturation
	this.HSV_2 = 0.95;
	this.color;
	this.cacheColorMap = {};
};

ColorGenerator.prototype = {
    getColor:function(key){
    	if(this.cacheColorMap[key] !== undefined){
    		return this.cacheColorMap[key];
    	}
    	else{
    		this.cacheColorMap[key] = this.generateColor();
    		return this.cacheColorMap[key];
    	}
    },
    _hsvToRgb:function(h,s,v){
        if (s == 0.0)
            return [v, v, v];
        i = parseInt(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if (i == 0) 
            return [v, t, p]
        if (i == 1) 
            return [q, v, p]
        if (i == 2) 
            return [p, v, t]
        if (i == 3)
            return [p, q, v]
        if (i == 4) 
            return [t, p, v]
        if (i == 5)
            return [v, p, q]            	
    },
    generateColor:function(){
        this.CURRENT_RATIO = this.CURRENT_RATIO+this.GOLDEN_RATIO;
        this.CURRENT_RATIO = this.CURRENT_RATIO %= 1;
        HSV_tuple = [this.CURRENT_RATIO, this.HSV_1, this.HSV_2]
        RGB_tuple = this._hsvToRgb(HSV_tuple[0],HSV_tuple[1],HSV_tuple[2]);
        function toRgb(v){
        	return ""+parseInt(v*256)
        }
        return [toRgb(RGB_tuple[0]),toRgb(RGB_tuple[1]),toRgb(RGB_tuple[2])];
        
    }
}





/**
 * GLOBAL YUI Shortcuts
 */
var YUC = YAHOO.util.Connect;
var YUD = YAHOO.util.Dom;
var YUE = YAHOO.util.Event;
var YUQ = YAHOO.util.Selector.query;

// defines if push state is enabled for this browser ?
var push_state_enabled = Boolean(
		window.history && window.history.pushState && window.history.replaceState
		&& !(   /* disable for versions of iOS before version 4.3 (8F190) */
				(/ Mobile\/([1-7][a-z]|(8([abcde]|f(1[0-8]))))/i).test(navigator.userAgent)
				/* disable for the mercury iOS browser, or at least older versions of the webkit engine */
				|| (/AppleWebKit\/5([0-2]|3[0-2])/i).test(navigator.userAgent)
		)
)

/**
 * Partial Ajax Implementation
 * 
 * @param url: defines url to make partial request
 * @param container: defines id of container to input partial result
 * @param s_call: success callback function that takes o as arg
 *  o.tId
 *  o.status
 *  o.statusText
 *  o.getResponseHeader[ ]
 *  o.getAllResponseHeaders
 *  o.responseText
 *  o.responseXML
 *  o.argument
 * @param f_call: failure callback
 * @param args arguments 
 */
function ypjax(url,container,s_call,f_call,args){
	var method='GET';
	if(args===undefined){
		args=null;
	}
	
	// Set special header for partial ajax == HTTP_X_PARTIAL_XHR
	YUC.initHeader('X-PARTIAL-XHR',true);
	
	// wrapper of passed callback
	var s_wrapper = (function(o){
		return function(o){
			YUD.get(container).innerHTML=o.responseText;
			YUD.setStyle(container,'opacity','1.0');
    		//execute the given original callback
    		if (s_call !== undefined){
    			s_call(o);
    		}
		}
	})()	
	YUD.setStyle(container,'opacity','0.3');
	YUC.asyncRequest(method,url,{
		success:s_wrapper,
		failure:function(o){
			console.log(o)
		}
	},args);
	
}

/**
 * tooltip activate
 */
var tooltip_activate = function(){
    function toolTipsId(){
        var ids = [];
        var tts = YUQ('.tooltip');
        for (var i = 0; i < tts.length; i++) {
            // if element doesn't not have and id 
        	//  autogenerate one for tooltip 
            if (!tts[i].id){
                tts[i].id='tt'+((i*100)+tts.length);
            }
            ids.push(tts[i].id);
        }
        return ids
    };
    var myToolTips = new YAHOO.widget.Tooltip("tooltip", {
        context: [[toolTipsId()],"tl","bl",null,[0,5]],
        monitorresize:false,
        xyoffset :[0,0],
        autodismissdelay:300000,
        hidedelay:5,
        showdelay:20,
    });
}

/**
 * show more
 */
var show_more_event = function(){
    YUE.on(YUD.getElementsByClassName('show_more'),'click',function(e){
        var el = e.target;
        YUD.setStyle(YUD.get(el.id.substring(1)),'display','');
        YUD.setStyle(el.parentNode,'display','none');
    });
}

