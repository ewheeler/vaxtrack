$(document).ready(function(){
    var saved_history = window.history;

    var options;
    var group;
    var country;
    var chart_name;
    var lang;
    var g;

    /* array of all possible chart options, used to check for plot visibility */
    var all_options = new Array("T", "N", "F", "P", "C", "U");
    /* map of plot options to position in csv file -- and dygraph visibility settings */
    var vis_map = {"T":1,"N":2, "F":3, "P":4, "C":5, "U":6};
    /* array of visibility settings used while initializing dygraphs,
        by default, show stock level, buffer stock, and overstock plots */
    var vis_bools = new Array(true, true, true, false, false, false, false);

    if (document.location.hash == ""){
        /* default chart options, vax, and country */
        options = new Array("T", "N", "F", "P");
        group = "bcg";
	country = "ML";
	chart_name = "";
    } else {
	update_from_hash();
    };

    function update_from_hash(){
	var hash_parts = new Array();
	hash_parts = document.location.hash.split('/');
	lang = hash_parts[1];
	country = hash_parts[2].replace(/[\#\-\!]/g,"");
	group = hash_parts[3];
	options = new Array();
	/* clean slate of chart options with only stock levels visible */
	vis_bools = new Array(true, false, false, false, false, false, false);
	for ( var i=0; i< hash_parts[4].length; i++){
	    options.push(hash_parts[4].charAt(i));
	    vis_bools[vis_map[hash_parts[4].charAt(i)]] = true;
	}
	$("#plot_options :input").val(options);
        $("#checkbox-S").attr("checked", "checked");
	$("#vaccines :input").attr("checked", false);
	$("#vaccines :input").filter("[value=" + group + "]").attr("checked", "checked");
	$("#country").val(country);
	$("#auth select").val(lang);
    };

    /* 	whenever url hash is changed, update global variables
	to reflect these changes, and set inputs accordingly */
    $(window).bind("hashchange",  function(event){
    	update_from_hash();
    });

    /*	dictionary for jsi18n strings */
    var strings = {};

    /* 	strings for stats jsi18n */
    strings["est_daily_cons_txt"] = gettext("estimated daily consumption");
    strings["est_daily_cons_tip"] = gettext("Estimated daily consumption based on annual demand provided in UNICEF forecasts");

    strings["days_of_stock_txt"] = gettext("days of stock");
    strings["days_of_stock_tip"] = gettext("Number of days worth of doses currently in stock based on est daily cons");

    strings["percent_coverage_txt"] = gettext("coverage of annual need");
    strings["percent_coverage_tip"] = gettext("Percent coverage of annual need delivered to date, based on stock at beginning of year plus deliveries and forecasted annual demand");

    strings["doses_delivered_this_year_txt"] = gettext("doses delivered this year");
    strings["doses_delivered_this_year_tip"] = gettext("Total doses delivered this year to date");

    strings["doses_on_orders_txt"] = gettext("doses on order");
    strings["doses_on_orders_tip"] = gettext("Total number of doses to be delivered on any purchased orders.");

    strings["reference_date_txt"] = gettext("situation as of");
    strings["reference_date_tip"] = gettext("Reference date that is the basis for chart, alerts, and statistical analysis.");

    strings["analyzed_txt"] = gettext("analysis date");
    strings["analyzed_tip"] = gettext("Date statistical analysis was performed.");

    /* strings for hist jsi18n */
    strings["historical_note_txt"] = gettext("Note: first and last year totals may not reflect full 12 months");
    strings["trends_txt"] = gettext("Trend");

    strings["consumed_in_year_txt"] = gettext("usage (doses)");
    strings["consumed_in_year_tip"] = gettext("Total number of doses issued from national store.");

    strings["annual_demand_txt"] = gettext("annual demand (doses)");
    strings["annual_demand_tip"] = gettext("Annual demand as estimated in UNICEF forecasts.");

    strings["actual_cons_rate_txt"] = gettext("actual daily consumption rate");
    strings["actual_cons_rate_tip"] = gettext("Average daily consumption rate, based on total consumption during number of days included in stocklevel datapoints.");

    strings["three_by_year_txt"] = gettext("buffer stock level");
    strings["three_by_year_tip"] = gettext("Three month buffer stock level, based on annual demand.");

    strings["nine_by_year_txt"] = gettext("overstock level");
    strings["nine_by_year_tip"] = gettext("Nine month overstock level, based on annual demand.");

    strings["days_of_stock_data_txt"] = gettext("number of days with stocklevel information");
    strings["days_of_stock_data_tip"] = gettext("Number of days included between the first stock level datapoint of the year and the last stock level datapoint of the year");

    /*	set inputs to values of global variables */
    $("#plot_options :input").val(options);
    $("#checkbox-S").attr("checked", "checked");
    $("#vaccines :input:radio").filter("[value=" + group + "]").attr("checked", "checked");
    $("#country").val(country);

    /*	set lang global variable to selected lang
    (which is decided by django i18n based on
    browser's default lang or django cookie) */
    lang = $("#auth select").val();
    update_abbrs();

    /*	update url hash, fetch chart & tables based on globals */
    update_url();
    get_chart();
    get_alerts();
    get_stats();


    /* 	whenever language dropdown is changed,
	set global lang to new language,
	update url hash, fetch new chart & tables */
    $("#auth select").change(function(){
	lang = $("#auth select").val();
	update_abbrs();
	update_url();
        get_chart();
	get_alerts();
	get_stats();
    });

    function update_abbrs(){
	$("#vaccines label").each(function() {
	    var to_use = $(this).attr(lang);
	    $(this).text(to_use);
	});
    };

    /* 	whenever a plot option checkbox is clicked,
	reset global options to currently checked
	options, update url hash, and fetch new chart */
    $("#plot_options :input").click(function(){
        options = new Array();
	$("#plot_options :input:checked").each(function() {
	    options.push( $(this).val() );
	});
        $("#checkbox-S").attr("checked", "checked");
	update_url();
	set_vis();
    });

    /* 	whenever a vaccine radio button is clicked,
	reset global vaccine variable to currently checked
	vaccine, update url hash, fetch new chart and tables */
    $("#vaccines :input").click(function(){
        group = ""; 
	$("#vaccines :input:radio:checked").each(function() {
	    group = $(this).val();
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
    	var path;
	path = "#!/" + lang + "/" + country + "/" + group + "/" + chart_opts;
	document.location.hash = path;
    };

    /* 	fetch url for appropriate chart (based on current globals)
	and country flag */
    function get_chart(){
	$("#chart").html('');
	g = new Dygraph(document.getElementById("chart"),
		    "/assets/csv/" + country + "_" + group + "_all.csv",
		    {
			rollPeriod: 1,
			title: country + " " + group,
			ylabel: 'Doses',
			xlabel: 'Time',
			axisLabelFontSize: 10,
			labelsKMB: true,
			stacked: true,
			connectSeparatedPoints: true,
			gridLineColor: '#eee',
			visibility: vis_bools,
			labels: [ "Date", "Actual stock", "Buffer stock", "Overstock", "Forcasted orders (on forcast)", "Forecasted orders (on purchase)", "CO forecast", "CO forecast w/ deliveries" ],
			labelsSeparateLines: true,
			legend: "always",
			colors: ["blue", "red", "salmon", "purple", "cyan", "green", "orange"],
			labelsDiv: document.getElementById("legend"),
			labelsShowZeroValues: false,
			stepPlot: true,
			"Actual stock": {
			    stepPlot: true,
			    strokeWidth: 2
			},
			"Buffer stock": {
			    stepPlot: false,
			    strokeWidth: 1
			},
			"Overstock": {
			    stepPlot: false,
			    strokeWidth: 1
			},
			"Forecasted orders (on forcast)": {
			    stepPlot: false,
			    strokeWidth: 2
			},
			"Forecasted orders (on purchase)": {
			    stepPlot: false,
			    strokeWidth: 2
			},
			"CO forecast": {
			    stepPlot: false,
			    strokeWidth: 2
			},
			"CO forecast w/ deliveries": {
			    stepPlot: false,
			    strokeWidth: 2
			}
		    }); // options
        //`$("#flag").attr('src', "/assets/icons/bandiere/" + country.toLowerCase() + ".gif");
    };

    function set_vis(){
	for (n in all_options){
	    var opt = all_options[n]
	    if ($.inArray(opt, options) != -1){
		g.setVisibility(parseInt(vis_map[opt]),true);
	    } else {
		g.setVisibility(parseInt(vis_map[opt]),false);
	    };
	};
    };

    /* 	fetch alerts for current country/vax and build table rows if needed */
    function get_alerts(){
	$.get("/alerts/" + country + "/" + group, function (data){
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
	$.get("/stats/" + country + "/" + group, function (data){
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
				$("#stats > tbody:last").append("<tr class='tipoff' title='" + strings[row_name + "_tip"] + "'><td class='txt'>" + strings[row_name + "_txt"] + ":</td><td class='data'>" + stats[s][row_name] + "</td></tr>");
			};

			/* build first row of hist table */
			var first_row = "<tr class='headings'><td class='note'><em>" + strings["historical_note_txt"] + "</em></td><td class='spark'>" + strings["trends_txt"] + "</td>";
			for (y in stats[s].years){
				first_row = first_row + "<td>" + stats[s].years[y] + "</td>";
			};
			$("#hist > tbody:last").append(first_row + "</tr>");

			/* build a row for each of these variables */
			var hist_rows = ['consumed_in_year', 'annual_demand', 'three_by_year', 'nine_by_year', 'actual_cons_rate', 'days_of_stock_data'];
			for (row_index in hist_rows){
				var row_name = hist_rows[row_index];
				var row;
				var data = new Array();
				row = "<tr class='tipoff' title='" + strings[row_name + "_tip"] + "'><td class='txt'>" + strings[row_name + "_txt"] + "</td>";
				row = row + "<td class='spark' id='" + row_name + "'</td>";
				for (y in stats[s].years){
					row = row + "<td class='int data'>" + stats[s][row_name][y] + "</td>";
					data.push(stats[s][row_name][y]);
				};
				$("#hist > tbody:last").append(row + "</tr>");
				if (row_name != 'actual_cons_rate' & row_name != 'days_of_stock_data'){
				    var td_id = "#" + row_name;
				    $(td_id).sparkline(data, { type:'line', width:'8em', height:'2em', spotRadius:'0', chartRangeMin:'0', chartRangeMax:'1000000' });
				};
			};
		};
		$(".int").each(function(){
			$(this).text( $(this).text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,") );
		});
		/* add tooltips at end of $.get callback */
		$(".tipoff").tooltip({opacity: 0.9});
	});
    };
});
