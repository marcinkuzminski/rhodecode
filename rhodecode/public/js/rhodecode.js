/**
RhodeCode JS Files
**/

if (typeof console == "undefined" || typeof console.log == "undefined"){
	console = { log: function() {} }
}


var str_repeat = function(i, m) {
	for (var o = []; m > 0; o[--m] = i);
	return o.join('');
};

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
var ColorGenerator = function(){
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
);

var _run_callbacks = function(callbacks){
	if (callbacks !== undefined){
		var _l = callbacks.length;
	    for (var i=0;i<_l;i++){
	    	var func = callbacks[i];
	    	if(typeof(func)=='function'){
	            try{
	          	    func();
	            }catch (err){};            		
	    	}
	    }
	}		
}

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
			console.log(o);
			YUD.get(container).innerHTML='ERROR';
			YUD.setStyle(container,'opacity','1.0');
			YUD.setStyle(container,'color','red');
		}
	},args);
	
};

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
};

/**
 * show more
 */
var show_more_event = function(){
    YUE.on(YUD.getElementsByClassName('show_more'),'click',function(e){
        var el = e.target;
        YUD.setStyle(YUD.get(el.id.substring(1)),'display','');
        YUD.setStyle(el.parentNode,'display','none');
    });
};


/**
 * Quick filter widget
 * 
 * @param target: filter input target
 * @param nodes: list of nodes in html we want to filter.
 * @param display_element function that takes current node from nodes and
 *    does hide or show based on the node
 * 
 */
var q_filter = function(target,nodes,display_element){
	
	var nodes = nodes;
	var q_filter_field = YUD.get(target);
	var F = YAHOO.namespace(target);

	YUE.on(q_filter_field,'click',function(){
	   q_filter_field.value = '';
	});

	YUE.on(q_filter_field,'keyup',function(e){
	    clearTimeout(F.filterTimeout); 
	    F.filterTimeout = setTimeout(F.updateFilter,600); 
	});

	F.filterTimeout = null;

	var show_node = function(node){
		YUD.setStyle(node,'display','')
	}
	var hide_node = function(node){
		YUD.setStyle(node,'display','none');
	}
	
	F.updateFilter  = function() { 
	   // Reset timeout 
	   F.filterTimeout = null;
	   
	   var obsolete = [];
	   
	   var req = q_filter_field.value.toLowerCase();
	   
	   var l = nodes.length;
	   var i;
	   var showing = 0;
	   
       for (i=0;i<l;i++ ){
    	   var n = nodes[i];
    	   var target_element = display_element(n)
    	   if(req && n.innerHTML.toLowerCase().indexOf(req) == -1){
    		   hide_node(target_element);
    	   }
    	   else{
    		   show_node(target_element);
    		   showing+=1;
    	   }
       }	  	   

	   // if repo_count is set update the number
	   var cnt = YUD.get('repo_count');
	   if(cnt){
		   YUD.get('repo_count').innerHTML = showing;
	   }       
       
	}	
};

var ajaxPOST = function(url,postData,success) {
    var sUrl = url;
    var callback = {
        success: success,
        failure: function (o) {
            alert("error");
        },
    };
    var postData = postData;
    var request = YAHOO.util.Connect.asyncRequest('POST', sUrl, callback, postData);
};


/** comments **/
var removeInlineForm = function(form) {
	form.parentNode.removeChild(form);
};

var tableTr = function(cls,body){
	var form = document.createElement('tr');
	YUD.addClass(form, cls);
	form.innerHTML = '<td class="lineno-inline new-inline"></td>'+
    				 '<td class="lineno-inline old-inline"></td>'+ 
                     '<td>{0}</td>'.format(body);
	return form;
};

