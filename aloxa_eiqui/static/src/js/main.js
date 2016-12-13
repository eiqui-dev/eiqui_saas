/*#################################################################################
#
#    Copyright (C) 2016 Solucións Aloxa S.L. <info@aloxa.eu>
#						Alexandre Díaz <alex@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################*/
odoo.define('aloxa_eiqui.main', function (require) {
	'use strict';
	var ajax = require('web.ajax');
	var core = require('web.core');
	var _t = core._t;

	
	/** GENERAL EIQUI **/
	var AloxaEiqui = {
		loadTimeout: false,
		
		////////////////////////
		init: function() {
			jQuery(function($){AloxaEiqui.onPageLoad($);});
			return this;
		},
		
		////////////////////////
		onPageLoad: function($) {
			$('.select2-control').each(function(){ $(this).select2(); });
			
			$('.eiqui-message-item').each(function(i, elm){
				setTimeout(function(){
					$(elm).animate({'margin-top':0, 'opacity':'1.0'}, 'slow');
				}, 100*i);
			});
		},
		
		////////////////////////
		addAlert: function(title, msg) {
			var html = "<div class='alert alert-danger alert-dismissible fade in' role='alert' id='alert'>"+
			"<button type='button' class='close' data-dismiss='alert' aria-label='"+_t('Close')+"'>"+
			"<span aria-hidden='true'>×</span>"+
			"</button>"+
			"<h4>"+title+"</h4>"+
			"<p>"+msg+"</p>"+
			"</div>";
			$('#alerts').prepend(html);
		},
		
		checkResponse: function(data)
		{  
			if (data && data['error'])
			{
				this.addAlert(_t('Oops! something went wrong :S'), data['errormsg']);
				return false;
			}
			return true;
		},
		
		////////////////////////
		getCoreBabel: function() {
			return _t;
		},
		
		////////////////////////
		loadAjax: function(url, params, callback)
		{
			if (typeof params === 'undefined')
				params['csrf_token'] = [];
			params['csrf_token'] = core.csrf_token;
			
			$('#eiqui-ajax').css({'padding':'15px'});
			this.loadTimeout = setTimeout(function($this){
				var offLeft = $this[0].offsetLeft;
				var offTop = $this[0].offsetTop;
				var $div = $('<div/>', {
				    id: 'load_ajax_info',
				    title: _t('Loading Data...'),
				    class: 'eiqui-load-ajax text-center',
				    css: {
				    	'position':'absolute', 
				    	'z-index': 110,
				    }
				});
				var $shadow = $('<div/>', {
					id: 'load_ajax_shadow',
					css: {
						'position': 'absolute',
						'top': offTop+'px',
						'left': offLeft+'px',
						'width': $this[0].offsetWidth+'px',
						'height': '10px',
						'background-color': '#333',
						'opacity': '0',
						'z-index': 100,
						'border-radius':'25%',
					}
				});
				$('<span/>', {
					html: "<i class='fa fa-spinner fa-spin fa-2x fa-fw'></i><br/>"+_t('LOADING...')
				}).appendTo($div);
				$shadow.appendTo('body');
				$shadow.animate({
					'opacity':'0.5', 
					'border-radius':'0%', 
					'height': $this[0].offsetHeight+'px',
				});
				$div.appendTo('body');
				$div.css({
			    	'left': ((offLeft+$this[0].offsetWidth/2)-$div.width()/2)+'px', 
			    	'top': ((offTop+$this[0].offsetHeight/2)-$div.height()/2)+'px',
				});
			}, '250', $('#eiqui-ajax'));
			
			$.post(url, params, function(data){
				clearTimeout(AloxaEiqui.loadTimeout);
				var $this = $('#eiqui-ajax');
				$this.html(data);
				$this.css({'visibility':'initial'});
				$this.animate({'padding': 0, 'opacity':'1.0'}, 'fast');
				$('#load_ajax_info').remove();
				$('#load_ajax_shadow').animate({
					'opacity':0, 
					'border-radius':'25%', 
					'height': 0,
				}, 'fast', function(){ $(this).remove(); });
				callback(data);
			});
		},
		
		jsonRPC: function(url, params, callback) {
			ajax.jsonRpc(url, 'call', params).then(callback);
		}
	};
	
	return AloxaEiqui.init();
});