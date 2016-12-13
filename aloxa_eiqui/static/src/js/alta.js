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
'use strict;'

jQuery(function($){	
  var Step = {
    INIT:0,
    USER_INFO:1,
    CONTACT_INFO:2,
    WAIT:3,
    FINISH:4,
  };
	
  /*
   * CAROUSEL
   */
  var $signupCarousel = $('#carousel-signup');
  $signupCarousel.carousel({ interval: false, keyboard: false, wrap: false });
	
  /*
   * PAGE VALIDATIONS
   */
  function next_step_01()
  {
	var $editDomain = $('#domain');
	var $editDomainContainer = $('#edit-domain-container');
	
	// Check for empty data
	if (!check_empty_controls(['#domain']))
		return;
	
	// Check valid domain
	var re = /^[a-zA-Z0-9-_]+$/;
	if (!re.test($editDomain.val()))
	{
		set_form_error('#domain', _t('This not appear to be a valid domain :/'));
		return;
	}
	
	// Check if domain is free
	if (!$('#next_step_01 i').hasClass('fa-spin'))
	{
		$('#next_step_01 i').removeClass('fa-arrow-right').addClass('fa-cog fa-spin');
		openerp.jsonRpc('/_check_domain_status', 'call', { domain:$editDomain.val() }).then(function(data){
			if (!check_response(data))
				return;
			
			if (data['check'])
			{
				$('#domain-str').text($('#domain').val()+'.eiqui.com');
				$('#email-str').text($('#domain').val()+'@eiqui.com');
				go_to_step(Step.USER_INFO);
			}
			else
				set_form_error('#domain', _t('Domain in use :('));
			
			$("#next_step_01 i").addClass('fa-arrow-right').removeClass('fa-cog fa-spin');
		});
  	}
  }
  
  function next_step_02()
  {
	var $editEmail = $('#email');
	var $editPass = $('#password');
	var $editRePass = $('#repassword');
	
	// Check for empty data
	if (!check_empty_controls(['#email','#password','#repassword']))
		return;
	
	// Check Valid Email
	var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
	if (!re.test($editEmail.val()))
	{
		set_form_error('#email', _t('This not appear to be a valid email :/'));
		return;
	}
	
	// Check Password
	if ($editPass.val() !== $editRePass.val())
	{
		set_form_error('#repassword', _t("Password don't match!"));
		return;
	}
	
	// Check if email is free
	if (!$('#next_step_02 i').hasClass('fa-spin'))
	{
		$('#next_step_02 i').removeClass('fa-arrow-right').addClass('fa-cog fa-spin');
		openerp.jsonRpc('/_check_email_status', 'call', { email:$editEmail.val() }).then(function(data){
			if (!check_response(data))
				return;
			
			if (data['check'])
				go_to_step(Step.CONTACT_INFO);
			else
				set_form_error('#email', _t('Email in use :('));
			
			$("#next_step_02 i").addClass('fa-arrow-right').removeClass('fa-cog fa-spin');
		});
	}
  }
  
  function next_step_03()
  {  	
	// Check for empty data
	if (!check_empty_controls(['#name', '#phone', '#country', '#city', '#street', '#zip']))
		return;
	
	// Create User
	if (!$('#next_step_03 i').hasClass('fa-spin'))
	{
		$('#next_step_03 i').removeClass('fa-arrow-right').addClass('fa-cog fa-spin');
		openerp.jsonRpc('/_create_user', 'call', $('#newaccount').serializeObject()).then(function(data){
			if (!check_response(data))
			{
				go_to_step(Step.INIT);
				return false;
			}
			
			if (!data['check'])
				add_alert("Account creation error", _t('Unespected error while creating account... :S'));
			else
				go_to_step(Step.FINISH);
			
			$("#next_step_03 i").addClass('fa-arrow-right').removeClass('fa-cog fa-spin');
		});
	}
  }
  
  /*
   * UTILS
   */
  function check_empty_controls(formElms)
  {
	for (var i in formElms)
	{
		var $elm = $(formElms[i]);
		if (!$elm.val() || $elm.val() === "" || 
			($elm.is("select") && (!$elm.find(':selected').val() || $elm.find(':selected').val() === "")))
		{
			set_form_error(formElms[i], _t("Can't be empty"));
			return false;
		}
	}
	
	return true;
  }
  
  var SIGNUP_STEP = 0;
  function go_to_step(step, callback)
  {
	var leftPer = ['-100%', '100%'];
	if (step < SIGNUP_STEP)
		leftPer = ['100%', '-100%'];
	
	$('.panel-eiqui').animate({ left: leftPer[0], opacity: 0 }, function(){
		$signupCarousel.carousel(step);
		$('.panel-eiqui').css({ left: leftPer[1] });
		$('.panel-eiqui').animate({ left: '0%', opacity: 1.0 });
		SIGNUP_STEP = step;
		
		$('#next_step_0'+step).focus();
		
		if (callback && typeof(callback) === "function")
		{
			callback();
			callback = undefined;
		}
	});
  }
  
  function set_form_error(elm, msg)
  {
	var $edit = $(elm);
	$edit.addClass('highlightred');
	$edit.tooltip({ trigger:'manual', placement:'bottom', title: msg });
	$edit.tooltip('show');
	$edit.focus();
	return;
  }
  function remove_form_error(elm)
  {
	  var $this = $(elm);
	  if ($this.hasClass('highlightred'))
	  {
		  $this.tooltip('hide').tooltip('destroy');
		  $this.removeClass('highlightred');
	  }
  }
 
  function refresh_states()
  {
	openerp.jsonRpc('/_get_states', 'call', { 'id': $('#country').find(":selected").val() }).then(function(data){
		if (!check_response(data))
			return false;
		
		var html = "<option value=''>"+_t('State...')+"</option>";
		for (var i in data['states'])
			html += "<option value='"+data['states'][i][0]+"'>"+data['states'][i][1]+"</option>";
		$('#state').html(html);
		
		if ($STATE_ID !== '')
			$('#state').val($STATE_ID).trigger('change');
	});
  }
  
  var $STATE_ID = '';
  function auto_complete_address()
  {
	  var sel_zip = $('#zip').val();
	  if (sel_zip === '')
	  {
		  $STATE_ID = '';
		  return;
  	  }
	  
	  openerp.jsonRpc('/_get_bzip', 'call', { 'zip': sel_zip }).then(function(data){
			if (!check_response(data))
				return false;
			
			if (data['bzip'] && data['bzip'][0] != false)
			{
				$('#country').val(data['bzip'][3]).trigger('change');
				$('#city').val(data['bzip'][4]);
				$STATE_ID = data['bzip'][2];
			}
		});  
  }
  
  /*
   * EVENTS
   */
  $(document).on('click', '.btn-prev-step', function() { go_to_step(SIGNUP_STEP-1); });
  
  $(document).on('click', '#next_step_01', function() { next_step_01(); });
  $(document).on('click', '#next_step_02', function() { next_step_02(); });
  $(document).on('click', '#next_step_03', function() { next_step_03(); });
  
  $(document).on('change', '#country', function() { refresh_states(); });
  
  $(document).on('blur', '#zip', function() { auto_complete_address(); });
  
  $(document).on('keypress', "input[type='text'],input[type='password']", function(){ remove_form_error(this); });
  $(document).on('change', "select", function(){ remove_form_error(this); });
  
  /*
   * INITIALIZATIONS
   */
  refresh_states();
  auto_complete_address();
});