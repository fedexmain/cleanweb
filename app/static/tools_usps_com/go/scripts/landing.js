var trackingApp = {};
$(document).ready(function(e) {

	/** Click Handlers for accordion buttons **/
	$('.collapser').on('click', function(e) {
		e.preventDefault();
		$('.panel-collapse').each(function(i, obj){
			if($(this).hasClass('in')){
				$(this).collapse('toggle');
			}
		})
		var collapse_element = $(this).next();
		collapse_element.collapse('toggle');
	});
	
	/** Validate input for tracking when pasted **/
    $(':text,textarea').on('touchstart input paste blur', adjustHeight);
	
	function packageCheck()
		{
			var trackingcomma = $('#tracking-input').val().replace(/ /g, '').replace(/\n/g,',').split(',');
		
			var trackingLength = trackingcomma.length;
		
			var redeliveryNumbers = 0;
		
			trackingcomma.forEach(function(tn){
				if(tn.length === 16 && tn.substr(0,2) === '52')
				{	
					redeliveryNumbers++;
				}
			
			});
		
		if(redeliveryNumbers > 1)
		{
			return true;
		}
		else if(trackingLength > 35)
		{
			return true;
		}
		else {return false;}
		
		}

	/*
	
		A/B Testing Cookie
	 */


	
	/** Track labels **/
	// deferred object for tracking
	var deferred = $.Deferred();
	 
	// Add handlers to be called when deferred is resolved
	deferred.done(checkKeyboardState, adjustHeight, submitForm);
	  
	// Resolve the Deferred object when the button is clicked
	$(".tracking-btn").on( "click", function() {
		var hasErrors = $('#trackPackage').validator('validate').has('.has-error').length;
		var packageConstraints = packageCheck();
		if (!hasErrors && !packageConstraints) {
			deferred.resolve();
		}
	});
	
	// 2023-01 Update the Validator
	$('#trackPackage').validator({
  custom: {
    redelivery: function ($el) {
      if(packageCheck()){
        return "Please enter 1 redelivery number";
      }
      else {
        return false;
      }
    }


  },
  errors: {
    redelivery: "Please enter 1 redelivery number"
  }
});

	/** Show/hide the red underline when active **/
	$('.panel').on('shown.bs.collapse', function(){
		$(this).find('.down-arr, .up-arr').toggleClass("down-arr up-arr");
		$(this).find('.panel-word').toggleClass("red-underline");
	})

	$('.panel').on('hidden.bs.collapse', function(){
		$(this).find('.down-arr, .up-arr').toggleClass("down-arr up-arr");
		$(this).find('.panel-word').toggleClass("red-underline");
	});
	
	
	
	// Informed Delivery 2019 - Cross Sell Check
	trackingApp.isIDready = false;
	
	let idAskSession = sessionStorage.getItem('idCrossSellAsk');
	
	if(idAskSession == "YES")
		{
			trackingApp.isIDready = true;
		}
	
	// Check Methods
	idXSCheck();
	idXSLoggedIn();

	$('#trackPackage').validator();
	$('#trackPackage').validator('update');
	
	
	
	function idCrossSell() {
		
    	$('#track-package-modal').modal('show');
		$('#track-package-modal').modal({backdrop: 'static', keyboard: false})
		
		sessionStorage.setItem('idCrossSellAsk', 'YES');
		dataLayer.push({ 
			  'event': 'application',
			  'application': {
			    'element': 'IDXS Prompt',
				'userAction': 'impression'
			  }
			});
			
	}
	
	$("#faqHeader").on('click', function(){
		
		$('#trackPackage').validator('update');

		if(trackingApp.isIDready == false)
			{
				trackingApp.isIDready = true;
				trackingApp.clickedFAQ = true;
				trackingApp.crossSellURLREF = trackingApp.crossSellURL.replace("CHANGEMEHERE","faqHeader");
				idCrossSell();
			}
		else
			{
				window.open("https://faq.usps.com/s/article/Where-is-my-package", "_blank");
			}
		
	});
	$("#idxsFAQBtn").on('click', function(){
		
		$('#trackPackage').validator('update');

		if(trackingApp.isIDready == false)
			{
				trackingApp.isIDready = true;
				trackingApp.clickedFAQ = true;
				trackingApp.crossSellURLREF = trackingApp.crossSellURL.replace("CHANGEMEHERE","faqButton");
				idCrossSell();
			}
		else
			{
				window.open("https://faq.usps.com/s/article/Where-is-my-package", "_blank");
			}
		
	});
	
	// Display modal sign-up message after selecting the "Yes" radio button. 
	$("input:radio[name='track-package-rb']").change(function() {
		if ($('#trackradio1').is(':checked')) {
			$('.signup-txt').show();
			$('.error-message').hide();
		} else if ($('#trackradio2').is(':checked')) {
			$('.signup-txt').hide();
			$('.error-message').hide();
		}
    });
	
	
	// Display error message in modal if none of the options have been selected.
	$('.submit-btn').click(function() {
		if ($("input[name='track-package-rb']:checked").val()) {
			$('#track-package-modal').modal('hide');
			if($('#trackradio1').is(':checked'))
			{
			dataLayer.push({ 
				  'event': 'application',
				  'application': {
				    'element': 'IDXS Prompt',
					'userAction': 'interaction',
				    'selectedCheckbox' : 'Yes'
				  }
				});

				window.open(trackingApp.crossSellURLREF, "_blank");
			}
		if($('#trackradio2').is(':checked'))
		{
			updateIDXSRecord();
		dataLayer.push({ 
			  'event': 'application',
			  'application': {
			    'element': 'IDXS Prompt',
				'userAction': 'interaction',
			    'selectedCheckbox' : 'No'
			  }
			});
		}
			if(trackingApp.clickedFAQ == true){
				window.open("https://faq.usps.com/s/article/Where-is-my-package", "_self");
				trackingApp.clickedFAQ = false;
			}
			if(trackingApp.clickedClose == true)
				{

				$('.tracking-group').hide();
				$('.tracking_form_container h3').removeClass('open');
				if ($('.tracking-group').css('display') != 'none') {
					$('.track-another-package-close').show();
				} else if ($('.tracking-group').css('display') == 'none') {
					$('.track-another-package-close').hide();
				}
				trackingApp.clickedClose = false;
				}
			if(trackingApp.clickedRemove == true)
				{
				trackingApp.clickedRemove = false;
				}
		} else {
			$('.error-message').show();
		}
	});

});

	/** Adjust textarea height **/
    function adjustHeight() {
		//console.log("adjustHeight");
		$('textarea').each(function () {
		  this.setAttribute('style', 'height:' + (this.scrollHeight) + 'px;overflow-y:hidden;');
		}).on('touchstart touchend input paste', function () {
		  this.style.height = 'auto';
		  this.style.height = (this.scrollHeight) + 'px';
		});
	};

	/** check keyboard state **/
	function checkKeyboardState() {
		//console.log("checkKeyboardState");
		if($(document.activeElement).attr('type') === "text"){
			//console.log("Keyboard visible");
			// hide keyboard
			document.activeElement.blur();
		}else{
			//console.log("Keyboard not visible");  
		}
	};

	/** submit form **/
	/** Track labels **/
	function submitForm() {
		
		var getTLang = "false";
		
		$.each(dataLayer, function(dli, dld){
		if(dld.event == "trackingmanageAB_test")
		{
			if(dld.test_language == "true")
			{
				getTLang = "true";	
			}
		}
		
		});
		var tLabels = $('#tracking-input').val().replace(/ /g,'').split('\n')+',',
			tlCount = tLabels.split(',').length,
			tRef = $("input[id=tRef]").val();
			//console.log(tLabels);
		$("input[id=tLc]").val(tlCount);
		$("input[id=tABt]").val(getTLang);
		$("input[id=tLabels]").val(tLabels);/**/
		//console.log(tLabels + " Sent");
		$("#trackPackage").submit();
		//console.log(tLabels + " Submitted");
	};
	
	
	
	// Informed Delivery Cross Sell 2019
	// idxsSignedUp
	function idXSLoggedIn()
	{
	    jQuery.ajax({
	        url: "/UspsToolsRestServices/rest/idCrossSell/secure/idxsSignedUp",
	        type: "GET",
	        cache: false,
	        headers: {
	            "Content-Type": "application/json;charset=utf-8"
	        },
	        dataType: "json",
	        success: function (resp) {
	        	
	        	var idEnrolled = resp.IDEnrolled;
	        	
	        	var isLoggedInUser = resp.ValidLoginSession;
	        	trackingApp.isIDRegUser = isLoggedInUser;
	        	if(idEnrolled)
				{
					var isEligible = idEnrolled.IDAddressEligible;
					var hasBeenAsked = idEnrolled.IDHasBeenAsked;
					var isAccountIDEleg = idEnrolled.IDEligible;
	        		var isUserInID = idEnrolled.IDGroup;
				}
				
	        	var accountType = resp.AccountType;
	        	
	        	if(isEligible == "false" || hasBeenAsked == "Y" || accountType == "BUSINESS" || isAccountIDEleg == "N" || isUserInID == "GRANT")
	        		{
	        			trackingApp.isIDready = true;
	        		}

	        },
	        error: function (jqXHR, exception) {
	        	console.log("ERROR: ID Cross Sell - Defaulting to OFF")
	        }
	    });
	}
	
	function updateIDXSRecord()
	{
		if(trackingApp.isIDRegUser)
			{
		    jQuery.ajax({
		        url: "/UspsToolsRestServices/rest/idCrossSell/updateIDStatus",
		        type: "GET",
		        cache: false,
		        headers: {
		            "Content-Type": "application/json;charset=utf-8"
		        },
		        dataType: "json",
		        success: function (resp) {
		        },
		        error: function (jqXHR, exception) {
		        }
		    });
			}
	}
	
	function idXSCheck()
	{
	    jQuery.ajax({
	        url: "/UspsToolsRestServices/rest/idCrossSell/getIDStatus",
	        type: "GET",
	        cache: false,
	        headers: {
	            "Content-Type": "application/json;charset=utf-8"
	        },
	        dataType: "json",
	        success: function (resp) {
	        	
	        	if(resp.status == "false"){
	        		
	        		trackingApp.isIDready = true;
	        	}
	        	else {
	        		trackingApp.isIDready = false;
	        	}
	        	
	        	let idAskSession = sessionStorage.getItem('idCrossSellAsk');
	        	
	        	if(idAskSession == "YES")
	        		{
	        			trackingApp.isIDready = true;
	        		}

	        	trackingApp.crossSellURL = resp.crossSellURL;
				trackingApp.crossSellURLREF = trackingApp.crossSellURL.replace("CHANGEMEHERE","homepageBanner");
				
				var bannerURL = trackingApp.crossSellURL.replace("CHANGEMEHERE","homepageBanner");
				$("#crossSellBanner").prop("href", bannerURL);
	        	
	        },
	        error: function (jqXHR, exception) {
	        	console.log("ERROR: ID Cross Sell - Defaulting to OFF");
	        	trackingApp.isIDready = true;
	        }
	    });
	}	
	
