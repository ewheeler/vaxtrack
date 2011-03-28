$(document).ready(function(){
    var saved_history = window.history;

    /*	default chart options, vax, and country */
    var options = new Array("B","F","P");
    var vaccine = "BCG";
    var country = "ML";
    var chart_name = "";
    var lang;

    /*	dictionary for jsi18n strings */
    var strings = {};

    /* 	strings for stats jsi18n */
    strings["est_daily_cons_txt"] = gettext("est. daily cons.");
    strings["est_daily_cons_tip"] = gettext("Estimated daily consumption based on annual demand provided in UNICEF forecasts");

    strings["days_of_stock_txt"] = gettext("days of stock");
    strings["days_of_stock_tip"] = gettext("Number of days worth of doses currently in stock based on est daily cons");

    strings["percent_coverage_txt"] = gettext("coverage of annual need");
    strings["percent_coverage_tip"] = gettext("Percent coverage of annual need delivered to date, based on stock at beginning of year plus deliveries and forecasted annual demand");

    strings["doses_delivered_this_year_txt"] = gettext("doses delivered this year");
    strings["doses_delivered_this_year_tip"] = gettext("Total doses delivered this year to date");

    strings["doses_on_orders_txt"] = gettext("doses on order");
    strings["doses_on_orders_tip"] = gettext("Total number of doses to be delivered on any purchased orders.");

    strings["reference_date_txt"] = gettext("reference date");
    strings["reference_date_tip"] = gettext("Reference date that is the basis for chart, alerts, and statistical analysis.");

    strings["analyzed_txt"] = gettext("analysis date");
    strings["analyzed_tip"] = gettext("Date statistical analysis was performed.");

    /* strings for hist jsi18n */
    strings["historical_note_txt"] = gettext("Note: first and last year totals may not reflect full 12 months");

    strings["consumed_in_year_txt"] = gettext("total consumed");
    strings["consumed_in_year_tip"] = gettext("Total number of doses issued from national store.");

    strings["annual_demand_txt"] = gettext("annual demand");
    strings["annual_demand_tip"] = gettext("Annual demand as estimated in UNICEF forecasts.");

    strings["actual_cons_rate_txt"] = gettext("actual daily cons. rate");
    strings["actual_cons_rate_tip"] = gettext("Average daily consumption rate, based on total consumption during number of days included in stocklevel datapoints.");

    strings["three_by_year_txt"] = gettext("buffer stock level");
    strings["three_by_year_tip"] = gettext("Three month buffer stock level, based on annual demand.");

    strings["nine_by_year_txt"] = gettext("overstock level");
    strings["nine_by_year_tip"] = gettext("Nine month overstock level, based on annual demand.");

    strings["days_of_stock_data_txt"] = gettext("number of days");
    strings["days_of_stock_data_tip"] = gettext("Number of days included between the first stock level datapoint of the year and the last stock level datapoint of the year");

    /*	set inputs to values of global variables */
    $("#plot_options :input").val(options);
    $("#vaccines :input").val(vaccine);
    $("#country").val(country);

    /*	set lang global variable to selected lang
    (which is decided by django i18n based on
    browser's default lang or django cookie) */
    lang = $("#auth select").val();

    /*	update url hash, fetch chart & tables based on globals */
    update_url();
    get_chart();
    get_alerts();
    get_stats();


    /* 	whenever url hash is changed, update global variables
	to reflect these changes, and set inputs accordingly */
    $(window).bind("hashchange",  function(event){
	var hash_parts = new Array();
	hash_parts = document.location.hash.split('/');
	lang = hash_parts[1];
	country = hash_parts[2].replace(/[\#\-\!]/g,"");
	vaccine = hash_parts[3];
	options = new Array();
	for (i=0; i< hash_parts[4].length; i++){
	    options.push(hash_parts[4].charAt(i));
	}
	$("#plot_options :input").val(options);
	$("#vaccines :input").val(vaccine);
	$("#country").val(country);
	$("#auth select").val(lang);
    });


    /* 	whenever language dropdown is changed,
	set global lang to new language,
	update url hash, fetch new chart & tables */
    $("#auth select").change(function(){
	lang = $("#auth select").val();
	update_url();
        get_chart();
	get_alerts();
	get_stats();
    });

    /* 	whenever a plot option checkbox is clicked,
	reset global options to currently checked
	options, update url hash, and fetch new chart */
    $("#plot_options :input").click(function(){
        options = new Array();
	$("#plot_options :input:checked").each(function() {
	    options.push( $(this).val() );
	});
	update_url();
        get_chart();
    });

    /* 	whenever a vaccine radio button is clicked,
	reset global vaccine variable to currently checked
	vaccine, update url hash, fetch new chart and tables */
    $("#vaccines :input").click(function(){
        vaccine = ""; 
	$("#vaccines :input:radio:checked").each(function() {
	    vaccine = $(this).val();
	});
	update_url();
        get_chart();
	get_alerts();
	get_stats();
    });

    /* 	whenever country dropdown is changed,
	reset global country variable to current selection,
	update url hash, fetch new chart and tables */
    $("#country").change(function(){
        country = "";
	country = $(this).val();
	update_url();
        get_chart();
	get_alerts();
	get_stats();
    });


    /*	alter url hash to reflect current values of global variables */
    function update_url(){
	chart_opts = options.sort().join("");
        vaccine = vaccine.replace(/-/g, "_");
    	var path;
	path = "#!/" + lang + "/" + country + "/" + vaccine + "/" + chart_opts;
	document.location.hash = path;
    };

    /* 	fetch url for appropriate chart (based on current globals)
	and country flag */
    function get_chart(){
	chart_opts = options.sort().join("");
        vaccine = vaccine.replace(/-/g, "_");
        chart_name = country + "/" + vaccine + "/" + chart_opts + ".png";
        $("#chart").attr('src', "/charts/" + chart_name);
        $("#flag").attr('src', "/assets/icons/bandiere/" + country.toLowerCase() + ".gif");
    };

    /* 	fetch alerts for current country/vax and build table rows if needed */
    function get_alerts(){
	$.get("/alerts/" + country + "/" + vaccine, function (data){
		$("#alerts li").remove();
		var alerts;
		alerts = jQuery.parseJSON(data);
		if (alerts==null){
			$("#module-info").hide();
		} else {
			$("#module-info").show();
		};
		for (a in alerts){
			$("#alerts").append("<li class='" + alerts[a].status + "'>" + alerts[a].text + "</li>");
		};
	});
    };

    /* 	fetch stats and historical info for current country/vax
	and build table rows if needed */
    function get_stats(){
	$.get("/stats/" + country + "/" + vaccine, function (data){
		$("#stats tbody tr, #hist tbody tr").remove();
		var stats;
		stats = jQuery.parseJSON(data);
		if (stats==null){
			$("#module-stats, #module-hist").hide();
		} else {
			$("#module-stats, #module-hist").show();
		};
		for (s in stats){
			/* build a row for each of these variables */
			var stat_rows = ['est_daily_cons', 'days_of_stock', 'percent_coverage', 'doses_delivered_this_year', 'doses_on_orders', 'reference_date', 'analyzed'];
			for (row_index in stat_rows){
				var row_name = stat_rows[row_index];
				$("#stats > tbody:last").append("<tr class='tipoff' title='" + strings[row_name + "_tip"] + "'><td>" + strings[row_name + "_txt"] + ":</td><td>" + stats[s][row_name] + "</td></tr>");
			};

			/* build first row of hist table */
			var first_row = "<tr class='headings'><td class='note'><em>" + strings["historical_note_txt"] + "</em></td>";
			for (y in stats[s].years){
				first_row = first_row + "<td>" + stats[s].years[y] + "</td>";
			};
			$("#hist > tbody:last").append(first_row + "</tr>");

			/* build a row for each of these variables */
			var hist_rows = ['consumed_in_year', 'annual_demand', 'actual_cons_rate', 'three_by_year', 'nine_by_year', 'days_of_stock_data'];
			for (row_index in hist_rows){
				var row_name = hist_rows[row_index];
				var row;
				row = "<tr class='tipoff' title='" + strings[row_name + "_tip"] + "'><td>" + strings[row_name + "_txt"] + "</td>";
				for (y in stats[s].years){
					row = row + "<td>" + stats[s][row_name][y] + "</td>";
				};
				$("#hist > tbody:last").append(row + "</tr>");
			};
		};
	/* add tooltips at end of $.get callback */
	$(".tipoff").tooltip({opacity: 0.9});
	});
    };
});