var createInlineForm = function(parent_tr, f_path, line) {
	var tmpl = YUD.get('comment-inline-form-template').innerHTML;
	tmpl = tmpl.format(f_path, line);
	var form = tableTr('comment-form-inline',tmpl)
	
	// create event for hide button
	form = new YAHOO.util.Element(form);
	var form_hide_button = new YAHOO.util.Element(form.getElementsByClassName('hide-inline-form')[0]);
	form_hide_button.on('click', function(e) {
		var newtr = e.currentTarget.parentNode.parentNode.parentNode.parentNode.parentNode;
		removeInlineForm(newtr);
		YUD.removeClass(parent_tr, 'form-open');
	});
	return form
};
var injectInlineForm = function(tr){
	  if(YUD.hasClass(tr,'form-open') || YUD.hasClass(tr,'context') || YUD.hasClass(tr,'no-comment')){
		  return
	  }	
	  YUD.addClass(tr,'form-open');
	  var node = tr.parentNode.parentNode.parentNode.getElementsByClassName('full_f_path')[0];
	  var f_path = YUD.getAttribute(node,'path');
	  var lineno = getLineNo(tr);
	  var form = createInlineForm(tr, f_path, lineno);
	  var target_tr = tr;
	  if(YUD.hasClass(YUD.getNextSibling(tr),'inline-comments')){
		  target_tr = YUD.getNextSibling(tr);
	  }
	  YUD.insertAfter(form,target_tr);
	  YUD.get('text_'+lineno).focus();
	  tooltip_activate();
};

var createInlineAddButton = function(tr,label){
	var html = '<div class="add-comment"><span class="ui-btn">{0}</span></div>'.format(label);
        
	var add = new YAHOO.util.Element(tableTr('inline-comments-button',html));
	add.on('click', function(e) {
		injectInlineForm(tr);
	});
	return add;
};

var getLineNo = function(tr) {
	var line;
	var o = tr.children[0].id.split('_');
	var n = tr.children[1].id.split('_');

	if (n.length >= 2) {
		line = n[n.length-1];
	} else if (o.length >= 2) {
		line = o[o.length-1];
	}

	return line
};


var fileBrowserListeners = function(current_url, node_list_url, url_base,
									truncated_lbl, nomatch_lbl){
	var current_url_branch = +"?branch=__BRANCH__";
	var url = url_base;
	var node_url = node_list_url;	

	YUE.on('stay_at_branch','click',function(e){
	    if(e.target.checked){
	        var uri = current_url_branch;
	        uri = uri.replace('__BRANCH__',e.target.value);
	        window.location = uri;
	    }
	    else{
	        window.location = current_url;
	    }
	})            

	var n_filter = YUD.get('node_filter');
	var F = YAHOO.namespace('node_filter');
	
	F.filterTimeout = null;
	var nodes = null;

	F.initFilter = function(){
	  YUD.setStyle('node_filter_box_loading','display','');
	  YUD.setStyle('search_activate_id','display','none');
	  YUD.setStyle('add_node_id','display','none');
	  YUC.initHeader('X-PARTIAL-XHR',true);
	  YUC.asyncRequest('GET',url,{
	      success:function(o){
	        nodes = JSON.parse(o.responseText);
	        YUD.setStyle('node_filter_box_loading','display','none');
	        YUD.setStyle('node_filter_box','display','');
	        n_filter.focus();
			if(YUD.hasClass(n_filter,'init')){
				n_filter.value = '';
				YUD.removeClass(n_filter,'init');
			}   
	      },
	      failure:function(o){
	          console.log('failed to load');
	      }
	  },null);            
	}

	F.updateFilter  = function(e) {
	    
	    return function(){
	        // Reset timeout 
	        F.filterTimeout = null;
	        var query = e.target.value.toLowerCase();
	        var match = [];
	        var matches = 0;
	        var matches_max = 20;
	        if (query != ""){
	            for(var i=0;i<nodes.length;i++){
	            	
	                var pos = nodes[i].name.toLowerCase().indexOf(query)
	                if(query && pos != -1){
	                    
	                    matches++
	                    //show only certain amount to not kill browser 
	                    if (matches > matches_max){
	                        break;
	                    }
	                    
	                    var n = nodes[i].name;
	                    var t = nodes[i].type;
	                    var n_hl = n.substring(0,pos)
	                      +"<b>{0}</b>".format(n.substring(pos,pos+query.length))
	                      +n.substring(pos+query.length)                    
	                    match.push('<tr><td><a class="browser-{0}" href="{1}">{2}</a></td><td colspan="5"></td></tr>'.format(t,node_url.replace('__FPATH__',n),n_hl));
	                }
	                if(match.length >= matches_max){
	                    match.push('<tr><td>{0}</td><td colspan="5"></td></tr>'.format(truncated_lbl));
	                }
	                
	            }                       
	        }
	        if(query != ""){
	            YUD.setStyle('tbody','display','none');
	            YUD.setStyle('tbody_filtered','display','');
	            
	            if (match.length==0){
	              match.push('<tr><td>{0}</td><td colspan="5"></td></tr>'.format(nomatch_lbl));
	            }                           
	            
	            YUD.get('tbody_filtered').innerHTML = match.join("");   
	        }
	        else{
	            YUD.setStyle('tbody','display','');
	            YUD.setStyle('tbody_filtered','display','none');
	        }
	        
	    }
	};

	YUE.on(YUD.get('filter_activate'),'click',function(){
	    F.initFilter();
	})
	YUE.on(n_filter,'click',function(){
		if(YUD.hasClass(n_filter,'init')){
			n_filter.value = '';
			YUD.removeClass(n_filter,'init');
		}
	 });
	YUE.on(n_filter,'keyup',function(e){
	    clearTimeout(F.filterTimeout); 
	    F.filterTimeout = setTimeout(F.updateFilter(e),600);
	});
};


