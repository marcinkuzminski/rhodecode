(function() {
  if (!CodeMirror.modeURL) CodeMirror.modeURL = "../mode/%N/%N.js";

  var loading = {};
  function splitCallback(cont, n) {
    var countDown = n;
    return function() { if (--countDown == 0) cont(); };
  }
  function ensureDeps(mode, cont) {
    var deps = CodeMirror.modes[mode].dependencies;
    if (!deps) return cont();
    var missing = [];
    for (var i = 0; i < deps.length; ++i) {
      if (!CodeMirror.modes.hasOwnProperty(deps[i]))
        missing.push(deps[i]);
    }
    if (!missing.length) return cont();
    var split = splitCallback(cont, missing.length);
    for (var i = 0; i < missing.length; ++i)
      CodeMirror.requireMode(missing[i], split);
  }

  CodeMirror.requireMode = function(mode, cont) {
    if (typeof mode != "string") mode = mode.name;
    if (CodeMirror.modes.hasOwnProperty(mode)) return ensureDeps(mode, cont);
    if (loading.hasOwnProperty(mode)) return loading[mode].push(cont);

    var script = document.createElement("script");
    script.src = CodeMirror.modeURL.replace(/%N/g, mode);
    var others = document.getElementsByTagName("script")[0];
    others.parentNode.insertBefore(script, others);
    var list = loading[mode] = [cont];
    var count = 0, poll = setInterval(function() {
      if (++count > 100) return clearInterval(poll);
      if (CodeMirror.modes.hasOwnProperty(mode)) {
        clearInterval(poll);
        loading[mode] = null;
        ensureDeps(mode, function() {
          for (var i = 0; i < list.length; ++i) list[i]();
        });
      }
    }, 200);
  };

  CodeMirror.autoLoadMode = function(instance, mode) {
    if (!CodeMirror.modes.hasOwnProperty(mode))
      CodeMirror.requireMode(mode, function() {
        instance.setOption("mode", instance.getOption("mode"));
      });
  };
}());


//overlay plugin

// Utility function that allows modes to be combined. The mode given
// as the base argument takes care of most of the normal mode
// functionality, but a second (typically simple) mode is used, which
// can override the style of text. Both modes get to parse all of the
// text, but when both assign a non-null style to a piece of code, the
// overlay wins, unless the combine argument was true, in which case
// the styles are combined.

// overlayParser is the old, deprecated name
CodeMirror.overlayMode = CodeMirror.overlayParser = function(base, overlay, combine) {
  return {
    startState: function() {
      return {
        base: CodeMirror.startState(base),
        overlay: CodeMirror.startState(overlay),
        basePos: 0, baseCur: null,
        overlayPos: 0, overlayCur: null
      };
    },
    copyState: function(state) {
      return {
        base: CodeMirror.copyState(base, state.base),
        overlay: CodeMirror.copyState(overlay, state.overlay),
        basePos: state.basePos, baseCur: null,
        overlayPos: state.overlayPos, overlayCur: null
      };
    },

    token: function(stream, state) {
      if (stream.start == state.basePos) {
        state.baseCur = base.token(stream, state.base);
        state.basePos = stream.pos;
      }
      if (stream.start == state.overlayPos) {
        stream.pos = stream.start;
        state.overlayCur = overlay.token(stream, state.overlay);
        state.overlayPos = stream.pos;
      }
      stream.pos = Math.min(state.basePos, state.overlayPos);
      if (stream.eol()) state.basePos = state.overlayPos = 0;

      if (state.overlayCur == null) return state.baseCur;
      if (state.baseCur != null && combine) return state.baseCur + " " + state.overlayCur;
      else return state.overlayCur;
    },

    indent: base.indent && function(state, textAfter) {
      return base.indent(state.base, textAfter);
    },
    electricChars: base.electricChars,

    innerMode: function(state) { return {state: state.base, mode: base}; },

    blankLine: function(state) {
      if (base.blankLine) base.blankLine(state.base);
      if (overlay.blankLine) overlay.blankLine(state.overlay);
    }
  };
};
