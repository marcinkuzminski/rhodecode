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

String.prototype.strip = function(char) {
    if(char === undefined){
        char = '\\s';
    }
    return this.replace(new RegExp('^'+char+'+|'+char+'+$','g'), '');
}
String.prototype.lstrip = function(char) {
    if(char === undefined){
        char = '\\s';
    }
    return this.replace(new RegExp('^'+char+'+'),'');
}
String.prototype.rstrip = function(char) {
    if(char === undefined){
        char = '\\s';
    }
    return this.replace(new RegExp(''+char+'+$'),'');
}


if(!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(needle) {
        for(var i = 0; i < this.length; i++) {
            if(this[i] === needle) {
                return i;
            }
        }
        return -1;
    };
}

// IE(CRAP) doesn't support previousElementSibling
var prevElementSibling = function( el ) {
    if( el.previousElementSibling ) {
        return el.previousElementSibling;
    } else {
        while( el = el.previousSibling ) {
            if( el.nodeType === 1 ) return el;
        }
    }
}

/**
 * SmartColorGenerator
 *
 *usage::
 *  var CG = new ColorGenerator();
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
 * PyRoutesJS
 *
 * Usage pyroutes.url('mark_error_fixed',{"error_id":error_id}) // /mark_error_fixed/<error_id>
 */
var pyroutes = (function() {
    // access global map defined in special file pyroutes
    var matchlist = PROUTES_MAP;
    var sprintf = (function() {
        function get_type(variable) {
            return Object.prototype.toString.call(variable).slice(8, -1).toLowerCase();
        }
        function str_repeat(input, multiplier) {
            for (var output = []; multiplier > 0; output[--multiplier] = input) {/* do nothing */}
            return output.join('');
        }

        var str_format = function() {
            if (!str_format.cache.hasOwnProperty(arguments[0])) {
                str_format.cache[arguments[0]] = str_format.parse(arguments[0]);
            }
            return str_format.format.call(null, str_format.cache[arguments[0]], arguments);
        };

        str_format.format = function(parse_tree, argv) {
            var cursor = 1, tree_length = parse_tree.length, node_type = '', arg, output = [], i, k, match, pad, pad_character, pad_length;
            for (i = 0; i < tree_length; i++) {
                node_type = get_type(parse_tree[i]);
                if (node_type === 'string') {
                    output.push(parse_tree[i]);
                }
                else if (node_type === 'array') {
                    match = parse_tree[i]; // convenience purposes only
                    if (match[2]) { // keyword argument
                        arg = argv[cursor];
                        for (k = 0; k < match[2].length; k++) {
                            if (!arg.hasOwnProperty(match[2][k])) {
                                throw(sprintf('[sprintf] property "%s" does not exist', match[2][k]));
                            }
                            arg = arg[match[2][k]];
                        }
                    }
                    else if (match[1]) { // positional argument (explicit)
                        arg = argv[match[1]];
                    }
                    else { // positional argument (implicit)
                        arg = argv[cursor++];
                    }

                    if (/[^s]/.test(match[8]) && (get_type(arg) != 'number')) {
                        throw(sprintf('[sprintf] expecting number but found %s', get_type(arg)));
                    }
                    switch (match[8]) {
                        case 'b': arg = arg.toString(2); break;
                        case 'c': arg = String.fromCharCode(arg); break;
                        case 'd': arg = parseInt(arg, 10); break;
                        case 'e': arg = match[7] ? arg.toExponential(match[7]) : arg.toExponential(); break;
                        case 'f': arg = match[7] ? parseFloat(arg).toFixed(match[7]) : parseFloat(arg); break;
                        case 'o': arg = arg.toString(8); break;
                        case 's': arg = ((arg = String(arg)) && match[7] ? arg.substring(0, match[7]) : arg); break;
                        case 'u': arg = Math.abs(arg); break;
                        case 'x': arg = arg.toString(16); break;
                        case 'X': arg = arg.toString(16).toUpperCase(); break;
                    }
                    arg = (/[def]/.test(match[8]) && match[3] && arg >= 0 ? '+'+ arg : arg);
                    pad_character = match[4] ? match[4] == '0' ? '0' : match[4].charAt(1) : ' ';
                    pad_length = match[6] - String(arg).length;
                    pad = match[6] ? str_repeat(pad_character, pad_length) : '';
                    output.push(match[5] ? arg + pad : pad + arg);
                }
            }
            return output.join('');
        };

        str_format.cache = {};

        str_format.parse = function(fmt) {
            var _fmt = fmt, match = [], parse_tree = [], arg_names = 0;
            while (_fmt) {
                if ((match = /^[^\x25]+/.exec(_fmt)) !== null) {
                    parse_tree.push(match[0]);
                }
                else if ((match = /^\x25{2}/.exec(_fmt)) !== null) {
                    parse_tree.push('%');
                }
                else if ((match = /^\x25(?:([1-9]\d*)\$|\(([^\)]+)\))?(\+)?(0|'[^$])?(-)?(\d+)?(?:\.(\d+))?([b-fosuxX])/.exec(_fmt)) !== null) {
                    if (match[2]) {
                        arg_names |= 1;
                        var field_list = [], replacement_field = match[2], field_match = [];
                        if ((field_match = /^([a-z_][a-z_\d]*)/i.exec(replacement_field)) !== null) {
                            field_list.push(field_match[1]);
                            while ((replacement_field = replacement_field.substring(field_match[0].length)) !== '') {
                                if ((field_match = /^\.([a-z_][a-z_\d]*)/i.exec(replacement_field)) !== null) {
                                    field_list.push(field_match[1]);
                                }
                                else if ((field_match = /^\[(\d+)\]/.exec(replacement_field)) !== null) {
                                    field_list.push(field_match[1]);
                                }
                                else {
                                    throw('[sprintf] huh?');
                                }
                            }
                        }
                        else {
                            throw('[sprintf] huh?');
                        }
                        match[2] = field_list;
                    }
                    else {
                        arg_names |= 2;
                    }
                    if (arg_names === 3) {
                        throw('[sprintf] mixing positional and named placeholders is not (yet) supported');
                    }
                    parse_tree.push(match);
                }
                else {
                    throw('[sprintf] huh?');
                }
                _fmt = _fmt.substring(match[0].length);
            }
            return parse_tree;
        };

        return str_format;
    })();

    var vsprintf = function(fmt, argv) {
        argv.unshift(fmt);
        return sprintf.apply(null, argv);
    };
    return {
        'url': function(route_name, params) {
            var result = route_name;
            if (typeof(params) != 'object'){
                params = {};
            }
            if (matchlist.hasOwnProperty(route_name)) {
                var route = matchlist[route_name];
                // param substitution
                for(var i=0; i < route[1].length; i++) {

                   if (!params.hasOwnProperty(route[1][i]))
                        throw new Error(route[1][i] + ' missing in "' + route_name + '" route generation');
                }
                result = sprintf(route[0], params);

                var ret = [];
                //extra params => GET
                for(param in params){
                    if (route[1].indexOf(param) == -1){
                        ret.push(encodeURIComponent(param) + "=" + encodeURIComponent(params[param]));
                    }
                }
                var _parts = ret.join("&");
                if(_parts){
                    result = result +'?'+ _parts
                }
            }

            return result;
        },
        'register': function(route_name, route_tmpl, req_params) {
            if (typeof(req_params) != 'object') {
                req_params = [];
            }
            //fix escape
            route_tmpl = unescape(route_tmpl);
            keys = [];
            for (o in req_params){
                keys.push(req_params[o])
            }
            matchlist[route_name] = [
                route_tmpl,
                keys
            ]
        },
        '_routes': function(){
            return matchlist;
        }
    }
})();



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
 * turns objects into GET query string
 */
var toQueryString = function(o) {
    if(typeof o !== 'object') {
        return false;
    }
    var _p, _qs = [];
    for(_p in o) {
        _qs.push(encodeURIComponent(_p) + '=' + encodeURIComponent(o[_p]));
    }
    return _qs.join('&');
};

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
            YUD.get(container).innerHTML='<span class="error_red">ERROR: {0}</span>'.format(o.status);
            YUD.setStyle(container,'opacity','1.0');
        },
        cache:false
    },args);

};