var initCodeMirror = function(textAreadId,resetUrl){  
    var myCodeMirror = CodeMirror.fromTextArea(YUD.get(textAreadId),{
           mode:  "null",
           lineNumbers:true
         });
    YUE.on('reset','click',function(e){
        window.location=resetUrl
    });
    
    YUE.on('file_enable','click',function(){
        YUD.setStyle('editor_container','display','');
        YUD.setStyle('upload_file_container','display','none');
        YUD.setStyle('filename_container','display','');
    });
    
    YUE.on('upload_file_enable','click',function(){
        YUD.setStyle('editor_container','display','none');
        YUD.setStyle('upload_file_container','display','');
        YUD.setStyle('filename_container','display','none');
    });	
};



var getIdentNode = function(n){
	//iterate thru nodes untill matched interesting node !
	
	if (typeof n == 'undefined'){
		return -1
	}
	
	if(typeof n.id != "undefined" && n.id.match('L[0-9]+')){
			return n
		}
	else{
		return getIdentNode(n.parentNode);
	}
};

var  getSelectionLink = function(selection_link_label) {
	return function(){
	    //get selection from start/to nodes    	
	    if (typeof window.getSelection != "undefined") {
	    	s = window.getSelection();
	
	       	from = getIdentNode(s.anchorNode);
	       	till = getIdentNode(s.focusNode);
	        
	        f_int = parseInt(from.id.replace('L',''));
	        t_int = parseInt(till.id.replace('L',''));
	        
	        if (f_int > t_int){
	        	//highlight from bottom 
	        	offset = -35;
	        	ranges = [t_int,f_int];
	        	
	        }
	        else{
	        	//highligth from top 
	        	offset = 35;
	        	ranges = [f_int,t_int];
	        }
	        
	        if (ranges[0] != ranges[1]){
	            if(YUD.get('linktt') == null){
	                hl_div = document.createElement('div');
	                hl_div.id = 'linktt';
	            }
	            anchor = '#L'+ranges[0]+'-'+ranges[1];
	            hl_div.innerHTML = '';
	            l = document.createElement('a');
	            l.href = location.href.substring(0,location.href.indexOf('#'))+anchor;
	            l.innerHTML = selection_link_label;
	            hl_div.appendChild(l);
	            
	            YUD.get('body').appendChild(hl_div);
	            
	            xy = YUD.getXY(till.id);
	            
	            YUD.addClass('linktt','yui-tt');
	            YUD.setStyle('linktt','top',xy[1]+offset+'px');
	            YUD.setStyle('linktt','left',xy[0]+'px');
	            YUD.setStyle('linktt','visibility','visible');
	        }
	        else{
	        	YUD.setStyle('linktt','visibility','hidden');
	        }
	    }
	}
};

