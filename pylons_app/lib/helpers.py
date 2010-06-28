"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pygments.formatters import HtmlFormatter
from pygments import highlight as code_highlight
from pylons import url, app_globals as g
from pylons.i18n.translation import _, ungettext
from vcs.utils.annotate import annotate_highlight
from webhelpers.html import literal, HTML, escape
from webhelpers.html.tools import *
from webhelpers.html.builder import make_tag
from webhelpers.html.tags import auto_discovery_link, checkbox, css_classes, \
    end_form, file, form, hidden, image, javascript_link, link_to, link_to_if, \
    link_to_unless, ol, required_legend, select, stylesheet_link, submit, text, \
    password, textarea, title, ul, xml_declaration, radio
from webhelpers.html.tools import auto_link, button_to, highlight, js_obfuscate, \
    mail_to, strip_links, strip_tags, tag_re
from webhelpers.number import format_byte_size, format_bit_size
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form
from webhelpers.text import chop_at, collapse, convert_accented_entities, \
    convert_misc_entities, lchop, plural, rchop, remove_formatting, \
    replace_whitespace, urlify, truncate, wrap_paragraphs


#Custom helpers here :)
class _Link(object):
    '''
    Make a url based on label and url with help of url_for
    @param label:name of link    if not defined url is used
    @param url: the url for link
    '''

    def __call__(self, label='', *url_, **urlargs):
        if label is None or '':
            label = url
        link_fn = link_to(label, url(*url_, **urlargs))
        return link_fn

link = _Link()

class _GetError(object):

    def __call__(self, field_name, form_errors):
        tmpl = """<span class="error_msg">%s</span>"""
        if form_errors and form_errors.has_key(field_name):
            return literal(tmpl % form_errors.get(field_name))

get_error = _GetError()

def recursive_replace(str, replace=' '):
    """
    Recursive replace of given sign to just one instance
    @param str: given string
    @param replace:char to find and replace multiple instances
        
    Examples::
    >>> recursive_replace("Mighty---Mighty-Bo--sstones",'-')
    'Mighty-Mighty-Bo-sstones'
    """

    if str.find(replace * 2) == -1:
        return str
    else:
        str = str.replace(replace * 2, replace)
        return recursive_replace(str, replace)  

class _ToolTip(object):
    
    def __call__(self, tooltip_title, trim_at=50):
        """
        Special function just to wrap our text into nice formatted autowrapped
        text
        @param tooltip_title:
        """
        
        return literal(wrap_paragraphs(tooltip_title, trim_at)\
                       .replace('\n', '<br/>')) 
    
    def activate(self):
        """
        Adds tooltip mechanism to the given Html all tooltips have to have 
        set class tooltip and set attribute tooltip_title.
        Then a tooltip will be generated based on that
        All with yui js tooltip
        """
        
        js = '''
        YAHOO.util.Event.onDOMReady(function(){
            function toolTipsId(){
                var ids = [];
                var tts = YAHOO.util.Dom.getElementsByClassName('tooltip');
                
                for (var i = 0; i < tts.length; i++) {
                    //if element doesn not have and id autgenerate one for tooltip
                    
                    if (!tts[i].id){
                        tts[i].id='tt'+i*100;
                    }
                    ids.push(tts[i].id);
                }
                return ids        
            };
            var myToolTips = new YAHOO.widget.Tooltip("tooltip", { 
                context: toolTipsId(),
                monitorresize:false,
                xyoffset :[0,0],
                autodismissdelay:300000,
                hidedelay:5,
                showdelay:20,
            });
            
            //Mouse Over event disabled for new repositories since they dont
            //have last commit message
            myToolTips.contextMouseOverEvent.subscribe(
                function(type, args) {
                    var context = args[0];
                    var txt = context.getAttribute('tooltip_title');
                    if(txt){                                       
                        return true;
                    }
                    else{
                        return false;
                    }
                });
            
                            
            // Set the text for the tooltip just before we display it. Lazy method
            myToolTips.contextTriggerEvent.subscribe( 
                 function(type, args) { 

                 
                        var context = args[0]; 
                        
                        var txt = context.getAttribute('tooltip_title');
                        this.cfg.setProperty("text", txt);
                        
                        
                        // positioning of tooltip
                        var tt_w = this.element.clientWidth;
                        var tt_h = this.element.clientHeight;
                        
                        var context_w = context.offsetWidth;
                        var context_h = context.offsetHeight;
                        
                        var pos_x = YAHOO.util.Dom.getX(context);
                        var pos_y = YAHOO.util.Dom.getY(context);

                        var display_strategy = 'top';
                        var xy_pos = [0,0];
                        switch (display_strategy){
                        
                            case 'top':
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y-tt_h-4;
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'bottom':
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y+context_h+4;
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'left':
                                var cur_x = (pos_x-tt_w-4);
                                var cur_y = pos_y-((tt_h/2)-context_h/2);
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'right':
                                var cur_x = (pos_x+context_w+4);
                                var cur_y = pos_y-((tt_h/2)-context_h/2);
                                xy_pos = [cur_x,cur_y];                                
                                break;
                             default:
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y-tt_h-4;
                                xy_pos = [cur_x,cur_y];                                
                                break;                             
                                 
                        }

                        this.cfg.setProperty("xy",xy_pos);

                  });
                  
            //Mouse out 
            myToolTips.contextMouseOutEvent.subscribe(
                function(type, args) {
                    var context = args[0];
                    
                });
        });
        '''         
        return literal(js)

