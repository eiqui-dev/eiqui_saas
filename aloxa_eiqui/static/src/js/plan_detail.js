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
odoo.define('aloxa_eiqui.plan_detail', function (require) {
	'use strict';
	var eiqui = require('aloxa_eiqui.main');
	

	/** PAGINA DETALLE PLAN **/
	var AloxaEiquiPlan = {
		init: function() {
			jQuery(function($){AloxaEiquiPlan.onPageLoad($);});
		},
		
		////////////////////////
		onPageLoad: function($) {
			var $eiqui = $('#eiqui-ajax');
			
			$('.project-plan-url').animate({'margin-left': 0, 'opacity': '1.0'}, 800);
			
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
			
			eiqui.loadAjax(url, {}, function(data){
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
	
	return AloxaEiquiPlan.init();
});