var deleteNotification = function(url, notification_id,callbacks){
    var callback = { 
		success:function(o){
		    var obj = YUD.get(String("notification_"+notification_id));
		    if(obj.parentNode !== undefined){
				obj.parentNode.removeChild(obj);
			}
			_run_callbacks(callbacks);
		},
	    failure:function(o){
	        alert("error");
	    },
	};
    var postData = '_method=delete';
    var sUrl = url.replace('__NOTIFICATION_ID__',notification_id);
    var request = YAHOO.util.Connect.asyncRequest('POST', sUrl, 
    											  callback, postData);
};	


/**
 * QUICK REPO MENU
 */
var quick_repo_menu = function(){
    YUE.on(YUQ('.quick_repo_menu'),'click',function(e){
        var menu = e.currentTarget.firstElementChild.firstElementChild;
        if(YUD.hasClass(menu,'hidden')){
            YUD.addClass(e.currentTarget,'active');
            YUD.removeClass(menu,'hidden');
        }else{
            YUD.removeClass(e.currentTarget,'active');
            YUD.addClass(menu,'hidden');
        }
    })
};


/**
 * TABLE SORTING
 */

// returns a node from given html;
var fromHTML = function(html){
	  var _html = document.createElement('element');
	  _html.innerHTML = html;
	  return _html;
}
var get_rev = function(node){
    var n = node.firstElementChild.firstElementChild;
    
    if (n===null){
        return -1
    }
    else{
        out = n.firstElementChild.innerHTML.split(':')[0].replace('r','');
        return parseInt(out);
    }
}

var get_name = function(node){
	 var name = node.firstElementChild.children[2].innerHTML; 
	 return name
}
var get_group_name = function(node){
	var name = node.firstElementChild.children[1].innerHTML;
	return name
}
var get_date = function(node){
	var date_ = node.firstElementChild.innerHTML;
	return date_
}

var revisionSort = function(a, b, desc, field) {
	  
	  var a_ = fromHTML(a.getData(field));
	  var b_ = fromHTML(b.getData(field));
	  
	  // extract revisions from string nodes 
	  a_ = get_rev(a_)
	  b_ = get_rev(b_)
	      	  
	  var comp = YAHOO.util.Sort.compare;
	  var compState = comp(a_, b_, desc);
	  return compState;
};
var ageSort = function(a, b, desc, field) {
    var a_ = a.getData(field);
    var b_ = b.getData(field);
    
    var comp = YAHOO.util.Sort.compare;
    var compState = comp(a_, b_, desc);
    return compState;
};

var nameSort = function(a, b, desc, field) {
    var a_ = fromHTML(a.getData(field));
    var b_ = fromHTML(b.getData(field));
    
    // extract name from table
    a_ = get_name(a_)
    b_ = get_name(b_)          
    
    var comp = YAHOO.util.Sort.compare;
    var compState = comp(a_, b_, desc);
    return compState;
};

var groupNameSort = function(a, b, desc, field) {
    var a_ = fromHTML(a.getData(field));
    var b_ = fromHTML(b.getData(field));
    
    // extract name from table
    a_ = get_group_name(a_)
    b_ = get_group_name(b_)          
    
    var comp = YAHOO.util.Sort.compare;
    var compState = comp(a_, b_, desc);
    return compState;
};
var dateSort = function(a, b, desc, field) {
    var a_ = fromHTML(a.getData(field));
    var b_ = fromHTML(b.getData(field));
    
    // extract name from table
    a_ = get_date(a_)
    b_ = get_date(b_)          
    
    var comp = YAHOO.util.Sort.compare;
    var compState = comp(a_, b_, desc);
    return compState;
};