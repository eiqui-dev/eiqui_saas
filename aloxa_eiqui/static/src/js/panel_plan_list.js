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
odoo.define('aloxa_eiqui.plan_list', function(require) {
	'use strict';
	var eiqui = require('aloxa_eiqui.main');
	var _t = eiqui.getCoreBabel();
	
	/** PAGINA LISTA DE PLANES **/
	var AloxaEiquiPlanList = {
		INTER_TIMERS: {},
			
		////////////////////////
		init: function() {
			jQuery(function($){AloxaEiquiPlanList.onPageLoad($);});	
			return this;
		},
		
		////////////////////////
		onPageLoad: function($) {
			$('#search_plans').on('submit', function(ev) {
				var search = $("#search").val();
				eiqui.loadAjax('/panel/search', {search:search}, function(data) {
					$(".disabled").click(function(event) {
						event.preventDefault();
						return false;
					});
					
					// Create intervals
					for (var timer in AloxaEiquiPlanList.INTER_TIMERS)
						clearInterval(AloxaEiquiPlanList.INTER_TIMERS[timer]);
					$('#panel-projects tr').each(function(index, elm) {
						var $this = $(elm);
						var server_state = $this.data('state');
						if (!server_state || server_state === 'created' || server_state === 'error')
							return true;
						var proj_id = $this.data('id');
						var name = $this.data('name');
						
						AloxaEiquiPlanList.INTER_TIMERS[proj_id] = setInterval(function($parent, proj_id, name) {
							eiqui.jsonRPC('/_get_plan_status', {plan_id:proj_id}, function(data){
								if (!eiqui.checkResponse(data))
									return;
								
								if (data['check'] && data['status']) {
									$parent.data('state', data['status']);
									if (data['status'] === 'created') {
										clearInterval(AloxaEiquiPlanList.INTER_TIMERS[proj_id]);
										delete AloxaEiquiPlanList.INTER_TIMERS[proj_id];
										$parent.children('td.project-status').html("<img src='https://"+name+".eiqui.com/logo.png' alt='"+name+"' class='img-responsive img-small pull-right' />");
										$parent.children('td.project-name').html("<a href='/panel/plan/"+proj_id+"'>"+name+"</a>");
										$parent.children('td.project-options ul li').each(function(i, e){ 
											$(e).removeClass('disabled'); 
										});
										$parent.removeClass('bg-warning bg-danger');
									}
									else if (data['status'] === 'error') {
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
			
			$('#search_plans .a-submit').on('click', function(ev) {
				$('#search_plans').submit();
				ev.preventDefault();
			});
			
			$('#form_new_plan').validate({
				submitHandler: function(form) {
					$('#modal_new_plan').modal('hide');
					eiqui.jsonRPC('/_create_plan', $(form).serializeObject(), function(data) {
						if (!eiqui.checkResponse(data))
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
			
			$('.panel-menu li').on('click', function(ev) {
				var $elm = $(this);
				var preventDef = false;
				if ($elm.hasClass('menu-update-test')) {
					eiqui.jsonRPC('/_update_plan_test', '', function(){
						if (!eiqui.checkResponse(data))
							return;
						
					});
					preventDef = true;
				}
				if ($elm.hasClass('menu-create-security-copy')) {
					console.log("CREATE COPY!");
					preventDef = true;
				}
				if ($elm.hasClass('menu-restore-security-copy')) {
					console.log("RESTORE COPY!");
					preventDef = true;
				}
				
				if (preventDef)
					ev.preventDefault();
			});
			
			$('#search_plans').submit();
		}
	};
	
	return AloxaEiquiPlanList.init();
});