var ajaxGET = function(url,success) {
    // Set special header for ajax == HTTP_X_PARTIAL_XHR
    YUC.initHeader('X-PARTIAL-XHR',true);

    var sUrl = url;
    var callback = {
        success: success,
        failure: function (o) {
            if (o.status != 0) {
                alert("error: " + o.statusText);
            };
        },
    };

    var request = YAHOO.util.Connect.asyncRequest('GET', sUrl, callback);
    return request;
};



var ajaxPOST = function(url,postData,success) {
    // Set special header for ajax == HTTP_X_PARTIAL_XHR
    YUC.initHeader('X-PARTIAL-XHR',true);

    var sUrl = url;
    var callback = {
        success: success,
        failure: function (o) {
            alert("error");
        },
    };
    var postData = toQueryString(postData);
    var request = YAHOO.util.Connect.asyncRequest('POST', sUrl, callback, postData);
    return request;
};


/**
 * tooltip activate
 */
var tooltip_activate = function(){
    yt = YAHOO.yuitip.main;
    YUE.onDOMReady(yt.init);
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
 * show changeset tooltip
 */
var show_changeset_tooltip = function(){
    YUE.on(YUD.getElementsByClassName('lazy-cs'), 'mouseover', function(e){
        var target = e.currentTarget;
        var rid = YUD.getAttribute(target,'raw_id');
        var repo_name = YUD.getAttribute(target,'repo_name');
        var ttid = 'tt-'+rid;
        var success = function(o){
            var json = JSON.parse(o.responseText);
            YUD.addClass(target,'tooltip')
            YUD.setAttribute(target, 'title',json['message']);
            YAHOO.yuitip.main.show_yuitip(e, target);
        }
        if(rid && !YUD.hasClass(target, 'tooltip')){
            YUD.setAttribute(target,'id',ttid);
            YUD.setAttribute(target, 'title',_TM['loading...']);
            YAHOO.yuitip.main.set_listeners(target);
            YAHOO.yuitip.main.show_yuitip(e, target);
            var url = pyroutes.url('changeset_info', {"repo_name":repo_name, "revision": rid});
            ajaxGET(url, success)
        }
    });
};

var onSuccessFollow = function(target){
    var f = YUD.get(target);
    var f_cnt = YUD.get('current_followers_count');

    if(YUD.hasClass(f, 'follow')){
        f.setAttribute('class','following');
        f.setAttribute('title',_TM['Stop following this repository']);

        if(f_cnt){
            var cnt = Number(f_cnt.innerHTML)+1;
            f_cnt.innerHTML = cnt;
        }
    }
    else{
        f.setAttribute('class','follow');
        f.setAttribute('title',_TM['Start following this repository']);
        if(f_cnt){
            var cnt = Number(f_cnt.innerHTML)-1;
            f_cnt.innerHTML = cnt;
        }
    }
}

var toggleFollowingUser = function(target,fallows_user_id,token,user_id){
    args = 'follows_user_id='+fallows_user_id;
    args+= '&amp;auth_token='+token;
    if(user_id != undefined){
        args+="&amp;user_id="+user_id;
    }
    YUC.asyncRequest('POST',TOGGLE_FOLLOW_URL,{
        success:function(o){
            onSuccessFollow(target);
        }
    },args);
    return false;
}

var toggleFollowingRepo = function(target,fallows_repo_id,token,user_id){

    args = 'follows_repo_id='+fallows_repo_id;
    args+= '&amp;auth_token='+token;
    if(user_id != undefined){
        args+="&amp;user_id="+user_id;
    }
    YUC.asyncRequest('POST',TOGGLE_FOLLOW_URL,{
        success:function(o){
            onSuccessFollow(target);
        }
    },args);
    return false;
}

var showRepoSize = function(target, repo_name, token){
    var args= 'auth_token='+token;

    if(!YUD.hasClass(target, 'loaded')){
        YUD.get(target).innerHTML = _TM['Loading ...'];
        var url = pyroutes.url('repo_size', {"repo_name":repo_name});
        YUC.asyncRequest('POST',url,{
            success:function(o){
                YUD.get(target).innerHTML = JSON.parse(o.responseText);
                YUD.addClass(target, 'loaded');
            }
        },args);
    }
    return false;
}

/**
 * TOOLTIP IMPL.
 */
YAHOO.namespace('yuitip');
YAHOO.yuitip.main = {

    $:          YAHOO.util.Dom.get,

    bgColor:    '#000',
    speed:      0.3,
    opacity:    0.9,
    offset:     [15,15],
    useAnim:    false,
    maxWidth:   600,
    add_links:  false,
    yuitips:    [],

    set_listeners: function(tt){
        YUE.on(tt, 'mouseover', yt.show_yuitip,  tt);
        YUE.on(tt, 'mousemove', yt.move_yuitip,  tt);
        YUE.on(tt, 'mouseout',  yt.close_yuitip, tt);
    },

    init: function(){
        yt.tipBox = yt.$('tip-box');
        if(!yt.tipBox){
            yt.tipBox = document.createElement('div');
            document.body.appendChild(yt.tipBox);
            yt.tipBox.id = 'tip-box';
        }

        YUD.setStyle(yt.tipBox, 'display', 'none');
        YUD.setStyle(yt.tipBox, 'position', 'absolute');
        if(yt.maxWidth !== null){
            YUD.setStyle(yt.tipBox, 'max-width', yt.maxWidth+'px');
        }

        var yuitips = YUD.getElementsByClassName('tooltip');

        if(yt.add_links === true){
            var links = document.getElementsByTagName('a');
            var linkLen = links.length;
            for(i=0;i<linkLen;i++){
                yuitips.push(links[i]);
            }
        }

        var yuiLen = yuitips.length;

        for(i=0;i<yuiLen;i++){
            yt.set_listeners(yuitips[i]);
        }
    },

    show_yuitip: function(e, el){
        YUE.stopEvent(e);
        if(el.tagName.toLowerCase() === 'img'){
            yt.tipText = el.alt ? el.alt : '';
        } else {
            yt.tipText = el.title ? el.title : '';
        }

        if(yt.tipText !== ''){
            // save org title
            YUD.setAttribute(el, 'tt_title', yt.tipText);
            // reset title to not show org tooltips
            YUD.setAttribute(el, 'title', '');

            yt.tipBox.innerHTML = yt.tipText;
            YUD.setStyle(yt.tipBox, 'display', 'block');
            if(yt.useAnim === true){
                YUD.setStyle(yt.tipBox, 'opacity', '0');
                var newAnim = new YAHOO.util.Anim(yt.tipBox,
                    {
                        opacity: { to: yt.opacity }
                    }, yt.speed, YAHOO.util.Easing.easeOut
                );
                newAnim.animate();
            }
        }
    },

    move_yuitip: function(e, el){
        YUE.stopEvent(e);
        var movePos = YUE.getXY(e);
        YUD.setStyle(yt.tipBox, 'top', (movePos[1] + yt.offset[1]) + 'px');
        YUD.setStyle(yt.tipBox, 'left', (movePos[0] + yt.offset[0]) + 'px');
    },

    close_yuitip: function(e, el){
        YUE.stopEvent(e);

        if(yt.useAnim === true){
            var newAnim = new YAHOO.util.Anim(yt.tipBox,
                {
                    opacity: { to: 0 }
                }, yt.speed, YAHOO.util.Easing.easeOut
            );
            newAnim.animate();
        } else {
            YUD.setStyle(yt.tipBox, 'display', 'none');
        }
        YUD.setAttribute(el,'title', YUD.getAttribute(el, 'tt_title'));
    }
}

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

var tableTr = function(cls, body){
    var _el = document.createElement('div');
    var cont = new YAHOO.util.Element(body);
    var comment_id = fromHTML(body).children[0].id.split('comment-')[1];
    var id = 'comment-tr-{0}'.format(comment_id);
    var _html = ('<table><tbody><tr id="{0}" class="{1}">'+
                  '<td class="lineno-inline new-inline"></td>'+
                  '<td class="lineno-inline old-inline"></td>'+
                  '<td>{2}</td>'+
                 '</tr></tbody></table>').format(id, cls, body);
    _el.innerHTML = _html;
    return _el.children[0].children[0].children[0];
};

/** comments **/
var removeInlineForm = function(form) {
    form.parentNode.removeChild(form);
};

var createInlineForm = function(parent_tr, f_path, line) {
    var tmpl = YUD.get('comment-inline-form-template').innerHTML;
    tmpl = tmpl.format(f_path, line);
    var form = tableTr('comment-form-inline',tmpl)

    // create event for hide button
    form = new YAHOO.util.Element(form);
    var form_hide_button = new YAHOO.util.Element(YUD.getElementsByClassName('hide-inline-form',null,form)[0]);
    form_hide_button.on('click', function(e) {
        var newtr = e.currentTarget.parentNode.parentNode.parentNode.parentNode.parentNode;
        if(YUD.hasClass(newtr.nextElementSibling,'inline-comments-button')){
            YUD.setStyle(newtr.nextElementSibling,'display','');
        }
        removeInlineForm(newtr);
        YUD.removeClass(parent_tr, 'form-open');
        YUD.removeClass(parent_tr, 'hl-comment');

    });

    return form
};

/**
 * Inject inline comment for on given TR this tr should be always an .line
 * tr containing the line. Code will detect comment, and always put the comment
 * block at the very bottom
 */
var injectInlineForm = function(tr){
      if(!YUD.hasClass(tr, 'line')){
          return
      }
      var submit_url = AJAX_COMMENT_URL;
      var _td = YUD.getElementsByClassName('code',null,tr)[0];
      if(YUD.hasClass(tr,'form-open') || YUD.hasClass(tr,'context') || YUD.hasClass(_td,'no-comment')){
          return
      }
      YUD.addClass(tr,'form-open');
      YUD.addClass(tr,'hl-comment');
      var node = YUD.getElementsByClassName('full_f_path',null,tr.parentNode.parentNode.parentNode)[0];
      var f_path = YUD.getAttribute(node,'path');
      var lineno = getLineNo(tr);
      var form = createInlineForm(tr, f_path, lineno, submit_url);

      var parent = tr;
      while (1){
          var n = parent.nextElementSibling;
          // next element are comments !
          if(YUD.hasClass(n,'inline-comments')){
              parent = n;
          }
          else{
              break;
          }
      }
      YUD.insertAfter(form,parent);
      var f = YUD.get(form);
      var overlay = YUD.getElementsByClassName('overlay',null,f)[0];
      var _form = YUD.getElementsByClassName('inline-form',null,f)[0];

      YUE.on(YUD.get(_form), 'submit',function(e){
          YUE.preventDefault(e);

          //ajax submit
          var text = YUD.get('text_'+lineno).value;
          var postData = {
                'text':text,
                'f_path':f_path,
                'line':lineno
          };

          if(lineno === undefined){
              alert('missing line !');
              return
          }
          if(f_path === undefined){
              alert('missing file path !');
              return
          }

          if(text == ""){
              return
          }

          var success = function(o){
              YUD.removeClass(tr, 'form-open');
              removeInlineForm(f);
              var json_data = JSON.parse(o.responseText);
              renderInlineComment(json_data);
          };

          if (YUD.hasClass(overlay,'overlay')){
              var w = _form.offsetWidth;
              var h = _form.offsetHeight;
              YUD.setStyle(overlay,'width',w+'px');
              YUD.setStyle(overlay,'height',h+'px');
          }
          YUD.addClass(overlay, 'submitting');

          ajaxPOST(submit_url, postData, success);
      });

      YUE.on('preview-btn_'+lineno, 'click', function(e){
           var _text = YUD.get('text_'+lineno).value;
           if(!_text){
               return
           }
           var post_data = {'text': _text};
           YUD.addClass('preview-box_'+lineno, 'unloaded');
           YUD.get('preview-box_'+lineno).innerHTML = _TM['Loading ...'];
           YUD.setStyle('edit-container_'+lineno, 'display', 'none');
           YUD.setStyle('preview-container_'+lineno, 'display', '');

           var url = pyroutes.url('changeset_comment_preview', {'repo_name': REPO_NAME});
           ajaxPOST(url,post_data,function(o){
               YUD.get('preview-box_'+lineno).innerHTML = o.responseText;
               YUD.removeClass('preview-box_'+lineno, 'unloaded');
           })
       })
       YUE.on('edit-btn_'+lineno, 'click', function(e){
           YUD.setStyle('edit-container_'+lineno, 'display', '');
           YUD.setStyle('preview-container_'+lineno, 'display', 'none');
       })


      setTimeout(function(){
          // callbacks
          tooltip_activate();
          MentionsAutoComplete('text_'+lineno, 'mentions_container_'+lineno,
                             _USERS_AC_DATA, _GROUPS_AC_DATA);
          var _e = YUD.get('text_'+lineno);
          if(_e){
              _e.focus();
          }
      },10)
};

var deleteComment = function(comment_id){
    var url = AJAX_COMMENT_DELETE_URL.replace('__COMMENT_ID__',comment_id);
    var postData = {'_method':'delete'};
    var success = function(o){
        var n = YUD.get('comment-tr-'+comment_id);
        var root = prevElementSibling(prevElementSibling(n));
        n.parentNode.removeChild(n);

        // scann nodes, and attach add button to last one only for TR
        // which are the inline comments
        if(root && root.tagName == 'TR'){
            placeAddButton(root);
        }
    }
    ajaxPOST(url,postData,success);
}

var createInlineAddButton = function(tr){

    var label = TRANSLATION_MAP['Add another comment'];

    var html_el = document.createElement('div');
    YUD.addClass(html_el, 'add-comment');
    html_el.innerHTML = '<span class="ui-btn">{0}</span>'.format(label);

    var add = new YAHOO.util.Element(html_el);
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

var placeAddButton = function(target_tr){
    if(!target_tr){
        return
    }
    var last_node = target_tr;
    //scann
      while (1){
          var n = last_node.nextElementSibling;
          // next element are comments !
          if(YUD.hasClass(n,'inline-comments')){
              last_node = n;
              //also remove the comment button from previous
              var comment_add_buttons = YUD.getElementsByClassName('add-comment',null,last_node);
              for(var i=0;i<comment_add_buttons.length;i++){
                  var b = comment_add_buttons[i];
                  b.parentNode.removeChild(b);
              }
          }
          else{
              break;
          }
      }

    var add = createInlineAddButton(target_tr);
    // get the comment div
    var comment_block = YUD.getElementsByClassName('comment',null,last_node)[0];
    // attach add button
    YUD.insertAfter(add,comment_block);
}

/**
 * Places the inline comment into the changeset block in proper line position
 */
var placeInline = function(target_container,lineno,html){
      var lineid = "{0}_{1}".format(target_container,lineno);
      var target_line = YUD.get(lineid);
      var comment = new YAHOO.util.Element(tableTr('inline-comments',html))

      // check if there are comments already !
      var parent = target_line.parentNode;
      var root_parent = parent;
      while (1){
          var n = parent.nextElementSibling;
          // next element are comments !
          if(YUD.hasClass(n,'inline-comments')){
              parent = n;
          }
          else{
              break;
          }
      }
      // put in the comment at the bottom
      YUD.insertAfter(comment,parent);

      // scann nodes, and attach add button to last one
      placeAddButton(root_parent);

      return target_line;
}

/**
 * make a single inline comment and place it inside
 */
var renderInlineComment = function(json_data){
    try{
      var html =  json_data['rendered_text'];
      var lineno = json_data['line_no'];
      var target_id = json_data['target_id'];
      placeInline(target_id, lineno, html);

    }catch(e){
      console.log(e);
    }
}

/**
 * Iterates over all the inlines, and places them inside proper blocks of data
 */
var renderInlineComments = function(file_comments){
    for (f in file_comments){
        // holding all comments for a FILE
        var box = file_comments[f];

        var target_id = YUD.getAttribute(box,'target_id');
        // actually comments with line numbers
        var comments = box.children;
        for(var i=0; i<comments.length; i++){
            var data = {
                'rendered_text': comments[i].outerHTML,
                'line_no': YUD.getAttribute(comments[i],'line'),
                'target_id': target_id
            }
            renderInlineComment(data);
        }
    }
}

var fileBrowserListeners = function(current_url, node_list_url, url_base){
    var current_url_branch = +"?branch=__BRANCH__";

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
      YUC.asyncRequest('GET', node_list_url, {
          success:function(o){
            nodes = JSON.parse(o.responseText).nodes;
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
                        var new_url = url_base.replace('__FPATH__',n);
                        match.push('<tr><td><a class="browser-{0}" href="{1}">{2}</a></td><td colspan="5"></td></tr>'.format(t,new_url,n_hl));
                    }
                    if(match.length >= matches_max){
                        match.push('<tr><td>{0}</td><td colspan="5"></td></tr>'.format(_TM['Search truncated']));
                    }
                }
            }
            if(query != ""){
                YUD.setStyle('tbody','display','none');
                YUD.setStyle('tbody_filtered','display','');

                if (match.length==0){
                  match.push('<tr><td>{0}</td><td colspan="5"></td></tr>'.format(_TM['No matching files']));
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

var  getSelectionLink = function(e) {

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
        // if we select more than 2 lines
        if (ranges[0] != ranges[1]){
            if(YUD.get('linktt') == null){
                hl_div = document.createElement('div');
                hl_div.id = 'linktt';
            }
            hl_div.innerHTML = '';

            anchor = '#L'+ranges[0]+'-'+ranges[1];
            var link = document.createElement('a');
            link.href = location.href.substring(0,location.href.indexOf('#'))+anchor;
            link.innerHTML = _TM['Selection link'];
            hl_div.appendChild(link);
            YUD.get('body').appendChild(hl_div);

            xy = YUD.getXY(till.id);

            YUD.addClass('linktt', 'hl-tip-box');
            YUD.setStyle('linktt','top',xy[1]+offset+'px');
            YUD.setStyle('linktt','left',xy[0]+'px');
            YUD.setStyle('linktt','visibility','visible');

        }
        else{
            YUD.setStyle('linktt','visibility','hidden');
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

var readNotification = function(url, notification_id,callbacks){
    var callback = {
        success:function(o){
            var obj = YUD.get(String("notification_"+notification_id));
            YUD.removeClass(obj, 'unread');
            var r_button = YUD.getElementsByClassName('read-notification',null,obj.children[0])[0];

            if(r_button.parentNode !== undefined){
                r_button.parentNode.removeChild(r_button);
            }
            _run_callbacks(callbacks);
        },
        failure:function(o){
            alert("error");
        },
    };
    var postData = '_method=put';
    var sUrl = url.replace('__NOTIFICATION_ID__',notification_id);
    var request = YAHOO.util.Connect.asyncRequest('POST', sUrl,
                                                  callback, postData);
};

/** MEMBERS AUTOCOMPLETE WIDGET **/

var MembersAutoComplete = function (divid, cont, users_list, groups_list) {
    var myUsers = users_list;
    var myGroups = groups_list;

    // Define a custom search function for the DataSource of users
    var matchUsers = function (sQuery) {
            // Case insensitive matching
            var query = sQuery.toLowerCase();
            var i = 0;
            var l = myUsers.length;
            var matches = [];

            // Match against each name of each contact
            for (; i < l; i++) {
                contact = myUsers[i];
                if (((contact.fname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.lname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.nname) && ((contact.nname).toLowerCase().indexOf(query) > -1))) {
                       matches[matches.length] = contact;
                   }
            }
            return matches;
        };

    // Define a custom search function for the DataSource of userGroups
    var matchGroups = function (sQuery) {
            // Case insensitive matching
            var query = sQuery.toLowerCase();
            var i = 0;
            var l = myGroups.length;
            var matches = [];

            // Match against each name of each contact
            for (; i < l; i++) {
                matched_group = myGroups[i];
                if (matched_group.grname.toLowerCase().indexOf(query) > -1) {
                    matches[matches.length] = matched_group;
                }
            }
            return matches;
        };

    //match all
    var matchAll = function (sQuery) {
            u = matchUsers(sQuery);
            g = matchGroups(sQuery);
            return u.concat(g);
        };

    // DataScheme for members
    var memberDS = new YAHOO.util.FunctionDataSource(matchAll);
    memberDS.responseSchema = {
        fields: ["id", "fname", "lname", "nname", "grname", "grmembers", "gravatar_lnk"]
    };

    // DataScheme for owner
    var ownerDS = new YAHOO.util.FunctionDataSource(matchUsers);
    ownerDS.responseSchema = {
        fields: ["id", "fname", "lname", "nname", "gravatar_lnk"]
    };

    // Instantiate AutoComplete for perms
    var membersAC = new YAHOO.widget.AutoComplete(divid, cont, memberDS);
    membersAC.useShadow = false;
    membersAC.resultTypeList = false;
    membersAC.animVert = false;
    membersAC.animHoriz = false;
    membersAC.animSpeed = 0.1;

    // Instantiate AutoComplete for owner
    var ownerAC = new YAHOO.widget.AutoComplete("user", "owner_container", ownerDS);
    ownerAC.useShadow = false;
    ownerAC.resultTypeList = false;
    ownerAC.animVert = false;
    ownerAC.animHoriz = false;
    ownerAC.animSpeed = 0.1;

    // Helper highlight function for the formatter
    var highlightMatch = function (full, snippet, matchindex) {
            return full.substring(0, matchindex)
            + "<span class='match'>"
            + full.substr(matchindex, snippet.length)
            + "</span>" + full.substring(matchindex + snippet.length);
        };

    // Custom formatter to highlight the matching letters
    var custom_formatter = function (oResultData, sQuery, sResultMatch) {
            var query = sQuery.toLowerCase();
            var _gravatar = function(res, em, group){
                if (group !== undefined){
                    em = '/images/icons/group.png'
                }
                tmpl = '<div class="ac-container-wrap"><img class="perm-gravatar-ac" src="{0}"/>{1}</div>'
                return tmpl.format(em,res)
            }
            // group
            if (oResultData.grname != undefined) {
                var grname = oResultData.grname;
                var grmembers = oResultData.grmembers;
                var grnameMatchIndex = grname.toLowerCase().indexOf(query);
                var grprefix = "{0}: ".format(_TM['Group']);
                var grsuffix = " (" + grmembers + "  )";
                var grsuffix = " ({0}  {1})".format(grmembers, _TM['members']);

                if (grnameMatchIndex > -1) {
                    return _gravatar(grprefix + highlightMatch(grname, query, grnameMatchIndex) + grsuffix,null,true);
                }
                return _gravatar(grprefix + oResultData.grname + grsuffix, null,true);
            // Users
            } else if (oResultData.nname != undefined) {
                var fname = oResultData.fname || "";
                var lname = oResultData.lname || "";
                var nname = oResultData.nname;

                // Guard against null value
                var fnameMatchIndex = fname.toLowerCase().indexOf(query),
                    lnameMatchIndex = lname.toLowerCase().indexOf(query),
                    nnameMatchIndex = nname.toLowerCase().indexOf(query),
                    displayfname, displaylname, displaynname;

                if (fnameMatchIndex > -1) {
                    displayfname = highlightMatch(fname, query, fnameMatchIndex);
                } else {
                    displayfname = fname;
                }

                if (lnameMatchIndex > -1) {
                    displaylname = highlightMatch(lname, query, lnameMatchIndex);
                } else {
                    displaylname = lname;
                }

                if (nnameMatchIndex > -1) {
                    displaynname = "(" + highlightMatch(nname, query, nnameMatchIndex) + ")";
                } else {
                    displaynname = nname ? "(" + nname + ")" : "";
                }

                return _gravatar(displayfname + " " + displaylname + " " + displaynname, oResultData.gravatar_lnk);
            } else {
                return '';
            }
        };
    membersAC.formatResult = custom_formatter;
    ownerAC.formatResult = custom_formatter;

    var myHandler = function (sType, aArgs) {
            var nextId = divid.split('perm_new_member_name_')[1];
            var myAC = aArgs[0]; // reference back to the AC instance
            var elLI = aArgs[1]; // reference to the selected LI element
            var oData = aArgs[2]; // object literal of selected item's result data
            //fill the autocomplete with value
            if (oData.nname != undefined) {
                //users
                myAC.getInputEl().value = oData.nname;
                YUD.get('perm_new_member_type_'+nextId).value = 'user';
            } else {
                //groups
                myAC.getInputEl().value = oData.grname;
                YUD.get('perm_new_member_type_'+nextId).value = 'users_group';
            }
        };

    membersAC.itemSelectEvent.subscribe(myHandler);
    if(ownerAC.itemSelectEvent){
        ownerAC.itemSelectEvent.subscribe(myHandler);
    }

    return {
        memberDS: memberDS,
        ownerDS: ownerDS,
        membersAC: membersAC,
        ownerAC: ownerAC,
    };
}


var MentionsAutoComplete = function (divid, cont, users_list, groups_list) {
    var myUsers = users_list;
    var myGroups = groups_list;

    // Define a custom search function for the DataSource of users
    var matchUsers = function (sQuery) {
            var org_sQuery = sQuery;
            if(this.mentionQuery == null){
                return []
            }
            sQuery = this.mentionQuery;
            // Case insensitive matching
            var query = sQuery.toLowerCase();
            var i = 0;
            var l = myUsers.length;
            var matches = [];

            // Match against each name of each contact
            for (; i < l; i++) {
                contact = myUsers[i];
                if (((contact.fname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.lname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.nname) && ((contact.nname).toLowerCase().indexOf(query) > -1))) {
                    matches[matches.length] = contact;
                }
            }
            return matches
        };

    //match all
    var matchAll = function (sQuery) {
            u = matchUsers(sQuery);
            return u
        };

    // DataScheme for owner
    var ownerDS = new YAHOO.util.FunctionDataSource(matchUsers);

    ownerDS.responseSchema = {
        fields: ["id", "fname", "lname", "nname", "gravatar_lnk"]
    };

    // Instantiate AutoComplete for mentions
    var ownerAC = new YAHOO.widget.AutoComplete(divid, cont, ownerDS);
    ownerAC.useShadow = false;
    ownerAC.resultTypeList = false;
    ownerAC.suppressInputUpdate = true;
    ownerAC.animVert = false;
    ownerAC.animHoriz = false;
    ownerAC.animSpeed = 0.1;

    // Helper highlight function for the formatter
    var highlightMatch = function (full, snippet, matchindex) {
            return full.substring(0, matchindex)
            + "<span class='match'>"
            + full.substr(matchindex, snippet.length)
            + "</span>" + full.substring(matchindex + snippet.length);
        };

    // Custom formatter to highlight the matching letters
    ownerAC.formatResult = function (oResultData, sQuery, sResultMatch) {
            var org_sQuery = sQuery;
            if(this.dataSource.mentionQuery != null){
                sQuery = this.dataSource.mentionQuery;
            }

            var query = sQuery.toLowerCase();
            var _gravatar = function(res, em, group){
                if (group !== undefined){
                    em = '/images/icons/group.png'
                }
                tmpl = '<div class="ac-container-wrap"><img class="perm-gravatar-ac" src="{0}"/>{1}</div>'
                return tmpl.format(em,res)
            }
            if (oResultData.nname != undefined) {
                var fname = oResultData.fname || "";
                var lname = oResultData.lname || "";
                var nname = oResultData.nname;

                // Guard against null value
                var fnameMatchIndex = fname.toLowerCase().indexOf(query),
                    lnameMatchIndex = lname.toLowerCase().indexOf(query),
                    nnameMatchIndex = nname.toLowerCase().indexOf(query),
                    displayfname, displaylname, displaynname;

                if (fnameMatchIndex > -1) {
                    displayfname = highlightMatch(fname, query, fnameMatchIndex);
                } else {
                    displayfname = fname;
                }

                if (lnameMatchIndex > -1) {
                    displaylname = highlightMatch(lname, query, lnameMatchIndex);
                } else {
                    displaylname = lname;
                }

                if (nnameMatchIndex > -1) {
                    displaynname = "(" + highlightMatch(nname, query, nnameMatchIndex) + ")";
                } else {
                    displaynname = nname ? "(" + nname + ")" : "";
                }

                return _gravatar(displayfname + " " + displaylname + " " + displaynname, oResultData.gravatar_lnk);
            } else {
                return '';
            }
        };

    if(ownerAC.itemSelectEvent){
        ownerAC.itemSelectEvent.subscribe(function (sType, aArgs) {

            var myAC = aArgs[0]; // reference back to the AC instance
            var elLI = aArgs[1]; // reference to the selected LI element
            var oData = aArgs[2]; // object literal of selected item's result data
            //fill the autocomplete with value
            if (oData.nname != undefined) {
                //users
                //Replace the mention name with replaced
                var re = new RegExp();
                var org = myAC.getInputEl().value;
                var chunks = myAC.dataSource.chunks
                // replace middle chunk(the search term) with actuall  match
                chunks[1] = chunks[1].replace('@'+myAC.dataSource.mentionQuery,
                                              '@'+oData.nname+' ');
                myAC.getInputEl().value = chunks.join('')
                YUD.get(myAC.getInputEl()).focus(); // Y U NO WORK !?
            } else {
                //groups
                myAC.getInputEl().value = oData.grname;
                YUD.get('perm_new_member_type').value = 'users_group';
            }
        });
    }

    // in this keybuffer we will gather current value of search !
    // since we need to get this just when someone does `@` then we do the
    // search
    ownerAC.dataSource.chunks = [];
    ownerAC.dataSource.mentionQuery = null;

    ownerAC.get_mention = function(msg, max_pos) {
        var org = msg;
        var re = new RegExp('(?:^@|\s@)([a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+)$')
        var chunks  = [];


        // cut first chunk until curret pos
        var to_max = msg.substr(0, max_pos);
        var at_pos = Math.max(0,to_max.lastIndexOf('@')-1);
        var msg2 = to_max.substr(at_pos);

        chunks.push(org.substr(0,at_pos))// prefix chunk
        chunks.push(msg2)                // search chunk
        chunks.push(org.substr(max_pos)) // postfix chunk

        // clean up msg2 for filtering and regex match
        var msg2 = msg2.lstrip(' ').lstrip('\n');

        if(re.test(msg2)){
            var unam = re.exec(msg2)[1];
            return [unam, chunks];
        }
        return [null, null];
    };

    if (ownerAC.textboxKeyUpEvent){
        ownerAC.textboxKeyUpEvent.subscribe(function(type, args){

            var ac_obj = args[0];
            var currentMessage = args[1];
            var currentCaretPosition = args[0]._elTextbox.selectionStart;

            var unam = ownerAC.get_mention(currentMessage, currentCaretPosition);
            var curr_search = null;
            if(unam[0]){
                curr_search = unam[0];
            }

            ownerAC.dataSource.chunks = unam[1];
            ownerAC.dataSource.mentionQuery = curr_search;

        })
    }
    return {
        ownerDS: ownerDS,
        ownerAC: ownerAC,
    };
}

var addReviewMember = function(id,fname,lname,nname,gravatar_link){
    var members  = YUD.get('review_members');
    var tmpl = '<li id="reviewer_{2}">'+
    '<div class="reviewers_member">'+
      '<div class="gravatar"><img alt="gravatar" src="{0}"/> </div>'+
      '<div style="float:left">{1}</div>'+
      '<input type="hidden" value="{2}" name="review_members" />'+
      '<span class="delete_icon action_button" onclick="removeReviewMember({2})"></span>'+
    '</div>'+
    '</li>' ;
    var displayname = "{0} {1} ({2})".format(fname,lname,nname);
    var element = tmpl.format(gravatar_link,displayname,id);
    // check if we don't have this ID already in
    var ids = [];
    var _els = YUQ('#review_members li');
    for (el in _els){
        ids.push(_els[el].id)
    }
    if(ids.indexOf('reviewer_'+id) == -1){
        //only add if it's not there
        members.innerHTML += element;
    }

}

var removeReviewMember = function(reviewer_id, repo_name, pull_request_id){
    var el = YUD.get('reviewer_{0}'.format(reviewer_id));
    if (el.parentNode !== undefined){
        el.parentNode.removeChild(el);
    }
}

var updateReviewers = function(reviewers_ids, repo_name, pull_request_id){
    if (reviewers_ids === undefined){
      var reviewers_ids = [];
      var ids = YUQ('#review_members input');
      for(var i=0; i<ids.length;i++){
          var id = ids[i].value
          reviewers_ids.push(id);
      }
    }
    var url = pyroutes.url('pullrequest_update', {"repo_name":repo_name,
                                                  "pull_request_id": pull_request_id});
    var postData = {'_method':'put',
                    'reviewers_ids': reviewers_ids};
    var success = function(o){
        window.location.reload();
    }
    ajaxPOST(url,postData,success);
}

var PullRequestAutoComplete = function (divid, cont, users_list, groups_list) {
    var myUsers = users_list;
    var myGroups = groups_list;

    // Define a custom search function for the DataSource of users
    var matchUsers = function (sQuery) {
            // Case insensitive matching
            var query = sQuery.toLowerCase();
            var i = 0;
            var l = myUsers.length;
            var matches = [];

            // Match against each name of each contact
            for (; i < l; i++) {
                contact = myUsers[i];
                if (((contact.fname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.lname+"").toLowerCase().indexOf(query) > -1) ||
                     ((contact.nname) && ((contact.nname).toLowerCase().indexOf(query) > -1))) {
                       matches[matches.length] = contact;
                   }
            }
            return matches;
        };

    // Define a custom search function for the DataSource of userGroups
    var matchGroups = function (sQuery) {
            // Case insensitive matching
            var query = sQuery.toLowerCase();
            var i = 0;
            var l = myGroups.length;
            var matches = [];

            // Match against each name of each contact
            for (; i < l; i++) {
                matched_group = myGroups[i];
                if (matched_group.grname.toLowerCase().indexOf(query) > -1) {
                    matches[matches.length] = matched_group;
                }
            }
            return matches;
        };

    //match all
    var matchAll = function (sQuery) {
            u = matchUsers(sQuery);
            return u
        };

    // DataScheme for owner
    var ownerDS = new YAHOO.util.FunctionDataSource(matchUsers);

    ownerDS.responseSchema = {
        fields: ["id", "fname", "lname", "nname", "gravatar_lnk"]
    };

    // Instantiate AutoComplete for mentions
    var reviewerAC = new YAHOO.widget.AutoComplete(divid, cont, ownerDS);
    reviewerAC.useShadow = false;
    reviewerAC.resultTypeList = false;
    reviewerAC.suppressInputUpdate = true;
    reviewerAC.animVert = false;
    reviewerAC.animHoriz = false;
    reviewerAC.animSpeed = 0.1;

    // Helper highlight function for the formatter
    var highlightMatch = function (full, snippet, matchindex) {
            return full.substring(0, matchindex)
            + "<span class='match'>"
            + full.substr(matchindex, snippet.length)
            + "</span>" + full.substring(matchindex + snippet.length);
        };

    // Custom formatter to highlight the matching letters
    reviewerAC.formatResult = function (oResultData, sQuery, sResultMatch) {
            var org_sQuery = sQuery;
            if(this.dataSource.mentionQuery != null){
                sQuery = this.dataSource.mentionQuery;
            }

            var query = sQuery.toLowerCase();
            var _gravatar = function(res, em, group){
                if (group !== undefined){
                    em = '/images/icons/group.png'
                }
                tmpl = '<div class="ac-container-wrap"><img class="perm-gravatar-ac" src="{0}"/>{1}</div>'
                return tmpl.format(em,res)
            }
            if (oResultData.nname != undefined) {
                var fname = oResultData.fname || "";
                var lname = oResultData.lname || "";
                var nname = oResultData.nname;

                // Guard against null value
                var fnameMatchIndex = fname.toLowerCase().indexOf(query),
                    lnameMatchIndex = lname.toLowerCase().indexOf(query),
                    nnameMatchIndex = nname.toLowerCase().indexOf(query),
                    displayfname, displaylname, displaynname;

                if (fnameMatchIndex > -1) {
                    displayfname = highlightMatch(fname, query, fnameMatchIndex);
                } else {
                    displayfname = fname;
                }

                if (lnameMatchIndex > -1) {
                    displaylname = highlightMatch(lname, query, lnameMatchIndex);
                } else {
                    displaylname = lname;
                }

                if (nnameMatchIndex > -1) {
                    displaynname = "(" + highlightMatch(nname, query, nnameMatchIndex) + ")";
                } else {
                    displaynname = nname ? "(" + nname + ")" : "";
                }

                return _gravatar(displayfname + " " + displaylname + " " + displaynname, oResultData.gravatar_lnk);
            } else {
                return '';
            }
        };

    //members cache to catch duplicates
    reviewerAC.dataSource.cache = [];
    // hack into select event
    if(reviewerAC.itemSelectEvent){
        reviewerAC.itemSelectEvent.subscribe(function (sType, aArgs) {

            var myAC = aArgs[0]; // reference back to the AC instance
            var elLI = aArgs[1]; // reference to the selected LI element
            var oData = aArgs[2]; // object literal of selected item's result data

            //fill the autocomplete with value

            if (oData.nname != undefined) {
                addReviewMember(oData.id, oData.fname, oData.lname, oData.nname,
                                oData.gravatar_lnk);
                myAC.dataSource.cache.push(oData.id);
                YUD.get('user').value = ''
            }
        });
    }
    return {
        ownerDS: ownerDS,
        reviewerAC: reviewerAC,
    };
}

/**
 * QUICK REPO MENU
 */
var quick_repo_menu = function(){
    YUE.on(YUQ('.quick_repo_menu'),'mouseenter',function(e){
            var menu = e.currentTarget.firstElementChild.firstElementChild;
            if(YUD.hasClass(menu,'hidden')){
                YUD.replaceClass(e.currentTarget,'hidden', 'active');
                YUD.replaceClass(menu, 'hidden', 'active');
            }
        })
    YUE.on(YUQ('.quick_repo_menu'),'mouseleave',function(e){
            var menu = e.currentTarget.firstElementChild.firstElementChild;
            if(YUD.hasClass(menu,'active')){
                YUD.replaceClass(e.currentTarget, 'active', 'hidden');
                YUD.replaceClass(menu, 'active', 'hidden');
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
    var date_ = YUD.getAttribute(node.firstElementChild,'date');
    return date_
}

var get_age = function(node){
    return node
}

var get_link = function(node){
    return node.firstElementChild.text;
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
    var a_ = fromHTML(a.getData(field));
    var b_ = fromHTML(b.getData(field));

    // extract name from table
    a_ = get_date(a_)
    b_ = get_date(b_)

    var comp = YAHOO.util.Sort.compare;
    var compState = comp(a_, b_, desc);
    return compState;
};

var lastLoginSort = function(a, b, desc, field) {
    var a_ = a.getData('last_login_raw') || 0;
    var b_ = b.getData('last_login_raw') || 0;

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

var permNameSort = function(a, b, desc, field) {
    var a_ = fromHTML(a.getData(field));
    var b_ = fromHTML(b.getData(field));
    // extract name from table

    a_ = a_.children[0].innerHTML;
    b_ = b_.children[0].innerHTML;

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

var usernamelinkSort = function(a, b, desc, field) {
      var a_ = fromHTML(a.getData(field));
      var b_ = fromHTML(b.getData(field));

      // extract url text from string nodes
      a_ = get_link(a_)
      b_ = get_link(b_)
      var comp = YAHOO.util.Sort.compare;
      var compState = comp(a_, b_, desc);
      return compState;
}

var addPermAction = function(_html, users_list, groups_list){
    var elmts = YUD.getElementsByClassName('last_new_member');
    var last_node = elmts[elmts.length-1];
    if (last_node){
       var next_id = (YUD.getElementsByClassName('new_members')).length;
       _html = _html.format(next_id);
       last_node.innerHTML = _html;
       YUD.setStyle(last_node, 'display', '');
       YUD.removeClass(last_node, 'last_new_member');
       MembersAutoComplete("perm_new_member_name_"+next_id,
               "perm_container_"+next_id, users_list, groups_list);
       //create new last NODE
       var el = document.createElement('tr');
       el.id = 'add_perm_input';
       YUD.addClass(el,'last_new_member');
       YUD.addClass(el,'new_members');
       YUD.insertAfter(el, last_node);
    }
}
function ajaxActionRevokePermission(url, obj_id, obj_type, field_id, extra_data) {
    var callback = {
        success: function (o) {
            var tr = YUD.get(String(field_id));
            tr.parentNode.removeChild(tr);
        },
        failure: function (o) {
            alert(_TM['Failed to remoke permission'] + ": " + o.status);
        },
    };
    query_params = {
        '_method': 'delete'
    }
    // put extra data into POST
    if (extra_data !== undefined && (typeof extra_data === 'object')){
        for(k in extra_data){
            query_params[k] = extra_data[k];
        }
    }

    if (obj_type=='user'){
        query_params['user_id'] = obj_id;
        query_params['obj_type'] = 'user';
    }
    else if (obj_type=='user_group'){
        query_params['user_group_id'] = obj_id;
        query_params['obj_type'] = 'user_group';
    }

    var request = YAHOO.util.Connect.asyncRequest('POST', url, callback,
            toQueryString(query_params));
};
/* Multi selectors */

var MultiSelectWidget = function(selected_id, available_id, form_id){


    //definition of containers ID's
    var selected_container = selected_id;
    var available_container = available_id;

    //temp container for selected storage.
    var cache = new Array();
    var av_cache = new Array();
    var c =  YUD.get(selected_container);
    var ac = YUD.get(available_container);

    //get only selected options for further fullfilment
    for(var i = 0;node =c.options[i];i++){
        if(node.selected){
            //push selected to my temp storage left overs :)
            cache.push(node);
        }
    }

    //get all available options to cache
    for(var i = 0;node =ac.options[i];i++){
            //push selected to my temp storage left overs :)
            av_cache.push(node);
    }

    //fill available only with those not in chosen
    ac.options.length=0;
    tmp_cache = new Array();

    for(var i = 0;node = av_cache[i];i++){
        var add = true;
        for(var i2 = 0;node_2 = cache[i2];i2++){
            if(node.value == node_2.value){
                add=false;
                break;
            }
        }
        if(add){
            tmp_cache.push(new Option(node.text, node.value, false, false));
        }
    }

    for(var i = 0;node = tmp_cache[i];i++){
        ac.options[i] = node;
    }

    function prompts_action_callback(e){

        var chosen = YUD.get(selected_container);
        var available = YUD.get(available_container);

        //get checked and unchecked options from field
        function get_checked(from_field){
            //temp container for storage.
            var sel_cache = new Array();
            var oth_cache = new Array();

            for(var i = 0;node = from_field.options[i];i++){
                if(node.selected){
                    //push selected fields :)
                    sel_cache.push(node);
                }
                else{
                    oth_cache.push(node)
                }
            }

            return [sel_cache,oth_cache]
        }

        //fill the field with given options
        function fill_with(field,options){
            //clear firtst
            field.options.length=0;
            for(var i = 0;node = options[i];i++){
                    field.options[i]=new Option(node.text, node.value,
                            false, false);
            }

        }
        //adds to current field
        function add_to(field,options){
            for(var i = 0;node = options[i];i++){
                    field.appendChild(new Option(node.text, node.value,
                            false, false));
            }
        }

        // add action
        if (this.id=='add_element'){
            var c = get_checked(available);
            add_to(chosen,c[0]);
            fill_with(available,c[1]);
        }
        // remove action
        if (this.id=='remove_element'){
            var c = get_checked(chosen);
            add_to(available,c[0]);
            fill_with(chosen,c[1]);
        }
        // add all elements
        if(this.id=='add_all_elements'){
            for(var i=0; node = available.options[i];i++){
                    chosen.appendChild(new Option(node.text,
                            node.value, false, false));
            }
            available.options.length = 0;
        }
        //remove all elements
        if(this.id=='remove_all_elements'){
            for(var i=0; node = chosen.options[i];i++){
                available.appendChild(new Option(node.text,
                        node.value, false, false));
            }
            chosen.options.length = 0;
        }

    }

    YUE.addListener(['add_element','remove_element',
                   'add_all_elements','remove_all_elements'],'click',
                   prompts_action_callback)
    if (form_id !== undefined) {
        YUE.addListener(form_id,'submit',function(){
            var chosen = YUD.get(selected_container);
            for (var i = 0; i < chosen.options.length; i++) {
                chosen.options[i].selected = 'selected';
            }
        });
    }
}

// custom paginator
var YUI_paginator = function(links_per_page, containers){

    (function () {

        var Paginator = YAHOO.widget.Paginator,
            l         = YAHOO.lang,
            setId     = YAHOO.util.Dom.generateId;

        Paginator.ui.MyFirstPageLink = function (p) {
            this.paginator = p;

            p.subscribe('recordOffsetChange',this.update,this,true);
            p.subscribe('rowsPerPageChange',this.update,this,true);
            p.subscribe('totalRecordsChange',this.update,this,true);
            p.subscribe('destroy',this.destroy,this,true);

            // TODO: make this work
            p.subscribe('firstPageLinkLabelChange',this.update,this,true);
            p.subscribe('firstPageLinkClassChange',this.update,this,true);
        };

        Paginator.ui.MyFirstPageLink.init = function (p) {
            p.setAttributeConfig('firstPageLinkLabel', {
                value : 1,
                validator : l.isString
            });
            p.setAttributeConfig('firstPageLinkClass', {
                value : 'yui-pg-first',
                validator : l.isString
            });
            p.setAttributeConfig('firstPageLinkTitle', {
                value : 'First Page',
                validator : l.isString
            });
        };

        // Instance members and methods
        Paginator.ui.MyFirstPageLink.prototype = {
            current   : null,
            leftmost_page: null,
            rightmost_page: null,
            link      : null,
            span      : null,
            dotdot    : null,
            getPos    : function(cur_page, max_page, items){
                var edge = parseInt(items / 2) + 1;
                if (cur_page <= edge){
                    var radius = Math.max(parseInt(items / 2), items - cur_page);
                }
                else if ((max_page - cur_page) < edge) {
                    var radius = (items - 1) - (max_page - cur_page);
                }
                else{
                    var radius = parseInt(items / 2);
                }

                var left = Math.max(1, (cur_page - (radius)))
                var right = Math.min(max_page, cur_page + (radius))
                return [left, cur_page, right]
            },
            render : function (id_base) {
                var p      = this.paginator,
                    c      = p.get('firstPageLinkClass'),
                    label  = p.get('firstPageLinkLabel'),
                    title  = p.get('firstPageLinkTitle');

                this.link     = document.createElement('a');
                this.span     = document.createElement('span');
                YUD.setStyle(this.span, 'display', 'none');

                var _pos = this.getPos(p.getCurrentPage(), p.getTotalPages(), 5);
                this.leftmost_page = _pos[0];
                this.rightmost_page = _pos[2];

                setId(this.link, id_base + '-first-link');
                this.link.href      = '#';
                this.link.className = c;
                this.link.innerHTML = label;
                this.link.title     = title;
                YAHOO.util.Event.on(this.link,'click',this.onClick,this,true);

                setId(this.span, id_base + '-first-span');
                this.span.className = c;
                this.span.innerHTML = label;

                this.current = p.getCurrentPage() > 1 ? this.link : this.span;
                return this.current;
            },
            update : function (e) {
                var p      = this.paginator;
                var _pos   = this.getPos(p.getCurrentPage(), p.getTotalPages(), 5);
                this.leftmost_page = _pos[0];
                this.rightmost_page = _pos[2];

                if (e && e.prevValue === e.newValue) {
                    return;
                }

                var par = this.current ? this.current.parentNode : null;
                if (this.leftmost_page > 1) {
                    if (par && this.current === this.span) {
                        par.replaceChild(this.link,this.current);
                        this.current = this.link;
                    }
                } else {
                    if (par && this.current === this.link) {
                        par.replaceChild(this.span,this.current);
                        this.current = this.span;
                    }
                }
            },
            destroy : function () {
                YAHOO.util.Event.purgeElement(this.link);
                this.current.parentNode.removeChild(this.current);
                this.link = this.span = null;
            },
            onClick : function (e) {
                YAHOO.util.Event.stopEvent(e);
                this.paginator.setPage(1);
            }
        };

        })();
    (function () {

        var Paginator = YAHOO.widget.Paginator,
            l         = YAHOO.lang,
            setId     = YAHOO.util.Dom.generateId;

        Paginator.ui.MyLastPageLink = function (p) {
            this.paginator = p;

            p.subscribe('recordOffsetChange',this.update,this,true);
            p.subscribe('rowsPerPageChange',this.update,this,true);
            p.subscribe('totalRecordsChange',this.update,this,true);
            p.subscribe('destroy',this.destroy,this,true);

            // TODO: make this work
            p.subscribe('lastPageLinkLabelChange',this.update,this,true);
            p.subscribe('lastPageLinkClassChange', this.update,this,true);
        };

        Paginator.ui.MyLastPageLink.init = function (p) {
            p.setAttributeConfig('lastPageLinkLabel', {
                value : -1,
                validator : l.isString
            });
            p.setAttributeConfig('lastPageLinkClass', {
                value : 'yui-pg-last',
                validator : l.isString
            });
            p.setAttributeConfig('lastPageLinkTitle', {
                value : 'Last Page',
                validator : l.isString
            });

        };

        Paginator.ui.MyLastPageLink.prototype = {

            current   : null,
            leftmost_page: null,
            rightmost_page: null,
            link      : null,
            span      : null,
            dotdot    : null,
            na        : null,
            getPos    : function(cur_page, max_page, items){
                var edge = parseInt(items / 2) + 1;
                if (cur_page <= edge){
                    var radius = Math.max(parseInt(items / 2), items - cur_page);
                }
                else if ((max_page - cur_page) < edge) {
                    var radius = (items - 1) - (max_page - cur_page);
                }
                else{
                    var radius = parseInt(items / 2);
                }

                var left = Math.max(1, (cur_page - (radius)))
                var right = Math.min(max_page, cur_page + (radius))
                return [left, cur_page, right]
            },
            render : function (id_base) {
                var p      = this.paginator,
                    c      = p.get('lastPageLinkClass'),
                    label  = p.get('lastPageLinkLabel'),
                    last   = p.getTotalPages(),
                    title  = p.get('lastPageLinkTitle');

                var _pos = this.getPos(p.getCurrentPage(), p.getTotalPages(), 5);
                this.leftmost_page = _pos[0];
                this.rightmost_page = _pos[2];

                this.link = document.createElement('a');
                this.span = document.createElement('span');
                YUD.setStyle(this.span, 'display', 'none');

                this.na   = this.span.cloneNode(false);

                setId(this.link, id_base + '-last-link');
                this.link.href      = '#';
                this.link.className = c;
                this.link.innerHTML = label;
                this.link.title     = title;
                YAHOO.util.Event.on(this.link,'click',this.onClick,this,true);

                setId(this.span, id_base + '-last-span');
                this.span.className = c;
                this.span.innerHTML = label;

                setId(this.na, id_base + '-last-na');

                if (this.rightmost_page < p.getTotalPages()){
                    this.current = this.link;
                }
                else{
                    this.current = this.span;
                }

                this.current.innerHTML = p.getTotalPages();
                return this.current;
            },

            update : function (e) {
                var p      = this.paginator;

                var _pos = this.getPos(p.getCurrentPage(), p.getTotalPages(), 5);
                this.leftmost_page = _pos[0];
                this.rightmost_page = _pos[2];

                if (e && e.prevValue === e.newValue) {
                    return;
                }

                var par   = this.current ? this.current.parentNode : null,
                    after = this.link;
                if (par) {

                    // only show the last page if the rightmost one is
                    // lower, so we don't have doubled entries at the end
                    if (!(this.rightmost_page < p.getTotalPages())){
                        after = this.span
                    }

                    if (this.current !== after) {
                        par.replaceChild(after,this.current);
                        this.current = after;
                    }
                }
                this.current.innerHTML = this.paginator.getTotalPages();

            },
            destroy : function () {
                YAHOO.util.Event.purgeElement(this.link);
                this.current.parentNode.removeChild(this.current);
                this.link = this.span = null;
            },
            onClick : function (e) {
                YAHOO.util.Event.stopEvent(e);
                this.paginator.setPage(this.paginator.getTotalPages());
            }
        };

        })();

    var pagi = new YAHOO.widget.Paginator({
        rowsPerPage: links_per_page,
        alwaysVisible: false,
        template : "{PreviousPageLink} {MyFirstPageLink} {PageLinks} {MyLastPageLink} {NextPageLink}",
        pageLinks: 5,
        containerClass: 'pagination-wh',
        currentPageClass: 'pager_curpage',
        pageLinkClass: 'pager_link',
        nextPageLinkLabel: '&gt;',
        previousPageLinkLabel: '&lt;',
        containers:containers
    })

    return pagi
}



// global hooks after DOM is loaded

YUE.onDOMReady(function(){
    YUE.on(YUQ('.diff-collapse-button'), 'click', function(e){
        var button = e.currentTarget;
        var t = YUD.get(button).getAttribute('target');
        console.log(t);
        if(YUD.hasClass(t, 'hidden')){
            YUD.removeClass(t, 'hidden');
            YUD.get(button).innerHTML = "&uarr; {0} &uarr;".format(_TM['Collapse diff']);
        }
        else if(!YUD.hasClass(t, 'hidden')){
            YUD.addClass(t, 'hidden');
            YUD.get(button).innerHTML = "&darr; {0} &darr;".format(_TM['Expand diff']);
        }
    });



});
