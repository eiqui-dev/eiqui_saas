/* Copyright (C) 2016 Solucións Aloxa S.L. <info@aloxa.eu> */
odoo.define('aloxa_eiqui.website', function (require) {
	'use strict';
	var ajax = require('web.ajax');
	var core = require('web.core');
	var _t = core._t;
	
	
	/** CLASE GENERAL EIQUI **/
	var AloxaEiqui = {
		loadTimeout: false,
		
		////////////////////////
		onLoad: function() {
			$(function(){AloxaEiqui.onPageLoad();});
		},
		
		onPageLoad: function(ev) {
			$('.select2-control').each(function(){ $(this).select2(); });
			
			$('.eiqui-message-item').each(function(i, elm){
				setTimeout(function(){
					$(elm).animate({'margin-top':0, 'opacity':'1.0'}, 'slow');
				}, 100*i);
			});
			$('.project-plan-url').animate({'margin-left': 0, 'opacity': '1.0'}, 800);
			
			var $eiqui = $('#eiqui-ajax');
			if ($eiqui.length) {
				var eiquiPage = $eiqui.data('page');
				if (eiquiPage == 'plan')
					AloxaEiquiPlan.onPageLoad();
				else if (eiquiPage == 'panel')
					AloxaEiquiPlanList.onPageLoad();
			}
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
				this.addAlert(_t('Oops! something is wrong :S'), data['errormsg']);
				return false;
			}
			return true;
		},
		
		////////////////////////
		loadEiquiAjax: function(url, params, callback)
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
			})
		}
		
	};

	/** CLASE PAGINA DETALLE PLAN **/
	var AloxaEiquiPlan = {
		onPageLoad: function() {
			var $eiqui = $('#eiqui-ajax');
			var project_id = $eiqui.data('project');
			$('#project-plan-menu a').on('click', function(ev){
				var $this = $(this);
				var section = $this.data('section');
				AloxaEiquiPlan.loadPanelSection(project_id, section);
				ev.preventDefault();
			});
			
			var anchor = undefined;
			if (window.location.href.indexOf("#") != -1)
				anchor = window.location.href.substring(window.location.href.indexOf("#")+1);
			AloxaEiquiPlan.loadPanelSection(project_id, anchor);
		},
		
		////////////////////////
		loadSubpageModulesApps: function()
		{
			var project_id = $('#eiqui-ajax').data('project');
			$('#modules-pagination a').on('click', function(ev){
				var $this = $(this);
				if (!$this.parent().hasClass('disabled'))
				{
					var npag = $this.data('page');
					var text = $('#search').val();
					var filter = $('#menu_modules_filter li.active').data('filter');
					AloxaEiquiPlan.loadPanelSection(project_id, 'modules_apps', '/'+npag+'?search='+encodeURIComponent(text)+'&module_filter='+encodeURIComponent(filter));
				}
				ev.preventDefault();
			});
			
			$('#search-modules').on('submit', function(ev){
				var text = $('#search').val();
				var filter = $('#menu_modules_filter li.active').data('filter');
				AloxaEiquiPlan.loadPanelSection(project_id, 'modules_apps', '?search='+encodeURIComponent(text)+'&module_filter='+encodeURIComponent(filter));
				ev.preventDefault();
			});
			
			$('#search-modules .a-submit').on('click', function(ev){
				$('#search-modules').submit();
				ev.preventDefault();
			});
			
			$('#menu_modules_filter a').on('click', function(ev){
				var $this = $(this);
				$('#menu_modules_filter li.active').removeClass('active');
				$this.parent().addClass('active');
				$('#search-modules').submit();
				ev.preventDefault();
			});
		},
		
		loadPanelSection: function(project_id, section, payload) {
			if (!section || section.length == 0)
				section = 'charts';
			var url = '/panel/plan/'+project_id+'/'+section;
			if (payload)
				url += payload;
			
			// Update menu highlighted item
			$('#project-plan-menu li[class="active"]').removeClass('active');
			$('#project-plan-menu li a[data-section="'+section+'"]').parent().addClass('active');
			
			AloxaEiqui.loadEiquiAjax(url, {}, function(data){
				// Initialize Tooltips
				//$(function () {
				//	$('[data-toggle="tooltip"]').tooltip();
				//});
				// Modules & APPs
				if (section === 'modules_apps')
					AloxaEiquiPlan.loadSubpageModulesApps();
				
				$(".disabled").click(function(event){
					event.preventDefault();
					return false;
				});
			});
		}
			
	};

	/** CLASE PAGINA LISTA DE PLANES **/
	var AloxaEiquiPlanList = {
		INTER_TIMERS: {},
			
		onPageLoad: function() {
			$('#search_plans').on('submit', function(ev){
				var search = $("#search").val();
				AloxaEiqui.loadEiquiAjax('/panel/search', {search:search}, function(data){
					$(".disabled").click(function(event) {
						event.preventDefault();
						return false;
					});
					
					// Create intervals
					for (var timer in AloxaEiquiPlanList.INTER_TIMERS)
						clearInterval(AloxaEiquiPlanList.INTER_TIMERS[timer]);
					$('#panel-projects tr').each(function(index, elm){
						var $this = $(elm);
						var server_state = $this.data('state');
						if (!server_state || server_state === 'created' || server_state === 'error')
							return true;
						var proj_id = $this.data('id');
						var name = $this.data('name');
						
						AloxaEiquiPlanList.INTER_TIMERS[proj_id]=setInterval(function($parent, proj_id, name){
							ajax.jsonRpc('/_get_plan_status', 'call', {id:proj_id}).then(function(data){
								if (!check_response(data))
									return;
								
								if (data['check'] && data['status'])
								{
									$parent.data('state', data['status']);
									if (data['status'] === 'created')
									{
										clearInterval(AloxaEiquiPlanList.INTER_TIMERS[proj_id]);
										delete AloxaEiquiPlanList.INTER_TIMERS[proj_id];
										$parent.children('td.project-status').html("<img src='https://"+name+".eiqui.com/logo.png' alt='"+name+"' class='img-responsive img-small pull-right' />");
										$parent.children('td.project-name').html("<a href='/panel/plan/"+proj_id+"'>"+name+"</a>");
										$parent.children('td.project-options ul li').each(function(i, e){ 
											$(e).removeClass('disabled'); 
										});
										$parent.removeClass('bg-warning bg-danger');
									}
									else if (data['status'] === 'error')
									{
										clearInterval(AloxaEiquiPlanList.INTER_TIMERS[proj_id]);
										delete AloxaEiquiPlanList.INTER_TIMERS[proj_id];
										$parent.children('td.project-status').html("<i class='fa fa-warning'></i> <strong>"+_t("Error!")+"</strong>");
										$parent.children('td.project-name').text(name);
										$parent.removeClass('bg-warning').addClass('bg-danger');
									}
								}
							});
						}, 60*1000, $this, proj_id, name);
					});
				});
				ev.preventDefault();
			});
			$('#search_plans .a-submit').on('click', function(ev){
				$('#search_plans').submit();
				ev.preventDefault();
			});
			
			$('#form_new_plan').validate({
				submitHandler: function(form) {
					$('#modal_new_plan').modal('hide');
					ajax.jsonRpc('/_create_plan', 'call', $(form).serializeObject()).then(function(data){
						if (!check_response(data))
							return;
						
						if (data['check'])
						{
							$('#search_plans #search').val("");
							$('#search_plans').submit();
							$(form)[0].reset();
						}
					});
				},    
			});
			
			$('#modal_new_plan .btn-primary').on('click', function(ev) {
				$('#form_new_plan').submit();
				ev.preventDefault();
			});
			
			$('#search_plans').submit();
		}
	};
	
	AloxaEiqui.onLoad();
});