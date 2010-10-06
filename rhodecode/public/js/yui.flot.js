/**
\file yui.flot.js
\brief Javascript plotting library for YUI based on Flot v. 0.5.
\details
This file contains a port of Flot for YUI

Copyright (c) 2009 Yahoo! Inc.  All rights reserved.  The copyrights embodied
in the content of this file are licenced by Yahoo! Inc. under the BSD (revised)
open source license.

Requires yahoo-dom-event and datasource which you can get here:
<script type="text/javascript" src="http://yui.yahooapis.com/combo?2.7.0/build/yahoo-dom-event/yahoo-dom-event.js&2.7.0/build/datasource/datasource-min.js"></script>

Datasource is optional, you only need it if one of your axes has its mode set to "time"
*/

(function() {
	var L = YAHOO.lang;
	var UA = YAHOO.env.ua;
	var DOM = YAHOO.util.Dom;
	var E = YAHOO.util.Event;

	if(!DOM.createElementFromMarkup) {
		DOM.createElementFromMarkup = function(markup) {
			var p=document.createElement('div');
			p.innerHTML = markup;
			var e = p.firstChild;
			return p.removeChild(e);
		};
	}

	if(!DOM.removeElement) {
		DOM.removeElement = function(el) {
			return el.parentNode.removeChild(el);
		};
	}

	function Plot(target_, data_, options_) {
		// data is on the form:
		//   [ series1, series2 ... ]
		// where series is either just the data as [ [x1, y1], [x2, y2], ... ]
		// or { data: [ [x1, y1], [x2, y2], ... ], label: "some label" }

		var series = [],
			options = {
				// the color theme used for graphs
				colors: ["#edc240", "#afd8f8", "#cb4b4b", "#4da74d", "#9440ed"],
				locale: "en",
				legend: {
					show: true,
					noColumns: 1, // number of colums in legend table
					labelFormatter: null, // fn: string -> string
					labelBoxBorderColor: "#ccc", // border color for the little label boxes
					container: null, // container (as jQuery object) to put legend in, null means default on top of graph
					position: "ne", // position of default legend container within plot
					margin: 5, // distance from grid edge to default legend container within plot
					backgroundColor: null, // null means auto-detect
					backgroundOpacity: 0.85 // set to 0 to avoid background
				},
				xaxis: {
					mode: null, // null or "time"
					min: null, // min. value to show, null means set automatically
					max: null, // max. value to show, null means set automatically
					autoscaleMargin: null, // margin in % to add if auto-setting min/max
					ticks: null, // either [1, 3] or [[1, "a"], 3] or (fn: axis info -> ticks) or app. number of ticks for auto-ticks
					tickFormatter: null, // fn: number -> string
					label: null,
					labelWidth: null, // size of tick labels in pixels
					labelHeight: null,

					scaleType: 'linear',	// may be 'linear' or 'log'

					// mode specific options
					tickDecimals: null, // no. of decimals, null means auto
					tickSize: null, // number or [number, "unit"]
					minTickSize: null, // number or [number, "unit"]
					timeformat: null // format string to use
				},
				yaxis: {
					label: null,
					autoscaleMargin: 0.02
				},
				x2axis: {
					label: null,
					autoscaleMargin: null
				},
				y2axis: {
					label: null,
					autoscaleMargin: 0.02
				},			  
				points: {
					show: false,
					radius: 3,
					lineWidth: 2, // in pixels
					fill: true,
					fillColor: "#ffffff"
				},
				lines: {
					// we don't put in show: false so we can see
					// whether lines were actively disabled 
					lineWidth: 2, // in pixels
					fill: false,
					fillColor: null
				},
				bars: {
					show: false,
					lineWidth: 2, // in pixels
					barWidth: 1, // in units of the x axis
					fill: true,
					fillColor: null,
					align: "left" // or "center" 
				},
				grid: {
					show: true,
					showLines: true,
					color: "#545454", // primary color used for outline and labels
					backgroundColor: null, // null for transparent, else color
					tickColor: "#dddddd", // color used for the ticks
					labelMargin: 5, // in pixels
					labelFontSize: 16,
					borderWidth: 2, // in pixels
					borderColor: null, // set if different from the grid color
					markings: null, // array of ranges or fn: axes -> array of ranges
					markingsColor: "#f4f4f4",
					markingsLineWidth: 2,
					// interactive stuff
					clickable: false,
					hoverable: false,
					autoHighlight: true, // highlight in case mouse is near
					mouseActiveRadius: 10 // how far the mouse can be away to activate an item
				},
				selection: {
					mode: null, // one of null, "x", "y" or "xy"
					color: "#e8cfac"
				},
				crosshair: {
					mode: null, // one of null, "x", "y" or "xy",
					color: "#aa0000"
				},
				shadowSize: 3
			},
		canvas = null,	  // the canvas for the plot itself
		overlay = null,	 // canvas for interactive stuff on top of plot
		eventHolder = null, // jQuery object that events should be bound to
		ctx = null, octx = null,
		target = DOM.get(target_),
		axes = { xaxis: {}, yaxis: {}, x2axis: {}, y2axis: {} },
		plotOffset = { left: 0, right: 0, top: 0, bottom: 0},
		canvasWidth = 0, canvasHeight = 0,
		plotWidth = 0, plotHeight = 0,
		// dedicated to storing data for buggy standard compliance cases
		workarounds = {};

		this.setData = setData;
		this.setupGrid = setupGrid;
		this.draw = draw;
		this.clearSelection = clearSelection;
		this.setSelection = setSelection;
		this.getCanvas = function() { return canvas; };
		this.getPlotOffset = function() { return plotOffset; };
		this.getData = function() { return series; };
		this.getAxes = function() { return axes; };
		this.setCrosshair = setCrosshair;
		this.clearCrosshair = function () { setCrosshair(null); };
		this.highlight = highlight;
		this.unhighlight = unhighlight;

		// initialize
		parseOptions(options_);
		setData(data_);
		constructCanvas();
		setupGrid();
		draw();

		var plot = this;

		plot.createEvent('plotclick');
		plot.createEvent('plothover');
		plot.createEvent('plotselected');
		plot.createEvent('plotunselected');



		function setData(d) {
			series = parseData(d);

			fillInSeriesOptions();
			processData();
		}

		function normalizeData(d) {
			var possible_controls = ['x', 'time', 'date'];

			if (L.isArray(d)) {
				d = { data: d };
			} else {
				d = L.merge(d);
			}

			if(d.disabled) {
				return undefined;
			}

			if (d.data.length === 0) {
				return undefined;
			}

			var j, k;

			// Make a copy so we don't obliterate the caller's data
			var _data = [];

			if (L.isArray(d.data[0])) {
				for(j=0; j<d.data.length; j++) {
					if(d.data[j]) {
						var x = d.data[j][0];
						var y = d.data[j][1];

						if(L.isObject(x) && x.getTime) x = x.getTime()/1000;
						else x = parseFloat(x);

						if(L.isObject(y) && y.getTime) y = y.getTime()/1000;
						else y = parseFloat(y);

						_data.push({ x: x, y: y});
					} else {
						_data.push(d.data[j]);
					}
				}
				d.control='x';
				d.schema='y';
			} else {
				for(j=0; j<d.data.length; j++) {
					_data.push({});
					for(k in d.data[j]) {
						if(L.isObject(d.data[j][k]) && d.data[j][k].getTime)
							_data[j][k] = d.data[j][k].getTime()/1000;
						else
							_data[j][k] = parseFloat(d.data[j][k]);
					}
				}
			}

			d.data = _data;

			if (!d.control) {
				// try to guess the control field
				for (j=0; j<possible_controls.length; j++) {
					if(possible_controls[j] in d.data[0]) {
						d.control = possible_controls[j];
						break;
					}
				}
			}

			if (!d.schema) {
				d.schema = [];
				for(k in d.data[0]) {
					if(!d.control) {
						d.control = k;
					}
					if(k !== d.control) {
						d.schema.push(k);
					}
				}
			}

			return L.merge(d, {dropped: []});
		}

		function markDroppedPoints(s) {
			var l=s.data.length;

			if(l <= canvasWidth/10 || options.dontDropPoints) {	// at least 10px per point
				return s;
			}

			var dropperiod = 1-canvasWidth/10/l;
			var drops = 0;
			var points = l;

			for(var j=0; j<l; j++) {
				var x = s.data[j].x;
				var y = s.data[j].y;

				s.dropped[j] = (drops > 1);
				if(s.dropped[j]) {
					drops-=1;
				}

				if(!isNaN(x) && !isNaN(x))
					drops+=dropperiod;
				else {
					drops=0;	// bonus for a null point
					points--; 
					dropperiod=1-canvasWidth/10/points;
				}
			}

			return s;
		}

		function splitSeries(s) {
			var res = [];

			for(var k=0; k<s.schema.length; k++) {
				res[k] = L.merge(s, {data: []});
				if(s.label && L.isObject(s.label) && s.label[s.schema[k]]) {
					res[k].label = s.label[s.schema[k]];
				}
				if(s.color && L.isObject(s.color) && s.color[s.schema[k]]) {
					res[k].color = s.color[s.schema[k]];
				}
			}

			for(var i=0; i<s.data.length; i++) {
				var d = s.data[i];
				for(k=0; k<s.schema.length; k++) {
					var tuple = { x: d[s.control], y: d[s.schema[k]] };
					res[k].data.push(tuple);
					res[k].control='x';
					res[k].schema='y';
				}
			}

			return res;
		}

		function parseData(d) {
			if(d.length === 0) {
				return null;
			}
			
			// get the canvas width so we know if we have to drop points
			canvasWidth = parseInt(DOM.getStyle(target, 'width'), 10);

			// First we normalise the data into a standard format
			var s, res = [];
			for (var i = 0; i < d.length; ++i) {
				s = normalizeData(d[i]);
				if(typeof s === 'undefined') 
					continue;

				if(L.isArray(s.schema)) {
					s = splitSeries(s);
				}
				else {
					s = [s];
				}

				for(var k=0; k<s.length; k++) {
					s[k] = markDroppedPoints(s[k]);
					res.push(s[k]);
				}
			}

			return res;
		}

		function parseOptions(o) {
			if (options.grid.borderColor == null)
				options.grid.borderColor = options.grid.color;

			if(typeof o === 'undefined') {
				return;
			}
			o = YAHOO.lang.merge(o);
			for(var k in o)	{
				if(L.isObject(o[k]) && L.isObject(options[k])) {
					L.augmentObject(options[k], o[k], true);
					delete o[k];
				}
			}
			L.augmentObject(options, o, true);
		}

		function fillInSeriesOptions() {
			var i;

			// collect what we already got of colors
			var neededColors = series.length,
				usedColors = [],
				assignedColors = [];
			for (i = 0; i < series.length; ++i) {
				var sc = series[i].color;
				if (sc != null) {
					--neededColors;
					if (typeof sc == "number")
						assignedColors.push(sc);
					else
						usedColors.push(parseColor(series[i].color));
				}
			}

			// we might need to generate more colors if higher indices
			// are assigned
			for (i = 0; i < assignedColors.length; ++i) {
				neededColors = Math.max(neededColors, assignedColors[i] + 1);
			}

			// produce colors as needed
			var colors = [], variation = 0;
			i = 0;
			while (colors.length < neededColors) {
				var c;
				if (options.colors.length == i) // check degenerate case
					c = new Color(100, 100, 100);
				else
					c = parseColor(options.colors[i]);

				// vary color if needed
				var sign = variation % 2 == 1 ? -1 : 1;
				var factor = 1 + sign * Math.ceil(variation / 2) * 0.2;
				c.scale(factor, factor, factor);

				// FIXME: if we're getting too close to something else,
				// we should probably skip this one
				colors.push(c);

				++i;
				if (i >= options.colors.length) {
					i = 0;
					++variation;
				}
			}

			// fill in the options
			var colori = 0, s;
			for (i = 0; i < series.length; ++i) {
				s = series[i];

				// assign colors
				if (s.color == null) {
					s.color = colors[colori].toString();
					++colori;
				}
				else if (typeof s.color == "number")
					s.color = colors[s.color].toString();

				// copy the rest
				s.lines = L.merge(options.lines, s.lines || {});
				s.points = L.merge(options.points, s.points || {});
				s.bars = L.merge(options.bars, s.bars || {});

				// turn on lines automatically in case nothing is set
				if (s.lines.show == null && !s.bars.show && !s.points.show)
					s.lines.show = true;

				if (s.shadowSize == null)
					s.shadowSize = options.shadowSize;

				if (s.xaxis && s.xaxis == 2)
					s.xaxis = axes.x2axis;
				else
					s.xaxis = axes.xaxis;
				if (s.yaxis && s.yaxis >= 2) {
					if(!axes['y' + s.yaxis + 'axis'])
						axes['y' + s.yaxis + 'axis'] = {};
					if(!options['y' + s.yaxis + 'axis'])
						options['y' + s.yaxis + 'axis'] = { autoscaleMargin: 0.02 };
					s.yaxis = axes['y' + s.yaxis + 'axis'];
				}
				else
					s.yaxis = axes.yaxis;
			}
		}

		function processData() {
			var topSentry = Number.POSITIVE_INFINITY,
				bottomSentry = Number.NEGATIVE_INFINITY,
				axis;

			for (axis in axes) {
				axes[axis].datamin = topSentry;
				axes[axis].datamax = bottomSentry;
				axes[axis].min = options[axis].min;
				axes[axis].max = options[axis].max;
				axes[axis].used = false;
			}

			for (var i = 0; i < series.length; ++i) {
				var s = series[i];
				var data = s.data,
					axisx = s.xaxis, axisy = s.yaxis,
					xmin = topSentry, xmax = bottomSentry,
					ymin = topSentry, ymax = bottomSentry,
					x, y, p;

				axisx.used = axisy.used = true;

				if (s.bars.show) {
					// make sure we got room for the bar
					var delta = s.bars.align == "left" ? 0 : -s.bars.barWidth/2;
					xmin += delta;
					xmax += delta + s.bars.barWidth;
				}

				for (var j = 0; j < data.length; ++j) {
					p = data[j];

					if(data[j] === null)
						continue;

					x = p.x;
					y = p.y;

					if(L.isObject(x) && x.getTime) {	// this is a Date object
						x = x.getTime()/1000;
					}

					if(L.isObject(y) && y.getTime) {	// this is a Date object
						y = y.getTime()/1000;
					}

					// convert to number
					if (x != null && !isNaN(x = +x)) {
						if (x < xmin)
							xmin = x;
						if (x > xmax)
							xmax = x;
					}
					else
						x = null;

					if (y != null && !isNaN(y = +y)) {
						if (y < ymin)
							ymin = y;
						if (y > ymax)
							ymax = y;
					}
					else
						y = null;

					if (x == null || y == null)
						data[j] = x = y = null; // mark this point invalid
				}

				axisx.datamin = Math.min(axisx.datamin, xmin);
				axisx.datamax = Math.max(axisx.datamax, xmax);
				axisy.datamin = Math.min(axisy.datamin, ymin);
				axisy.datamax = Math.max(axisy.datamax, ymax);
			}
		}

		function constructCanvas() {
			function makeCanvas(width, height, container, style) {
				var c = document.createElement('canvas');
				c.width = width;
				c.height = height;
				if (typeof G_vmlCanvasManager !== 'undefined') // excanvas hack
					c = G_vmlCanvasManager.initElement(c);

				if(style) {
					for(var k in style) {
						c.style[k] = style[k];
					}
				}
				container.appendChild(c);

				return c;
			}

			canvasWidth = parseInt(DOM.getStyle(target, 'width'), 10);
			canvasHeight = parseInt(DOM.getStyle(target, 'height'), 10);
			target.innerHTML = ""; // clear target
			target.style.position = "relative"; // for positioning labels and overlay

			if (canvasWidth <= 0 || canvasHeight <= 0)
				throw "Invalid dimensions for plot, width = " + canvasWidth + ", height = " + canvasHeight;

			if (YAHOO.env.ua.ie) {
				G_vmlCanvasManager.init_(document);
			}

			// the canvas
			canvas = makeCanvas(canvasWidth, canvasHeight, target);
			ctx = canvas.getContext("2d");

			// overlay canvas for interactive features
			overlay = makeCanvas(canvasWidth, canvasHeight, target, { position: 'absolute', left: '0px', top: '0px' });
			octx = overlay.getContext("2d");

			// we include the canvas in the event holder too, because IE 7
			// sometimes has trouble with the stacking order
			eventHolder = [overlay, canvas];

			// bind events
			if (options.selection.mode != null || options.crosshair.mode != null || options.grid.hoverable) {
				E.on(eventHolder, 'mousemove', onMouseMove);

				if (options.selection.mode != null)
					E.on(eventHolder, "mousedown", onMouseDown);
			}

			if (options.crosshair.mode != null)
				E.on(eventHolder, "mouseout", onMouseOut);

			if (options.grid.clickable)
				E.on(eventHolder, "click", onClick);
		}

		function setupGrid() {
			function setupAxis(axis, options, type) {
				setRange(axis, options);
				prepareTickGeneration(axis, options);
				setTicks(axis, options);
				// add transformation helpers
				if (type == 'x') {
					// data point to canvas coordinate
					axis.p2c = function (p) { return (p - axis.min) * axis.scale; };
					// canvas coordinate to data point
					axis.c2p = function (c) { return axis.min + c / axis.scale; };
				}
				else {
					axis.p2c = function (p) { return (axis.max - p) * axis.scale; };
					axis.c2p = function (c) { return axis.max - c / axis.scale; };
				}
			}

			for (var axis in axes)
				setupAxis(axes[axis], options[axis], axis.charAt(0));

			setSpacing();
			if(options.grid.show)
			  insertLabels();
			insertLegend();
			insertAxisLabels();
		}

		function setRange(axis, axisOptions) {
			var min = axisOptions.min != null ? (axisOptions.scaleType == 'log' ? Math.log(axisOptions.min<=0?1:axisOptions.min) * Math.LOG10E : axisOptions.min) : axis.datamin;
			var max = axisOptions.max != null ? (axisOptions.scaleType == 'log' ? Math.log(axisOptions.max) * Math.LOG10E : axisOptions.max) : axis.datamax;

			if(axisOptions.mode === 'time') {
				if(L.isObject(min) && min.getTime) min = min.getTime()/1000;
				if(L.isObject(max) && max.getTime) max = max.getTime()/1000;
			}

			// degenerate case
			if (min == Number.POSITIVE_INFINITY)
				min = 0;
			if (max == Number.NEGATIVE_INFINITY)
				max = 1;

			if (max - min == 0.0) {
				// degenerate case
				var widen = max == 0 ? 1 : 0.01;

				if (axisOptions.min == null)
					min -= widen;
				// alway widen max if we couldn't widen min to ensure we
				// don't fall into min == max which doesn't work
				if (axisOptions.max == null || axisOptions.min != null)
					max += widen;
			}
			else {
				// consider autoscaling
				var margin = axisOptions.autoscaleMargin;
				if (margin != null) {
					if (axisOptions.min == null) {
						min -= (max - min) * margin;
						// make sure we don't go below zero if all values
						// are positive
						if (min < 0 && axis.datamin >= 0)
							min = 0;
					}
					if (axisOptions.max == null) {
						max += (max - min) * margin;
						if (max > 0 && axis.datamax <= 0)
							max = 0;
					}
				}
			}
			axis.min = min;
			axis.max = max;
		}

		function prepareTickGeneration(axis, axisOptions) {
			// estimate number of ticks
			var noTicks;
			if (typeof axisOptions.ticks == "number" && axisOptions.ticks > 0)
				noTicks = axisOptions.ticks;
			else if (axis == axes.xaxis || axis == axes.x2axis)
				noTicks = canvasWidth / 100;
			else
				noTicks = canvasHeight / 60;

			var delta = (axis.max - axis.min) / noTicks;
			var size, generator, unit, formatter, magn, norm;

			if (axisOptions.mode == "time") {
				// pretty handling of time

				delta*=1000;

				// map of app. size of time units in milliseconds
				var timeUnitSize = {
					"second": 1000,
					"minute": 60 * 1000,
					"hour": 60 * 60 * 1000,
					"day": 24 * 60 * 60 * 1000,
					"month": 30 * 24 * 60 * 60 * 1000,
					"year": 365.2425 * 24 * 60 * 60 * 1000
				};


				// the allowed tick sizes, after 1 year we use
				// an integer algorithm
				var spec = [
					[1, "second"], [2, "second"], [5, "second"], [10, "second"],
					[30, "second"], 
					[1, "minute"], [2, "minute"], [5, "minute"], [10, "minute"],
					[30, "minute"], 
					[1, "hour"], [2, "hour"], [4, "hour"],
					[8, "hour"], [12, "hour"],
					[1, "day"], [2, "day"], [3, "day"],
					[0.25, "month"], [0.5, "month"], [1, "month"],
					[2, "month"], [3, "month"], [6, "month"],
					[1, "year"]
				];

				var minSize = 0;
				if (axisOptions.minTickSize != null) {
					if (typeof axisOptions.tickSize == "number")
						minSize = axisOptions.tickSize;
					else
						minSize = axisOptions.minTickSize[0] * timeUnitSize[axisOptions.minTickSize[1]];
				}

				for (var i = 0; i < spec.length - 1; ++i)
					if (delta < (spec[i][0] * timeUnitSize[spec[i][1]]
								 + spec[i + 1][0] * timeUnitSize[spec[i + 1][1]]) / 2
					   && spec[i][0] * timeUnitSize[spec[i][1]] >= minSize)
						break;
				size = spec[i][0];
				unit = spec[i][1];

				// special-case the possibility of several years
				if (unit == "year") {
					magn = Math.pow(10, Math.floor(Math.log(delta / timeUnitSize.year) / Math.LN10));
					norm = (delta / timeUnitSize.year) / magn;
					if (norm < 1.5)
						size = 1;
					else if (norm < 3)
						size = 2;
					else if (norm < 7.5)
						size = 5;
					else
						size = 10;

					size *= magn;
				}

				if (axisOptions.tickSize) {
					size = axisOptions.tickSize[0];
					unit = axisOptions.tickSize[1];
				}

				generator = function(axis) {
					var ticks = [],
						tickSize = axis.tickSize[0], unit = axis.tickSize[1],
						d = new Date(axis.min*1000);

					var step = tickSize * timeUnitSize[unit];

					if (unit == "second")
						d.setUTCSeconds(floorInBase(d.getUTCSeconds(), tickSize));
					if (unit == "minute")
						d.setUTCMinutes(floorInBase(d.getUTCMinutes(), tickSize));
					if (unit == "hour")
						d.setUTCHours(floorInBase(d.getUTCHours(), tickSize));
					if (unit == "month")
						d.setUTCMonth(floorInBase(d.getUTCMonth(), tickSize));
					if (unit == "year")
						d.setUTCFullYear(floorInBase(d.getUTCFullYear(), tickSize));

					// reset smaller components
					d.setUTCMilliseconds(0);
					if (step >= timeUnitSize.minute)
						d.setUTCSeconds(0);
					if (step >= timeUnitSize.hour)
						d.setUTCMinutes(0);
					if (step >= timeUnitSize.day)
						d.setUTCHours(0);
					if (step >= timeUnitSize.day * 4)
						d.setUTCDate(1);
					if (step >= timeUnitSize.year)
						d.setUTCMonth(0);


					var carry = 0, v = Number.NaN, prev;
					do {
						prev = v;
						v = d.getTime();
						ticks.push({ v: v/1000, label: axis.tickFormatter(v, axis) });
						if (unit == "month") {
							if (tickSize < 1) {
								// a bit complicated - we'll divide the month
								// up but we need to take care of fractions
								// so we don't end up in the middle of a day
								d.setUTCDate(1);
								var start = d.getTime();
								d.setUTCMonth(d.getUTCMonth() + 1);
								var end = d.getTime();
								d.setTime(v + carry * timeUnitSize.hour + (end - start) * tickSize);
								carry = d.getUTCHours();
								d.setUTCHours(0);
							}
							else
								d.setUTCMonth(d.getUTCMonth() + tickSize);
						}
						else if (unit == "year") {
							d.setUTCFullYear(d.getUTCFullYear() + tickSize);
						}
						else
							d.setTime(v + step);
					} while (v < axis.max*1000 && v != prev);

					return ticks;
				};

				formatter = function (v, axis) {
					var d = new Date(v);

					// first check global format
					if (axisOptions.timeformat != null)
						return YAHOO.util.Date.format(d, {format: axisOptions.timeformat}, options.locale);

					var t = axis.tickSize[0] * timeUnitSize[axis.tickSize[1]];
					var span = axis.max - axis.min;
					span*=1000;

					if (t < timeUnitSize.minute)
						var fmt = "%k:%M:%S";
					else if (t < timeUnitSize.day) {
						if (span < 2 * timeUnitSize.day)
							fmt = "%k:%M";
						else
							fmt = "%b %d %k:%M";
					}
					else if (t < timeUnitSize.month)
						fmt = "%b %d";
					else if (t < timeUnitSize.year) {
						if (span < timeUnitSize.year/2)
							fmt = "%b";
						else
							fmt = "%b %Y";
					}
					else
						fmt = "%Y";

					return YAHOO.util.Date.format(d, {format: fmt}, axisOptions.timelang);
				};
			}
			else {
				// pretty rounding of base-10 numbers
				var maxDec = axisOptions.tickDecimals;
				var dec = -Math.floor(Math.log(delta) / Math.LN10);
				if (maxDec != null && dec > maxDec)
					dec = maxDec;

				magn = Math.pow(10, -dec);
				norm = delta / magn; // norm is between 1.0 and 10.0

				if (norm < 1.5)
					size = 1;
				else if (norm < 3) {
					size = 2;
					// special case for 2.5, requires an extra decimal
					if (norm > 2.25 && (maxDec == null || dec + 1 <= maxDec)) {
						size = 2.5;
						++dec;
					}
				}
				else if (norm < 7.5)
					size = 5;
				else
					size = 10;

				size *= magn;

				if (axisOptions.minTickSize != null && size < axisOptions.minTickSize)
					size = axisOptions.minTickSize;

				if (axisOptions.tickSize != null)
					size = axisOptions.tickSize;

				axis.tickDecimals = Math.max(0, (maxDec != null) ? maxDec : dec);

				generator = function (axis) {
					var ticks = [];

					// spew out all possible ticks
					var start = floorInBase(axis.min, axis.tickSize),
						i = 0, v = Number.NaN, prev;
					do {
						prev = v;
						v = start + i * axis.tickSize;
						var t=v;
						if(axis.scaleType == 'log') {
							t = Math.exp(t / Math.LOG10E);
						}
						ticks.push({ v: v, label: axis.tickFormatter(t, axis) });
						++i;
					} while (v < axis.max && v != prev);
					return ticks;
				};

				formatter = function (v, axis) {
					return v.toFixed(axis.tickDecimals);
				};
			}

			axis.scaleType = axisOptions.scaleType;
			axis.tickSize = unit ? [size, unit] : size;
			axis.tickGenerator = generator;
			if (L.isFunction(axisOptions.tickFormatter))
				axis.tickFormatter = function (v, axis) { return "" + axisOptions.tickFormatter(v, axis); };
			else
				axis.tickFormatter = formatter;
			if (axisOptions.labelWidth != null)
				axis.labelWidth = axisOptions.labelWidth;
			if (axisOptions.labelHeight != null)
				axis.labelHeight = axisOptions.labelHeight;
		}

		function setTicks(axis, axisOptions) {
			axis.ticks = [];

			if (!axis.used)
				return;

			if (axisOptions.ticks == null)
				axis.ticks = axis.tickGenerator(axis);
			else if (typeof axisOptions.ticks == "number") {
				if (axisOptions.ticks > 0)
					axis.ticks = axis.tickGenerator(axis);
			}
			else if (axisOptions.ticks) {
				var ticks = axisOptions.ticks;

				if (L.isFunction(ticks))
					// generate the ticks
					ticks = ticks({ min: axis.min, max: axis.max });

				// clean up the user-supplied ticks, copy them over
				var v;
				for (var i = 0; i < ticks.length; ++i) {
					var label = null;
					var t = ticks[i];
					if (typeof t == "object") {
						v = t[0];
						if (t.length > 1)
							label = t[1];
					}
					else
						v = t;
					if (axisOptions.scaleType == 'log') {
						if (label == null)
							label = v;
						v = Math.log(v) * Math.LOG10E;
					}

					if (label == null)
						label = axis.tickFormatter(v, axis);
					axis.ticks[i] = { v: v, label: label };
				}
			}

			if (axisOptions.autoscaleMargin != null && axis.ticks.length > 0) {
				// snap to ticks
				if (axisOptions.min == null)
					axis.min = Math.min(axis.min, axis.ticks[0].v);
				if (axisOptions.max == null && axis.ticks.length > 1)
					axis.max = Math.min(axis.max, axis.ticks[axis.ticks.length - 1].v);
			}
		}

		function setSpacing() {
			function measureXLabels(axis) {
  			if(options.grid.show){
  				// to avoid measuring the widths of the labels, we
  				// construct fixed-size boxes and put the labels inside
  				// them, we don't need the exact figures and the
  				// fixed-size box content is easy to center
  				if (axis.labelWidth == null)
  					axis.labelWidth = canvasWidth / 6;

  				// measure x label heights
  				if (axis.labelHeight == null) {
  					var labels = [];
  					for (var i = 0; i < axis.ticks.length; ++i) {
  						var l = axis.ticks[i].label;
  						if (l)
  							labels.push('<div class="tickLabel" style="float:left;width:' + axis.labelWidth + 'px">' + l + '</div>');
  					}

  					axis.labelHeight = 0;
  					if (labels.length > 0) {
  						var dummyDiv = target.appendChild(DOM.createElementFromMarkup('<div style="position:absolute;top:-10000px;width:10000px;font-size:smaller">'
  										 + labels.join("") + '<div style="clear:left"></div></div>'));
  						axis.labelHeight = dummyDiv.offsetHeight;
  						target.removeChild(dummyDiv);
  					}
  				}
			  }
			  else{
				  axis.labelHeight = 0;
				  axis.labelWidth = 0;
			  }
			}

			function measureYLabels(axis) {
  			if(options.grid.show){
  				if (axis.labelWidth == null || axis.labelHeight == null) {
  					var labels = [], l;
  					// calculate y label dimensions
  					for (var i = 0; i < axis.ticks.length; ++i) {
  						l = axis.ticks[i].label;
  						if (l)
  							labels.push('<div class="tickLabel">' + l + '</div>');
  					}

  					if (labels.length > 0) {
  						var dummyDiv = target.appendChild(DOM.createElementFromMarkup('<div style="position:absolute;top:-10000px;font-size:smaller">'
  										 + labels.join("") + '</div>'));
  						if (axis.labelWidth == null)
  							axis.labelWidth = dummyDiv.offsetWidth;
  						if (axis.labelHeight == null)
  							axis.labelHeight = dummyDiv.firstChild.offsetHeight;
  						target.removeChild(dummyDiv);
  					}

  					if (axis.labelWidth == null)
  						axis.labelWidth = 0;
  					if (axis.labelHeight == null)
  						axis.labelHeight = 0;
  				}
  		  }
			  else{
				  axis.labelHeight = 0;
				  axis.labelWidth = 0;
			  }
			}

			measureXLabels(axes.xaxis);
			measureYLabels(axes.yaxis);
			measureXLabels(axes.x2axis);
			measureYLabels(axes.y2axis);
			// get the most space needed around the grid for things
			// that may stick out
			var maxOutset = (options.grid.show) ? options.grid.borderWidth : 0;
			for (var i = 0; i < series.length; ++i)
				maxOutset = (Math.max(maxOutset, 2 * (((series[i].points.show) ? series[i].points.radius : 0 ) + series[i].points.lineWidth/2)));
      
			plotOffset.left = plotOffset.right = plotOffset.top = plotOffset.bottom = maxOutset;

			var margin = options.grid.labelMargin + options.grid.borderWidth;

			if (axes.xaxis.labelHeight > 0)
				plotOffset.bottom = Math.max(maxOutset, axes.xaxis.labelHeight + margin);
			if (axes.yaxis.labelWidth > 0)
				plotOffset.left = Math.max(maxOutset, axes.yaxis.labelWidth + margin);

			if (axes.x2axis.labelHeight > 0)
				plotOffset.top = Math.max(maxOutset, axes.x2axis.labelHeight + margin);

			if (axes.y2axis.labelWidth > 0)
				plotOffset.right = Math.max(maxOutset, axes.y2axis.labelWidth + margin);

			plotWidth = canvasWidth - plotOffset.left - plotOffset.right;
			plotHeight = canvasHeight - plotOffset.bottom - plotOffset.top;

			// precompute how much the axis is scaling a point in canvas space
			for(var axis in axes) {
				axes[axis].scale = (axis.charAt(0) == 'x' ? plotWidth : plotHeight) / (axes[axis].max - axes[axis].min);
			}
		}

		function draw() {
			drawGrid();
			for (var i = 0; i < series.length; i++) {
				drawSeries(series[i]);
			}
		}

		function extractRange(ranges, coord) {
			var firstAxis = coord + "axis",
				secondaryAxis = coord + "2axis",
				axis, from, to, reverse;

			if (ranges[firstAxis]) {
				axis = firstAxis;
			}
			else if (ranges[secondaryAxis]) {
				axis = secondaryAxis;
			}
			else {
				return { from: null, to: null, axis: axes[firstAxis] };
			}

			from = ranges[axis].from;
			to = ranges[axis].to;

			if (options[axis].scaleType == 'log') {
				if (from != null)
					from = Math.log(from) * Math.LOG10E;
				if (to != null)
					to = Math.log(to) * Math.LOG10E;
			}

			axis = axes[axis];

			// auto-reverse as an added bonus
			if (from != null && to != null && from > to)
				return { from: to, to: from, axis: axis };

			return { from: from, to: to, axis: axis };
		}

		function drawGrid() {
			var i;

			ctx.save();
			ctx.clearRect(0, 0, canvasWidth, canvasHeight);
			ctx.translate(plotOffset.left, plotOffset.top);

			// draw background, if any
			if (options.grid.backgroundColor) {
				ctx.fillStyle = getColorOrGradient(options.grid.backgroundColor, plotHeight, 0, "rgba(255, 255, 255, 0)");
				ctx.fillRect(0, 0, plotWidth, plotHeight);
			}

			// draw markings
			var markings = options.grid.markings;
			if (markings) {
				if (L.isFunction(markings))
					markings = markings({ xaxis: axes.xaxis, yaxis: axes.yaxis, x2axis: axes.x2axis, y2axis: axes.y2axis });

				for (i = 0; i < markings.length; ++i) {
					var m = markings[i],
						xrange = extractRange(m, "x"),
						yrange = extractRange(m, "y");

					// fill in missing
					if (xrange.from == null)
						xrange.from = xrange.axis.min;
					if (xrange.to == null)
						xrange.to = xrange.axis.max;
					if (yrange.from == null)
						yrange.from = yrange.axis.min;
					if (yrange.to == null)
						yrange.to = yrange.axis.max;

					// clip
					if (xrange.to < xrange.axis.min || xrange.from > xrange.axis.max ||
						yrange.to < yrange.axis.min || yrange.from > yrange.axis.max)
						continue;

					xrange.from = Math.max(xrange.from, xrange.axis.min);
					xrange.to = Math.min(xrange.to, xrange.axis.max);
					yrange.from = Math.max(yrange.from, yrange.axis.min);
					yrange.to = Math.min(yrange.to, yrange.axis.max);

					if (xrange.from == xrange.to && yrange.from == yrange.to)
						continue;

					// then draw
					xrange.from = xrange.axis.p2c(xrange.from);
					xrange.to = xrange.axis.p2c(xrange.to);
					yrange.from = yrange.axis.p2c(yrange.from);
					yrange.to = yrange.axis.p2c(yrange.to);

					if (xrange.from == xrange.to || yrange.from == yrange.to) {
						// draw line
						ctx.strokeStyle = m.color || options.grid.markingsColor;
						ctx.beginPath();
						ctx.lineWidth = m.lineWidth || options.grid.markingsLineWidth;
						ctx.moveTo(xrange.from, yrange.from);
						ctx.lineTo(xrange.to, yrange.to);
						ctx.stroke();
					}
					else {
						// fill area
						ctx.fillStyle = m.color || options.grid.markingsColor;
						ctx.fillRect(xrange.from, yrange.to,
									 xrange.to - xrange.from,
									 yrange.from - yrange.to);
					}
				}
			}

			if(options.grid.show && options.grid.showLines) {
				// draw the inner grid
				ctx.lineWidth = 1;
				ctx.strokeStyle = options.grid.tickColor;
				ctx.beginPath();
				var v, axis = axes.xaxis;
				for (i = 0; i < axis.ticks.length; ++i) {
					v = axis.ticks[i].v;
					if (v <= axis.min || v >= axes.xaxis.max)
						continue;   // skip those lying on the axes
	
					ctx.moveTo(Math.floor(axis.p2c(v)) + ctx.lineWidth/2, 0);
					ctx.lineTo(Math.floor(axis.p2c(v)) + ctx.lineWidth/2, plotHeight);
				}
	
				axis = axes.yaxis;
				for (i = 0; i < axis.ticks.length; ++i) {
					v = axis.ticks[i].v;
					if (v <= axis.min || v >= axis.max)
						continue;
	
					ctx.moveTo(0, Math.floor(axis.p2c(v)) + ctx.lineWidth/2);
					ctx.lineTo(plotWidth, Math.floor(axis.p2c(v)) + ctx.lineWidth/2);
				}
	
				axis = axes.x2axis;
				for (i = 0; i < axis.ticks.length; ++i) {
					v = axis.ticks[i].v;
					if (v <= axis.min || v >= axis.max)
						continue;
	
					ctx.moveTo(Math.floor(axis.p2c(v)) + ctx.lineWidth/2, -5);
					ctx.lineTo(Math.floor(axis.p2c(v)) + ctx.lineWidth/2, 5);
				}
	
				axis = axes.y2axis;
				for (i = 0; i < axis.ticks.length; ++i) {
					v = axis.ticks[i].v;
					if (v <= axis.min || v >= axis.max)
						continue;
	
					ctx.moveTo(plotWidth-5, Math.floor(axis.p2c(v)) + ctx.lineWidth/2);
					ctx.lineTo(plotWidth+5, Math.floor(axis.p2c(v)) + ctx.lineWidth/2);
				}
	
				ctx.stroke();
			}

			if (options.grid.show && options.grid.borderWidth) {
				// draw border
				var bw = options.grid.borderWidth;
				ctx.lineWidth = bw;
				ctx.strokeStyle = options.grid.borderColor;
				ctx.lineJoin = "round";
				ctx.strokeRect(-bw/2, -bw/2, plotWidth + bw, plotHeight + bw);
			}

			ctx.restore();
		}

		function insertLabels() {
			DOM.getElementsByClassName("tickLabels", "div", target, DOM.removeElement);

			var html = ['<div class="tickLabels" style="font-size:smaller;color:' + options.grid.color + '">'];

			function addLabels(axis, labelGenerator) {
				for (var i = 0; i < axis.ticks.length; ++i) {
					var tick = axis.ticks[i];
					if (!tick.label || tick.v < axis.min || tick.v > axis.max)
						continue;
					html.push(labelGenerator(tick, axis));
				}
			}

			var margin = options.grid.labelMargin + options.grid.borderWidth;

			addLabels(axes.xaxis, function (tick, axis) {
				return '<div style="position:absolute;top:' + (plotOffset.top + plotHeight + margin) + 'px;left:' + Math.round(plotOffset.left + axis.p2c(tick.v) - axis.labelWidth/2) + 'px;width:' + axis.labelWidth + 'px;text-align:center" class="tickLabel">' + tick.label + "</div>";
			});


			addLabels(axes.yaxis, function (tick, axis) {
				return '<div style="position:absolute;top:' + Math.round(plotOffset.top + axis.p2c(tick.v) - axis.labelHeight/2) + 'px;right:' + (plotOffset.right + plotWidth + margin) + 'px;width:' + axis.labelWidth + 'px;text-align:right" class="tickLabel">' + tick.label + "</div>";
			});

			addLabels(axes.x2axis, function (tick, axis) {
				return '<div style="position:absolute;bottom:' + (plotOffset.bottom + plotHeight + margin) + 'px;left:' + Math.round(plotOffset.left + axis.p2c(tick.v) - axis.labelWidth/2) + 'px;width:' + axis.labelWidth + 'px;text-align:center" class="tickLabel">' + tick.label + "</div>";
			});

			addLabels(axes.y2axis, function (tick, axis) {
				return '<div style="position:absolute;top:' + Math.round(plotOffset.top + axis.p2c(tick.v) - axis.labelHeight/2) + 'px;left:' + (plotOffset.left + plotWidth + margin) +'px;width:' + axis.labelWidth + 'px;text-align:left" class="tickLabel">' + tick.label + "</div>";
			});

			html.push('</div>');

			target.appendChild(DOM.createElementFromMarkup(html.join("")));
		}

		function insertAxisLabels() {
			var xLocation, yLocation;
			if( options.xaxis.label ) {
				yLocation = plotOffset.top + plotHeight + ( axes.xaxis.labelHeight * 1.5 );
				xLocation = plotOffset.left;
				DOM.getElementsByClassName("xaxislabel", "div", target, DOM.removeElement);
				target.appendChild(
					DOM.createElementFromMarkup(
						"<div class='xaxislabel' style='color:" + options.grid.color + ";width:" + plotWidth + "px;"
							+ "text-align:center;position:absolute;top:" + yLocation + "px;left:" + xLocation + "px;'>"
							+ options.xaxis.label + "</div>"
					)
				);
			}
			if( options.yaxis.label ) {
				xLocation = plotOffset.left - ( axes.yaxis.labelWidth * 2 ) - options.grid.labelFontSize;
				yLocation = plotOffset.top + plotHeight/2;
				DOM.getElementsByClassName("yaxislabel", "div", target, DOM.removeElement);

				target.appendChild(
					DOM.createElementFromMarkup(
						"<div class='yaxislabel' style='-moz-transform:rotate(270deg);-webkit-transform:rotate(270deg);writing-mode:tb-rl;filter:flipV flipH;color:" + options.grid.color + ";"
							+ "text-align:center;position:absolute;top:" + yLocation + "px;left:" + xLocation + "px;'>"
							+ options.yaxis.label + "</div>")
				);
			}
	        }

		function drawSeries(series) {
			if (series.lines.show)
				drawSeriesLines(series);
			if (series.bars.show)
				drawSeriesBars(series);
			if (series.points.show)
				drawSeriesPoints(series);
		}

		function drawSeriesLines(series) {
			function plotLine(data, xoffset, yoffset, axisx, axisy) {
				var prev = null, cur=null, drawx = null, drawy = null;

				ctx.beginPath();
				for (var i = 0; i < data.length; i++) {
					prev = cur;
					cur = data[i];

					if(prev == null || cur == null)
						continue;

					var x1 = prev.x, y1 = prev.y,
						x2 = cur.x, y2 = cur.y;

					// clip with ymin
					if (y1 <= y2 && y1 < axisy.min) {
						if (y2 < axisy.min)
							continue;   // line segment is outside
						// compute new intersection point
						x1 = (axisy.min - y1) / (y2 - y1) * (x2 - x1) + x1;
						y1 = axisy.min;
					}
					else if (y2 <= y1 && y2 < axisy.min) {
						if (y1 < axisy.min)
							continue;
						x2 = (axisy.min - y1) / (y2 - y1) * (x2 - x1) + x1;
						y2 = axisy.min;
					}

					// clip with ymax
					if (y1 >= y2 && y1 > axisy.max) {
						if (y2 > axisy.max)
							continue;
						x1 = (axisy.max - y1) / (y2 - y1) * (x2 - x1) + x1;
						y1 = axisy.max;
					}
					else if (y2 >= y1 && y2 > axisy.max) {
						if (y1 > axisy.max)
							continue;
						x2 = (axisy.max - y1) / (y2 - y1) * (x2 - x1) + x1;
						y2 = axisy.max;
					}

					// clip with xmin
					if (x1 <= x2 && x1 < axisx.min) {
						if (x2 < axisx.min)
							continue;
						y1 = (axisx.min - x1) / (x2 - x1) * (y2 - y1) + y1;
						x1 = axisx.min;
					}
					else if (x2 <= x1 && x2 < axisx.min) {
						if (x1 < axisx.min)
							continue;
						y2 = (axisx.min - x1) / (x2 - x1) * (y2 - y1) + y1;
						x2 = axisx.min;
					}

					// clip with xmax
					if (x1 >= x2 && x1 > axisx.max) {
						if (x2 > axisx.max)
							continue;
						y1 = (axisx.max - x1) / (x2 - x1) * (y2 - y1) + y1;
						x1 = axisx.max;
					}
					else if (x2 >= x1 && x2 > axisx.max) {
						if (x1 > axisx.max)
							continue;
						y2 = (axisx.max - x1) / (x2 - x1) * (y2 - y1) + y1;
						x2 = axisx.max;
					}

					if (drawx != axisx.p2c(x1) + xoffset || drawy != axisy.p2c(y1) + yoffset)
						ctx.moveTo(axisx.p2c(x1) + xoffset, axisy.p2c(y1) + yoffset);

					drawx = axisx.p2c(x2) + xoffset;
					drawy = axisy.p2c(y2) + yoffset;
					ctx.lineTo(axisx.p2c(x2) + xoffset, axisy.p2c(y2) + yoffset);
				}
				ctx.stroke();
			}

			function plotLineArea(data, axisx, axisy) {
				var prev, cur = null,
					bottom = Math.min(Math.max(0, axisy.min), axisy.max),
					top, lastX = 0, areaOpen = false;

				for (var i = 0; i < data.length; i++) {
					prev = cur;
					cur = data[i];

					if (areaOpen && x1 != null && x2 == null) {
						// close area
						ctx.lineTo(axisx.p2c(lastX), axisy.p2c(bottom));
						ctx.fill();
						areaOpen = false;
						continue;
					}

					if (prev == null || cur == null) {
						if(areaOpen) {
							ctx.lineTo(axisx.p2c(lastX), axisy.p2c(bottom));
							ctx.fill();
						}
						areaOpen = false;
						continue;
					}

					var x1 = prev.x, y1 = prev.y,
						x2 = cur.x, y2 = cur.y;

					// clip x values

					// clip with xmin
					if (x1 <= x2 && x1 < axisx.min) {
						if (x2 < axisx.min)
							continue;
						y1 = (axisx.min - x1) / (x2 - x1) * (y2 - y1) + y1;
						x1 = axisx.min;
					}
					else if (x2 <= x1 && x2 < axisx.min) {
						if (x1 < axisx.min)
							continue;
						y2 = (axisx.min - x1) / (x2 - x1) * (y2 - y1) + y1;
						x2 = axisx.min;
					}

					// clip with xmax
					if (x1 >= x2 && x1 > axisx.max) {
						if (x2 > axisx.max)
							continue;
						y1 = (axisx.max - x1) / (x2 - x1) * (y2 - y1) + y1;
						x1 = axisx.max;
					}
					else if (x2 >= x1 && x2 > axisx.max) {
						if (x1 > axisx.max)
							continue;
						y2 = (axisx.max - x1) / (x2 - x1) * (y2 - y1) + y1;
						x2 = axisx.max;
					}

					if (!areaOpen) {
						// open area
						ctx.beginPath();
						ctx.moveTo(axisx.p2c(x1), axisy.p2c(bottom));
						areaOpen = true;
					}

					// now first check the case where both is outside
					if (y1 >= axisy.max && y2 >= axisy.max) {
						ctx.lineTo(axisx.p2c(x1), axisy.p2c(axisy.max));
						ctx.lineTo(axisx.p2c(x2), axisy.p2c(axisy.max));
						lastX = x2;
						continue;
					}
					else if (y1 <= axisy.min && y2 <= axisy.min) {
						ctx.lineTo(axisx.p2c(x1), axisy.p2c(axisy.min));
						ctx.lineTo(axisx.p2c(x2), axisy.p2c(axisy.min));
						lastX = x2;
						continue;
					}

					// else it's a bit more complicated, there might
					// be two rectangles and two triangles we need to fill
					// in; to find these keep track of the current x values
					var x1old = x1, x2old = x2;

					// and clip the y values, without shortcutting

					// clip with ymin
					if (y1 <= y2 && y1 < axisy.min && y2 >= axisy.min) {
						x1 = (axisy.min - y1) / (y2 - y1) * (x2 - x1) + x1;
						y1 = axisy.min;
					}
					else if (y2 <= y1 && y2 < axisy.min && y1 >= axisy.min) {
						x2 = (axisy.min - y1) / (y2 - y1) * (x2 - x1) + x1;
						y2 = axisy.min;
					}

					// clip with ymax
					if (y1 >= y2 && y1 > axisy.max && y2 <= axisy.max) {
						x1 = (axisy.max - y1) / (y2 - y1) * (x2 - x1) + x1;
						y1 = axisy.max;
					}
					else if (y2 >= y1 && y2 > axisy.max && y1 <= axisy.max) {
						x2 = (axisy.max - y1) / (y2 - y1) * (x2 - x1) + x1;
						y2 = axisy.max;
					}


					// if the x value was changed we got a rectangle
					// to fill
					if (x1 != x1old) {
						if (y1 <= axisy.min)
							top = axisy.min;
						else
							top = axisy.max;

						ctx.lineTo(axisx.p2c(x1old), axisy.p2c(top));
						ctx.lineTo(axisx.p2c(x1), axisy.p2c(top));
					}

					// fill the triangles
					ctx.lineTo(axisx.p2c(x1), axisy.p2c(y1));
					ctx.lineTo(axisx.p2c(x2), axisy.p2c(y2));

					// fill the other rectangle if it's there
					if (x2 != x2old) {
						if (y2 <= axisy.min)
							top = axisy.min;
						else
							top = axisy.max;

						ctx.lineTo(axisx.p2c(x2), axisy.p2c(top));
						ctx.lineTo(axisx.p2c(x2old), axisy.p2c(top));
					}

					lastX = Math.max(x2, x2old);
				}

				if (areaOpen) {
					ctx.lineTo(axisx.p2c(lastX), axisy.p2c(bottom));
					ctx.fill();
				}
			}

			ctx.save();
			ctx.translate(plotOffset.left, plotOffset.top);
			ctx.lineJoin = "round";

			var lw = series.lines.lineWidth,
				sw = series.shadowSize;
			// FIXME: consider another form of shadow when filling is turned on
			if (lw > 0 && sw > 0) {
				// draw shadow as a thick and thin line with transparency
				ctx.lineWidth = sw;
				ctx.strokeStyle = "rgba(0,0,0,0.1)";
				var xoffset = 1;
				plotLine(series.data, xoffset, Math.sqrt((lw/2 + sw/2)*(lw/2 + sw/2) - xoffset*xoffset), series.xaxis, series.yaxis);
				ctx.lineWidth = sw/2;
				plotLine(series.data, xoffset, Math.sqrt((lw/2 + sw/4)*(lw/2 + sw/4) - xoffset*xoffset), series.xaxis, series.yaxis);
			}

			ctx.lineWidth = lw;
			ctx.strokeStyle = series.color;
			var fillStyle = getFillStyle(series.lines, series.color, 0, plotHeight);
			if (fillStyle) {
				ctx.fillStyle = fillStyle;
				plotLineArea(series.data, series.xaxis, series.yaxis);
			}

			if (lw > 0)
				plotLine(series.data, 0, 0, series.xaxis, series.yaxis);
			ctx.restore();
		}

		function drawSeriesPoints(series) {
			function plotPoints(data, radius, fillStyle, offset, circumference, axisx, axisy) {
				for (var i = 0; i < data.length; i++) {
					if (data[i] == null || series.dropped[i])
						continue;

					var x = data[i].x, y = data[i].y;
					if (x < axisx.min || x > axisx.max || y < axisy.min || y > axisy.max)
						continue;

					ctx.beginPath();
					ctx.arc(axisx.p2c(x), axisy.p2c(y) + offset, radius, 0, circumference, true);
					if (fillStyle) {
						ctx.fillStyle = fillStyle;
						ctx.fill();
					}
					ctx.stroke();
				}
			}

			ctx.save();
			ctx.translate(plotOffset.left, plotOffset.top);

			var lw = series.lines.lineWidth,
				sw = series.shadowSize,
				radius = series.points.radius;
			if (lw > 0 && sw > 0) {
				// draw shadow in two steps
				var w = sw / 2;
				ctx.lineWidth = w;
				ctx.strokeStyle = "rgba(0,0,0,0.1)";
				plotPoints(series.data, radius, null, w + w/2, 2 * Math.PI,
						   series.xaxis, series.yaxis);

				ctx.strokeStyle = "rgba(0,0,0,0.2)";
				plotPoints(series.data, radius, null, w/2, 2 * Math.PI,
						   series.xaxis, series.yaxis);
			}

			ctx.lineWidth = lw;
			ctx.strokeStyle = series.color;
			plotPoints(series.data, radius,
					   getFillStyle(series.points, series.color), 0, 2 * Math.PI,
					   series.xaxis, series.yaxis);
			ctx.restore();
		}

		function drawBar(x, y, barLeft, barRight, offset, fill, axisx, axisy, c) {
			var drawLeft = true, drawRight = true,
				drawTop = true, drawBottom = false,
				left = x + barLeft, right = x + barRight,
				bottom = 0, top = y;

			// account for negative bars
			if (top < bottom) {
				top = 0;
				bottom = y;
				drawBottom = true;
				drawTop = false;
			}
		   
			// clip
			if (right < axisx.min || left > axisx.max ||
				top < axisy.min || bottom > axisy.max)
				return;

			if (left < axisx.min) {
				left = axisx.min;
				drawLeft = false;
			}

			if (right > axisx.max) {
				right = axisx.max;
				drawRight = false;
			}

			if (bottom < axisy.min) {
				bottom = axisy.min;
				drawBottom = false;
			}

			if (top > axisy.max) {
				top = axisy.max;
				drawTop = false;
			}

			left = axisx.p2c(left);
			bottom = axisy.p2c(bottom);
			right = axisx.p2c(right);
			top = axisy.p2c(top);

			// fill the bar
			if (fill) {
				c.beginPath();
				c.moveTo(left, bottom);
				c.lineTo(left, top);
				c.lineTo(right, top);
				c.lineTo(right, bottom);
				if(typeof fill === 'function') {
					c.fillStyle = fill(bottom, top);
				} else if(typeof fill === 'string') {
					c.fillStyle = fill;
				}
				c.fill();
			}

			// draw outline
			if (drawLeft || drawRight || drawTop || drawBottom) {
				c.beginPath();

				// FIXME: inline moveTo is buggy with excanvas
				c.moveTo(left, bottom + offset);
				if (drawLeft)
					c.lineTo(left, top + offset);
				else
					c.moveTo(left, top + offset);
				if (drawTop)
					c.lineTo(right, top + offset);
				else
					c.moveTo(right, top + offset);
				if (drawRight)
					c.lineTo(right, bottom + offset);
				else
					c.moveTo(right, bottom + offset);
				if (drawBottom)
					c.lineTo(left, bottom + offset);
				else
					c.moveTo(left, bottom + offset);
				c.stroke();
			}
		}

		function drawSeriesBars(series) {
			function plotBars(data, barLeft, barRight, offset, fill, axisx, axisy) {

				for (var i = 0; i < data.length; i++) {
					if (data[i] == null)
						continue;
					drawBar(data[i].x, data[i].y, barLeft, barRight, offset, fill, axisx, axisy, ctx);
				}
			}

			ctx.save();
			ctx.translate(plotOffset.left, plotOffset.top);

			// FIXME: figure out a way to add shadows (for instance along the right edge)
			ctx.lineWidth = series.bars.lineWidth;
			ctx.strokeStyle = series.color;
			var barLeft = series.bars.align == "left" ? 0 : -series.bars.barWidth/2;
			var fill = series.bars.fill ? function (bottom, top) { return getFillStyle(series.bars, series.color, bottom, top); } : null;
			plotBars(series.data, barLeft, barLeft + series.bars.barWidth, 0, fill, series.xaxis, series.yaxis);
			ctx.restore();
		}

		function getFillStyle(filloptions, seriesColor, bottom, top) {
			var fill = filloptions.fill;
			if (!fill)
				return null;

			if (filloptions.fillColor)
				return getColorOrGradient(filloptions.fillColor, bottom, top, seriesColor);

			var c = parseColor(seriesColor);
			c.a = typeof fill == "number" ? fill : 0.4;
			c.normalize();
			return c.toString();
		}

		function insertLegend() {
			DOM.getElementsByClassName("legend", "div", target, DOM.removeElement);

			if (!options.legend.show)
				return;

			var fragments = [], rowStarted = false,
				lf = options.legend.labelFormatter, s, label;
			for (var i = 0; i < series.length; ++i) {
				s = series[i];
				label = s.label;
				if (!label)
					continue;

				if (i % options.legend.noColumns == 0) {
					if (rowStarted)
						fragments.push('</tr>');
					fragments.push('<tr>');
					rowStarted = true;
				}

				if (lf)
					label = lf(label, s);

				fragments.push(
					'<td class="legendColorBox"><div style="border:1px solid ' + options.legend.labelBoxBorderColor + ';padding:1px"><div style="width:4px;height:0;border:5px solid ' + s.color + ';overflow:hidden"></div></div></td>' +
					'<td class="legendLabel">' + label + '</td>');
			}
			if (rowStarted)
				fragments.push('</tr>');

			if (fragments.length == 0)
				return;

			var table = '<table style="font-size:smaller;color:' + options.grid.color + '">' + fragments.join("") + '</table>';
			if (options.legend.container != null)
				DOM.get(options.legend.container).innerHTML = table;
			else {
				var pos = "",
					p = options.legend.position,
					m = options.legend.margin;
				if (m[0] == null)
					m = [m, m];
				if (p.charAt(0) == "n")
					pos += 'top:' + (m[1] + plotOffset.top) + 'px;';
				else if (p.charAt(0) == "s")
					pos += 'bottom:' + (m[1] + plotOffset.bottom) + 'px;';
				if (p.charAt(1) == "e")
					pos += 'right:' + (m[0] + plotOffset.right) + 'px;';
				else if (p.charAt(1) == "w")
					pos += 'left:' + (m[0] + plotOffset.left) + 'px;';
				var legend = target.appendChild(DOM.createElementFromMarkup('<div class="legend">' + table.replace('style="', 'style="position:absolute;' + pos +';') + '</div>'));
				if (options.legend.backgroundOpacity != 0.0) {
					// put in the transparent background
					// separately to avoid blended labels and
					// label boxes
					var c = options.legend.backgroundColor;
					if (c == null) {
						var tmp;
						if (options.grid.backgroundColor && typeof options.grid.backgroundColor == "string")
							tmp = options.grid.backgroundColor;
						else
							tmp = extractColor(legend);
						c = parseColor(tmp).adjust(null, null, null, 1).toString();
					}
					var div = legend.firstChild;
					var _el = DOM.insertBefore(
								DOM.createElementFromMarkup('<div style="position:absolute;width:' + parseInt(DOM.getStyle(div, 'width'), 10)
											+ 'px;height:' + parseInt(DOM.getStyle(div, 'height'), 10) + 'px;'
											+ pos +'background-color:' + c + ';"> </div>'),
								legend
							);
					DOM.setStyle(_el, 'opacity', options.legend.backgroundOpacity);
				}
			}
		}


		// interactive features

		var lastMousePos = { pageX: null, pageY: null },
			selection = {
				first: { x: -1, y: -1}, second: { x: -1, y: -1},
				show: false, active: false },
			crosshair = { pos: { x: -1, y: -1 } },
			highlights = [],
			clickIsMouseUp = false,
			redrawTimeout = null,
			hoverTimeout = null;

		// Returns the data item the mouse is over, or null if none is found
		function findNearbyItem(mouseX, mouseY) {
			var maxDistance = options.grid.mouseActiveRadius,
				lowestDistance = maxDistance * maxDistance + 1,
				item = null, foundPoint = false, j, x, y;

			function result(i, j) {
				return {
					datapoint: series[i].data[j],
					dataIndex: j,
					series: series[i],
					seriesIndex: i
				};
			}

			for (var i = 0; i < series.length; ++i) {
				var s = series[i],
					axisx = s.xaxis,
					axisy = s.yaxis,
					mx = axisx.c2p(mouseX), // precompute some stuff to make the loop faster
					my = axisy.c2p(mouseY),
					maxx = maxDistance / axisx.scale,
					maxy = maxDistance / axisy.scale;

				var data = s.data;

				if (s.lines.show || s.points.show) {
					for (j = 0; j < data.length; j++ ) {
						if (data[j] == null)
							continue;

						x = data[j].x;
						y = data[j].y;

						// For points and lines, the cursor must be within a
						// certain distance to the data point
						if (x - mx > maxx || x - mx < -maxx ||
							y - my > maxy || y - my < -maxy)
							continue;

						// We have to calculate distances in pixels, not in
						// data units, because the scales of the axes may be different
						var dx = Math.abs(axisx.p2c(x) - mouseX),
							dy = Math.abs(axisy.p2c(y) - mouseY),
							dist = dx * dx + dy * dy; // no idea in taking sqrt
						if (dist < lowestDistance) {
							lowestDistance = dist;
							item = result(i, j);
						}
					}
				}

				if (s.bars.show && !item) { // no other point can be nearby
					var barLeft = s.bars.align == "left" ? 0 : -s.bars.barWidth/2,
						barRight = barLeft + s.bars.barWidth;

					for (j = 0; j < data.length; j++) {
						x = data[j].x;
						y = data[j].y;
						if (x == null)
							continue;
  
						// for a bar graph, the cursor must be inside the bar
						if ((mx >= x + barLeft && mx <= x + barRight &&
							 my >= Math.min(0, y) && my <= Math.max(0, y)))
								item = result(i, j);
					}
				}
			}

			return item;
		}

		function onMouseMove(e) {
			lastMousePos.pageX = E.getPageX(e);
			lastMousePos.pageY = E.getPageY(e);

			if (options.grid.hoverable)
				triggerClickHoverEvent("plothover", lastMousePos);

			if (options.crosshair.mode != null) {
				if (!selection.active) {
					setPositionFromEvent(crosshair.pos, lastMousePos);
					triggerRedrawOverlay();
				}
				else
					crosshair.pos.x = -1; // hide the crosshair while selecting
			}

			if (selection.active) {
				updateSelection(lastMousePos);
			}
		}

		function onMouseDown(e) {
			var button = e.which || e.button;
			if (button != 1)  // only accept left-click
				return;

			// cancel out any text selections
			document.body.focus();

			// prevent text selection and drag in old-school browsers
			if (document.onselectstart !== undefined && workarounds.onselectstart == null) {
				workarounds.onselectstart = document.onselectstart;
				document.onselectstart = function () { return false; };
			}
			if (document.ondrag !== undefined && workarounds.ondrag == null) {
				workarounds.ondrag = document.ondrag;
				document.ondrag = function () { return false; };
			}

			var mousePos = {pageX: E.getPageX(e), pageY: E.getPageY(e)};
			setSelectionPos(selection.first, mousePos);

			lastMousePos.pageX = null;
			selection.active = true;
			E.on(document, "mouseup", onSelectionMouseUp);
		}

		function onMouseOut(e) {
			if (options.crosshair.mode != null && crosshair.pos.x != -1) {
				crosshair.pos.x = -1;
				triggerRedrawOverlay();
			}
		}

		function onClick(e) {
			if (clickIsMouseUp) {
				clickIsMouseUp = false;
				return;
			}

			var mousePos = {pageX: E.getPageX(e), pageY: E.getPageY(e)};
			triggerClickHoverEvent("plotclick", mousePos);
		}

		// trigger click or hover event (they send the same parameters
		// so we share their code)
		function triggerClickHoverEvent(eventname, event) {
			var offset = DOM.getXY(eventHolder[0]),
				pos = { pageX: event.pageX, pageY: event.pageY },
				canvasX = event.pageX - offset[0] - plotOffset.left,
				canvasY = event.pageY - offset[1] - plotOffset.top;

			for(var axis in axes)
				if(axes[axis].used)
					pos[axis.replace(/axis$/, '')] = axes[axis].c2p(axis.charAt(0) == 'x' ? canvasX :  canvasY);

			var item = findNearbyItem(canvasX, canvasY);

			if (item) {
				// fill in mouse pos for any listeners out there
				item.pageX = parseInt(item.series.xaxis.p2c(item.datapoint.x) + offset[0] + plotOffset.left, 10);
				item.pageY = parseInt(item.series.yaxis.p2c(item.datapoint.y) + offset[1] + plotOffset.top, 10);
			}

			if (options.grid.autoHighlight) {
				// clear auto-highlights
				for (var i = 0; i < highlights.length; ++i) {
					var h = highlights[i];
					if (h.auto == eventname &&
						!(item && h.series == item.series && h.point == item.datapoint))
						unhighlight(h.series, h.point);
				}

				if (item)
					highlight(item.series, item.datapoint, eventname);
			}

			plot.fireEvent(eventname, {pos: pos, item: item });
		}

		function triggerRedrawOverlay() {
			if (!redrawTimeout)
				redrawTimeout = setTimeout(redrawOverlay, 30);
		}

		function redrawOverlay() {
			redrawTimeout = null;

			// redraw highlights
			octx.save();
			octx.clearRect(0, 0, canvasWidth, canvasHeight);
			octx.translate(plotOffset.left, plotOffset.top);

			var hi;
			for (var i = 0; i < highlights.length; ++i) {
				hi = highlights[i];

				if (hi.series.bars.show)
					drawBarHighlight(hi.series, hi.point);
				else
					drawPointHighlight(hi.series, hi.point);
			}

			// redraw selection
			if (selection.show && selectionIsSane()) {
				octx.strokeStyle = parseColor(options.selection.color).scale(null, null, null, 0.8).toString();
				octx.lineWidth = 1;
				ctx.lineJoin = "round";
				octx.fillStyle = parseColor(options.selection.color).scale(null, null, null, 0.4).toString();

				var x = Math.min(selection.first.x, selection.second.x),
					y = Math.min(selection.first.y, selection.second.y),
					w = Math.abs(selection.second.x - selection.first.x),
					h = Math.abs(selection.second.y - selection.first.y);

				octx.fillRect(x, y, w, h);
				octx.strokeRect(x, y, w, h);
			}

			// redraw crosshair
			var pos = crosshair.pos, mode = options.crosshair.mode;
			if (mode != null && pos.x != -1) {
				octx.strokeStyle = parseColor(options.crosshair.color).scale(null, null, null, 0.8).toString();
				octx.lineWidth = 1;
				ctx.lineJoin = "round";

				octx.beginPath();
				if (mode.indexOf("x") != -1) {
					octx.moveTo(pos.x, 0);
					octx.lineTo(pos.x, plotHeight);
				}
				if (mode.indexOf("y") != -1) {
					octx.moveTo(0, pos.y);
					octx.lineTo(plotWidth, pos.y);
				}
				octx.stroke();

			}
			octx.restore();
		}

		function highlight(s, point, auto) {
			if (typeof s == "number")
				s = series[s];

			if (typeof point == "number")
				point = s.data[point];

			var i = indexOfHighlight(s, point);
			if (i == -1) {
				highlights.push({ series: s, point: point, auto: auto });

				triggerRedrawOverlay();
			}
			else if (!auto)
				highlights[i].auto = false;
		}

		function unhighlight(s, point) {
			if (typeof s == "number")
				s = series[s];

			if (typeof point == "number")
				point = s.data[point];

			var i = indexOfHighlight(s, point);
			if (i != -1) {
				highlights.splice(i, 1);

				triggerRedrawOverlay();
			}
		}

		function indexOfHighlight(s, p) {
			for (var i = 0; i < highlights.length; ++i) {
				var h = highlights[i];
				if (h.series == s && h.point[0] == p[0]
					&& h.point[1] == p[1])
					return i;
			}
			return -1;
		}

		function drawPointHighlight(series, point) {
			var x = point.x, y = point.y,
				axisx = series.xaxis, axisy = series.yaxis;

			if (x < axisx.min || x > axisx.max || y < axisy.min || y > axisy.max)
				return;

			var pointRadius = series.points.radius + series.points.lineWidth / 2;
			octx.lineWidth = pointRadius;
			octx.strokeStyle = parseColor(series.color).scale(1, 1, 1, 0.5).toString();
			var radius = 1.5 * pointRadius;
			octx.beginPath();
			octx.arc(axisx.p2c(x), axisy.p2c(y), radius, 0, 2 * Math.PI, true);
			octx.stroke();
		}

		function drawBarHighlight(series, point) {
			octx.lineJoin = "round";
			octx.lineWidth = series.bars.lineWidth;
			octx.strokeStyle = parseColor(series.color).scale(1, 1, 1, 0.5).toString();
			var fillStyle = parseColor(series.color).scale(1, 1, 1, 0.5).toString();
			var barLeft = series.bars.align == "left" ? 0 : -series.bars.barWidth/2;
			drawBar(point.x, point.y, barLeft, barLeft + series.bars.barWidth,
					0, function () { return fillStyle; }, series.xaxis, series.yaxis, octx);
		}

		function setPositionFromEvent(pos, e) {
			var offset = DOM.getXY(eventHolder[0]);
			pos.x = clamp(0, e.pageX - offset[0] - plotOffset.left, plotWidth);
			pos.y = clamp(0, e.pageY - offset[1] - plotOffset.top, plotHeight);
		}

		function setCrosshair(pos) {
			if (pos == null)
				crosshair.pos.x = -1;
			else {
				crosshair.pos.x = clamp(0, pos.x != null ? axes.xaxis.p2c(pos.x) : axes.x2axis.p2c(pos.x2), plotWidth);
				crosshair.pos.y = clamp(0, pos.y != null ? axes.yaxis.p2c(pos.y) : axes.y2axis.p2c(pos.y2), plotHeight);
			}
			triggerRedrawOverlay();
		}

		function getSelectionForEvent() {
			var x1 = Math.min(selection.first.x, selection.second.x),
				x2 = Math.max(selection.first.x, selection.second.x),
				y1 = Math.max(selection.first.y, selection.second.y),
				y2 = Math.min(selection.first.y, selection.second.y);

			var r = {};
			if (axes.xaxis.used)
				r.xaxis = { from: axes.xaxis.c2p(x1), to: axes.xaxis.c2p(x2) };
			if (axes.x2axis.used)
				r.x2axis = { from: axes.x2axis.c2p(x1), to: axes.x2axis.c2p(x2) };
			if (axes.yaxis.used)
				r.yaxis = { from: axes.yaxis.c2p(y1), to: axes.yaxis.c2p(y2) };
			if (axes.y2axis.used)
				r.y2axis = { from: axes.y2axis.c2p(y1), to: axes.y2axis.c2p(y2) };
			return r;
		}

		function triggerSelectedEvent() {
			var r = getSelectionForEvent();

			plot.fireEvent("plotselected", r);
		}

		function onSelectionMouseUp(e) {
			// revert drag stuff for old-school browsers
			if (document.onselectstart !== undefined)
				document.onselectstart = workarounds.onselectstart;
			if (document.ondrag !== undefined)
				document.ondrag = workarounds.ondrag;

			// no more draggy-dee-drag
			selection.active = false;
			var mousePos = {pageX: E.getPageX(e), pageY: E.getPageY(e)};
			updateSelection(mousePos);

			if (selectionIsSane()) {
				triggerSelectedEvent();
				clickIsMouseUp = true;
			}
			else {
				// this counts as a clear
				plot.fireEvent("plotunselected", {});
			}

			E.removeListener(document, "mouseup", onSelectionMouseUp);
			return false;
		}

		function setSelectionPos(pos, e) {
			setPositionFromEvent(pos, e);

			if (options.selection.mode == "y") {
				if (pos == selection.first)
					pos.x = 0;
				else
					pos.x = plotWidth;
			}

			if (options.selection.mode == "x") {
				if (pos == selection.first)
					pos.y = 0;
				else
					pos.y = plotHeight;
			}
		}

		function updateSelection(pos) {
			if (pos.pageX == null)
				return;

			setSelectionPos(selection.second, pos);
			if (selectionIsSane()) {
				selection.show = true;
				triggerRedrawOverlay();
			}
			else
				clearSelection(true);
		}

		function clearSelection(preventEvent) {
			if (selection.show) {
				selection.show = false;
				triggerRedrawOverlay();
				if (!preventEvent)
					plot.fireEvent("plotunselected", {});
			}
		}

		function setSelection(ranges, preventEvent) {
			var range;

			if (options.selection.mode == "y") {
				selection.first.x = 0;
				selection.second.x = plotWidth;
			}
			else {
				range = extractRange(ranges, "x");

				selection.first.x = range.axis.p2c(range.from);
				selection.second.x = range.axis.p2c(range.to);
			}

			if (options.selection.mode == "x") {
				selection.first.y = 0;
				selection.second.y = plotHeight;
			}
			else {
				range = extractRange(ranges, "y");

				selection.first.y = range.axis.p2c(range.from);
				selection.second.y = range.axis.p2c(range.to);
			}

			selection.show = true;
			triggerRedrawOverlay();
			if (!preventEvent)
				triggerSelectedEvent();
		}

		function selectionIsSane() {
			var minSize = 5;
			return Math.abs(selection.second.x - selection.first.x) >= minSize &&
				Math.abs(selection.second.y - selection.first.y) >= minSize;
		}

		function getColorOrGradient(spec, bottom, top, defaultColor) {
			if (typeof spec == "string")
				return spec;
			else {
				// assume this is a gradient spec; IE currently only
				// supports a simple vertical gradient properly, so that's
				// what we support too
				var gradient = ctx.createLinearGradient(0, top, 0, bottom);

				for (var i = 0, l = spec.colors.length; i < l; ++i) {
					var c = spec.colors[i];
					gradient.addColorStop(i / (l - 1), typeof c == "string" ? c : parseColor(defaultColor).scale(c.brightness, c.brightness, c.brightness, c.opacity));
				}

				return gradient;
			}
		}
	}

	L.augment(Plot, YAHOO.util.EventProvider);

	YAHOO.widget.Flot = function(target, data, options) {
		return new Plot(target, data, options);
	};

	// round to nearby lower multiple of base
	function floorInBase(n, base) {
		return base * Math.floor(n / base);
	}

	function clamp(min, value, max) {
		if (value < min)
			return min;
		else if (value > max)
			return max;
		else
			return value;
	}

	// color helpers, inspiration from the jquery color animation
	// plugin by John Resig
	function Color (r, g, b, a) {
	   
		var rgba = ['r','g','b','a'];
		var x = 4; //rgba.length
	   
		while (-1<--x) {
			this[rgba[x]] = arguments[x] || ((x==3) ? 1.0 : 0);
		}
	   
		this.toString = function() {
			if (this.a >= 1.0) {
				return "rgb("+[this.r,this.g,this.b].join(",")+")";
			} else {
				return "rgba("+[this.r,this.g,this.b,this.a].join(",")+")";
			}
		};

		this.scale = function(rf, gf, bf, af) {
			x = 4; //rgba.length
			while (-1<--x) {
				if (arguments[x] != null)
					this[rgba[x]] *= arguments[x];
			}
			return this.normalize();
		};

		this.adjust = function(rd, gd, bd, ad) {
			x = 4; //rgba.length
			while (-1<--x) {
				if (arguments[x] != null)
					this[rgba[x]] += arguments[x];
			}
			return this.normalize();
		};

		this.clone = function() {
			return new Color(this.r, this.b, this.g, this.a);
		};

		var limit = function(val,minVal,maxVal) {
			return Math.max(Math.min(val, maxVal), minVal);
		};

		this.normalize = function() {
			this.r = clamp(0, parseInt(this.r, 10), 255);
			this.g = clamp(0, parseInt(this.g, 10), 255);
			this.b = clamp(0, parseInt(this.b, 10), 255);
			this.a = clamp(0, this.a, 1);
			return this;
		};

		this.normalize();
	}

	var lookupColors = {
		aqua:[0,255,255],
		azure:[240,255,255],
		beige:[245,245,220],
		black:[0,0,0],
		blue:[0,0,255],
		brown:[165,42,42],
		cyan:[0,255,255],
		darkblue:[0,0,139],
		darkcyan:[0,139,139],
		darkgrey:[169,169,169],
		darkgreen:[0,100,0],
		darkkhaki:[189,183,107],
		darkmagenta:[139,0,139],
		darkolivegreen:[85,107,47],
		darkorange:[255,140,0],
		darkorchid:[153,50,204],
		darkred:[139,0,0],
		darksalmon:[233,150,122],
		darkviolet:[148,0,211],
		fuchsia:[255,0,255],
		gold:[255,215,0],
		green:[0,128,0],
		indigo:[75,0,130],
		khaki:[240,230,140],
		lightblue:[173,216,230],
		lightcyan:[224,255,255],
		lightgreen:[144,238,144],
		lightgrey:[211,211,211],
		lightpink:[255,182,193],
		lightyellow:[255,255,224],
		lime:[0,255,0],
		magenta:[255,0,255],
		maroon:[128,0,0],
		navy:[0,0,128],
		olive:[128,128,0],
		orange:[255,165,0],
		pink:[255,192,203],
		purple:[128,0,128],
		violet:[128,0,128],
		red:[255,0,0],
		silver:[192,192,192],
		white:[255,255,255],
		yellow:[255,255,0]
	};

	function extractColor(element) {
		var color, elem = element;
		do {
			color = DOM.getStyle(elem, 'backgroundColor').toLowerCase();
			// keep going until we find an element that has color, or
			// we hit the body
			if (color != '' && color != 'transparent')
				break;
			elem = elem.parentNode;
		} while (!elem.nodeName == "body");

		// catch Safari's way of signalling transparent
		if (color == "rgba(0, 0, 0, 0)")
			return "transparent";

		return color;
	}

	// parse string, returns Color
	function parseColor(str) {
		var result;

		// Look for rgb(num,num,num)
		if (result = /rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(str))
			return new Color(parseInt(result[1], 10), parseInt(result[2], 10), parseInt(result[3], 10));

		// Look for rgba(num,num,num,num)
		if (result = /rgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(str))
			return new Color(parseInt(result[1], 10), parseInt(result[2], 10), parseInt(result[3], 10), parseFloat(result[4]));

		// Look for rgb(num%,num%,num%)
		if (result = /rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(str))
			return new Color(parseFloat(result[1])*2.55, parseFloat(result[2])*2.55, parseFloat(result[3])*2.55);

		// Look for rgba(num%,num%,num%,num)
		if (result = /rgba\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(str))
			return new Color(parseFloat(result[1])*2.55, parseFloat(result[2])*2.55, parseFloat(result[3])*2.55, parseFloat(result[4]));

		// Look for #a0b1c2
		if (result = /#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(str))
			return new Color(parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16));

		// Look for #fff
		if (result = /#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(str))
			return new Color(parseInt(result[1]+result[1], 16), parseInt(result[2]+result[2], 16), parseInt(result[3]+result[3], 16));

		// Otherwise, we're most likely dealing with a named color
		var name = L.trim(str).toLowerCase();
		if (name == "transparent")
			return new Color(255, 255, 255, 0);
		else {
			result = lookupColors[name];
			return new Color(result[0], result[1], result[2]);
		}
	}

})();
