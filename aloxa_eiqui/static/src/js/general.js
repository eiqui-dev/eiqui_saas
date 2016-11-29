/* Copyright (C) 2016 Solucións Aloxa S.L. <info@aloxa.eu> */
"use strict;"

/*
 * GENERAL
 */
var _t = openerp._t;

function add_alert(title, msg)
{
	var html = "<div class='alert alert-danger alert-dismissible fade in' role='alert' id='alert'>"+
				"<button type='button' class='close' data-dismiss='alert' aria-label='"+_t('Close')+"'>"+
				"<span aria-hidden='true'>×</span>"+
				"</button>"+
				"<h4>"+title+"</h4>"+
				"<p>"+msg+"</p>"+
				"</div>";
	$('#alerts').prepend(html);
}

function check_response(data)
{
	if (data && data['error'])
	{
		add_alert(_t('Oops! something is wrong :S'), data['errormsg']);
		return false;
	}
	return true;
}

$(function(){
	$('.select2-control').each(function(){ $(this).select2(); });
	
	var loadTimeout = false;
	$(document).ajaxStart(function(){
		$('#eiqui-ajax').css({'padding':'15px'});
		loadTimeout = setTimeout(function($this){
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
	}).ajaxComplete(function(){
		clearTimeout(loadTimeout);
		var $this = $('#eiqui-ajax');
		$this.css({'visibility':'initial'});
		$this.animate({'padding': 0, 'opacity':'1.0'}, 'fast');
		$('#load_ajax_info').remove();
		$('#load_ajax_shadow').animate({
			'opacity':0, 
			'border-radius':'25%', 
			'height': 0,
		}, 'fast', function(){ $(this).remove(); });
	});
	
	$('.eiqui-message-item').each(function(i, elm){
		setTimeout(function(){
			$(elm).animate({'margin-top':0, 'opacity':'1.0'}, 'slow');
		}, 100*i);
	});
	$('.project-plan-url').animate({'margin-left': 0, 'opacity': '1.0'}, 800);
});


/*
 * PANEL - PLAN
 */
function load_panel_section(project_id, section, payload)
{
	if (!section || section.length == 0)
		section = 'charts';
	var url = '/panel/plan/'+project_id+'/'+section;
	if (payload)
		url += payload;
	
	// Update menu highlighted item
	$('#project-plan-menu li[class="active"]').removeClass('active');
	$('#project-plan-menu li a[data-section="'+section+'"]').parent().addClass('active');
	
	$.post(url, function(data){
		$('#eiqui-ajax').html(data);
		
		// Initialize Tooltips
		//$(function () {
		//	$('[data-toggle="tooltip"]').tooltip();
		//});
		// Modules & APPs
		if (section === 'modules_apps')
			load_subpage_modules_apps();
		
		$(".disabled").click(function(event){
			event.preventDefault();
			return false;
		});
	});
}

function load_subpage_modules_apps()
{
	var project_id = $('#eiqui-ajax').data('project');
	$('#modules-pagination a').on('click', function(ev){
		var $this = $(this);
		if (!$this.parent().hasClass('disabled'))
		{
			var npag = $this.data('page');
			var text = $('#search').val();
			var filter = $('#menu_modules_filter li.active').data('filter');
			load_panel_section(project_id, 'modules_apps', '/'+npag+'?search='+encodeURIComponent(text)+'&module_filter='+encodeURIComponent(filter));
		}
		ev.preventDefault();
	});
	
	$('#search-modules').on('submit', function(ev){
		var text = $('#search').val();
		var filter = $('#menu_modules_filter li.active').data('filter');
		load_panel_section(project_id, 'modules_apps', '?search='+encodeURIComponent(text)+'&module_filter='+encodeURIComponent(filter));
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
}

$(function(){
	var $eiqui = $('#eiqui-ajax');
	if ($eiqui.length && $eiqui.data('page') == 'plan')
	{
		var project_id = $eiqui.data('project');
		$('#project-plan-menu a').on('click', function(ev){
			var $this = $(this);
			var section = $this.data('section');
			load_panel_section(project_id, section);
			ev.preventDefault();
		});
		
		var anchor = undefined;
		if (window.location.href.indexOf("#") != -1)
			anchor = window.location.href.substring(window.location.href.indexOf("#")+1);
		load_panel_section(project_id, anchor);
	}
});


/*
 * PANEL - MAIN
 */
$(function(){
	var $eiqui = $('#eiqui-ajax');
	if ($eiqui.length && $eiqui.data('page') == 'panel')
	{
		$('#search_plans').on('submit', function(ev){
			var search = $("#search").val();
			$.post('/panel/search?search='+search, function(data){
				$('#eiqui-ajax').html(data);
				$(".disabled").click(function(event) {
					event.preventDefault();
					return false;
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
				openerp.jsonRpc('/_create_plan', 'call', $(form).serializeObject()).then(function(data){
					if (!check_response(data))
						return;
					
					if (data['check'])
					{
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
});