tooltip = _ToolTip()

class _FilesBreadCrumbs(object):
    
    def __call__(self, repo_name, rev, paths):
        url_l = [link_to(repo_name, url('files_home',
                                        repo_name=repo_name,
                                        revision=rev, f_path=''))]
        paths_l = paths.split('/')
        
        for cnt, p in enumerate(paths_l, 1):
            if p != '':
                url_l.append(link_to(p, url('files_home',
                                            repo_name=repo_name,
                                            revision=rev,
                                            f_path='/'.join(paths_l[:cnt]))))

        return literal(' / '.join(url_l))

files_breadcrumbs = _FilesBreadCrumbs()

def pygmentize(filenode, **kwargs):
    """
    pygmentize function using pygments
    @param filenode:
    """
    return literal(code_highlight(filenode.content, filenode.lexer, HtmlFormatter(**kwargs)))

def pygmentize_annotation(filenode, **kwargs):
    """
    pygmentize function for annotation
    @param filenode:
    """
    
    color_dict = g.changeset_annotation_colors
    def gen_color():
        import random
        return [str(random.randrange(10, 235)) for _ in xrange(3)]
    def get_color_string(cs):
        if color_dict.has_key(cs):
            col = color_dict[cs]
        else:
            color_dict[cs] = gen_color()
            col = color_dict[cs]
        return "color: rgb(%s) ! important;" % (', '.join(col))
        
    def url_func(changeset):
        tooltip_html = "<div style='font-size:0.8em'><b>Author:</b> %s<br/><b>Date:</b> %s</b><br/><b>Message:</b> %s<br/></div>" 
        
        tooltip_html = tooltip_html % (changeset.author,
                                               changeset.date,
                                               tooltip(changeset.message))
        lnk_format = 'r%s:%s' % (changeset.revision,
                                 changeset.raw_id)
        uri = link_to(
                lnk_format,
                url('changeset_home', repo_name='test',
                    revision=changeset.raw_id),
                style=get_color_string(changeset.raw_id),
                class_='tooltip',
                tooltip_title=tooltip_html
              )
        
        uri += '\n'
        return uri   
    return literal(annotate_highlight(filenode, url_func, **kwargs))
      
def repo_name_slug(value):
    """
    Return slug of name of repository
    """
    slug = urlify(value)
    for c in """=[]\;'"<>,/~!@#$%^&*()+{}|:""":
        slug = slug.replace(c, '-')
    slug = recursive_replace(slug, '-')
    return slug

flash = _Flash()


#===============================================================================
# MERCURIAL FILTERS available via h.
#===============================================================================


from mercurial import util
from mercurial.templatefilters import age as _age, person as _person

age = lambda  x:_age(x)
capitalize = lambda x: x.capitalize()
date = lambda x: util.datestr(x)
email = util.email
person = lambda x: _person(x)
hgdate = lambda  x: "%d %d" % x
isodate = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')
isodatesec = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M:%S %1%2')
localdate = lambda  x: (x[0], util.makedate()[1])
rfc822date = lambda  x: util.datestr(x, "%a, %d %b %Y %H:%M:%S %1%2")
rfc3339date = lambda  x: util.datestr(x, "%Y-%m-%dT%H:%M:%S%1:%2")
time_ago = lambda x: util.datestr(_age(x), "%a, %d %b %Y %H:%M:%S %1%2")


#===============================================================================
# PERMS
#===============================================================================
from pylons_app.lib.auth import HasPermissionAny, HasPermissionAll, \
HasRepoPermissionAny, HasRepoPermissionAll


