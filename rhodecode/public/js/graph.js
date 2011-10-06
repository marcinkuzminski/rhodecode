// branch_renderer.js - Rendering of branch DAGs on the client side
//
// Copyright 2010 Marcin Kuzminski <marcin AT python-works DOT com>
// Copyright 2008 Jesper Noehr <jesper AT noehr DOT org>
// Copyright 2008 Dirkjan Ochtman <dirkjan AT ochtman DOT nl>
// Copyright 2006 Alexander Schremmer <alex AT alexanderweb DOT de>
//
// derived from code written by Scott James Remnant <scott@ubuntu.com>
// Copyright 2005 Canonical Ltd.
//
// This software may be used and distributed according to the terms
// of the GNU General Public License, incorporated herein by reference.

var colors = [
	[ 1.0, 0.0, 0.0 ],
	[ 1.0, 1.0, 0.0 ],
	[ 0.0, 1.0, 0.0 ],
	[ 0.0, 1.0, 1.0 ],
	[ 0.0, 0.0, 1.0 ],
	[ 1.0, 0.0, 1.0 ],
	[ 1.0, 1.0, 0.0 ],
	[ 0.0, 0.0, 0.0 ]
];

function BranchRenderer() {
	
	this.canvas = document.getElementById("graph_canvas");
	
	if (navigator.userAgent.indexOf('MSIE') >= 0) 
		this.canvas = window.G_vmlCanvasManager.initElement(this.canvas);
	this.ctx = this.canvas.getContext('2d');
	this.ctx.strokeStyle = 'rgb(0, 0, 0)';
	this.ctx.fillStyle = 'rgb(0, 0, 0)';
	this.cur = [0, 0];
	this.max_column = 1;
	this.line_width = 2.5;
	this.dot_radius = 5.5;
	this.bg = [0, 4];
	this.cell = [2, 0];
	this.revlink = '';
	
	this.scale = function(height) {
		this.box_size = Math.floor(height/1.2);
		this.cell_height = this.box_size;
		this.bg_height = height;
	}
	
	this.setColor = function(color, bg, fg) {
		color %= colors.length;
		var red = (colors[color][0] * fg) || bg;
		var green = (colors[color][1] * fg) || bg;
		var blue = (colors[color][2] * fg) || bg;
		red = Math.round(red * 255);
		green = Math.round(green * 255);
		blue = Math.round(blue * 255);
		var s = 'rgb(' + red + ', ' + green + ', ' + blue + ')';
		this.ctx.strokeStyle = s;
		this.ctx.fillStyle = s;
	}

	this.render = function(data,pad) {
		var idx = 1;
		var rela = document.getElementById('graph');
		var pad = pad;
		var scale = 22;
		
		for (var i in data) {
			this.scale(scale);
			var row = document.getElementById("chg_"+idx);
			var	next = document.getElementById("chg_"+idx+1);
			var extra = 0;
			
			//skip this since i don't have DATE in my app
			//if (next.is('.changesets-date')) {
			//	extra = next.outerHeight();
			//}
						
			this.cell[1] += row.clientWidth;
			this.bg[1] += this.bg_height;
			
			cur = data[i];
			nodeid = cur[0];
			node = cur[1];
			in_l = cur[2];
			
			for (var j in in_l) {
				
				line = in_l[j];
				start = line[0];
				end = line[1];
				color = line[2];

				if (start > this.max_column) {
					this.max_column = start;
				}
				
				if (end > this.max_column) {
					this.max_column = end;
				}
				
				this.setColor(color, 0.0, 0.65);
				
				y = row.offsetTop-rela.offsetTop+4;
				x = pad-((this.cell[0] + this.box_size * start - 1) + this.bg_height-2);
				
				this.ctx.lineWidth=this.line_width;
				this.ctx.beginPath();
				this.ctx.moveTo(x, y);

				y += row.offsetHeight;
				x = pad-((1 + this.box_size * end) + this.bg_height-2);
				this.ctx.lineTo(x,y+extra,3);
				this.ctx.stroke();
			}
			
			column = node[0]
			color = node[1]
			
			radius = this.dot_radius;
			y = row.offsetTop-rela.offsetTop+4;
			x = pad-(Math.round(this.cell[0] * scale/2 * column + radius) + 15 - (column*4));
		
			this.ctx.beginPath();
			this.setColor(color, 0.25, 0.75);
			this.ctx.arc(x, y, radius, 0, Math.PI * 2, true);
			this.ctx.fill();
			
			idx++;
		}
				
	}

}
