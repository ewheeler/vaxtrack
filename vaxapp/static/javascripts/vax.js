$(document).ready(function(){
    var saved_history = window.history;

    var options = new Array("B","F","P");
    var vaccine = "BCG";
    var country = "ML";
    var chart_name = "";
    var lang;

    /* strings for jsi18n */
    var est_daily_cons_txt = gettext("est. daily cons.");
    var days_of_stock_txt = gettext("days of stock");
    var coverage_of_annual_need_txt = gettext("coverage of annual need");
    var doses_delivered_this_year_txt = gettext("doses delivered this year");
    var doses_on_order_txt = gettext("doses on order");
    var reference_date_txt = gettext("reference date");
    var analysis_date_txt = gettext("analysis date");

    var historical_note_txt = gettext("Note: first and last year totals may not reflect full 12 months");
    var total_consumed_txt = gettext("total consumed");
    var annual_demand_txt = gettext("annual demand");
    var actual_daily_cons_rate_txt = gettext("actual daily cons. rate");
    var buffer_stock_level_txt = gettext("buffer stock level");
    var overstock_level_txt = gettext("overstock level");

    $("#plot_options label[title]").tooltip();

    window.onhashchange = function(event){
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
	get_chart();
	get_alerts();
	get_stats();
	return false;
    }

    $("#plot_options :input").val(options);
    $("#vaccines :input").val(vaccine);
    $("#country").val(country);
    update_lang();
    get_chart();
    get_alerts();
    get_stats();
    update_url();

    $("#auth select").change(function(){
	update_lang();
    });

    $("#plot_options :input").click(function(){
        options = new Array();
	$("#plot_options :input:checked").each(function() {
	    options.push( $(this).val() );
	});
        get_chart();
	update_url();
    });

    $("#vaccines :input").click(function(){
        vaccine = ""; 
	$("#vaccines :input:radio:checked").each(function() {
	    vaccine = $(this).val();
	});
        get_chart();
	update_url();
    });

    $("#country").change(function(){
        country = "";
	country = $(this).val();
        get_chart();
	get_alerts();
	get_stats();
	update_url();
    });

    function update_lang(){
	$("#auth select option:selected").each(function(){
	    lang = "";
	    lang = $(this).val();
	});
	//$.post("/i18n/setlang/", {"language": lang});
	update_url();
    }

    function update_url(){
	chart_opts = options.sort().join("");
        vaccine = vaccine.replace(/-/g, "_");
    	var path;
	path = "#!/" + lang + "/" + country + "/" + vaccine + "/" + chart_opts
	//saved_history.pushState("", path, path)
	document.location.hash = path;
    }

    function get_chart(){
	chart_opts = options.sort().join("");
        vaccine = vaccine.replace(/-/g, "_");
        chart_name = country + "/" + vaccine + "/" + chart_opts + ".png";
        $("#chart").attr('src', "/charts/" + chart_name);
        $("#flag").attr('src', "/assets/icons/bandiere/" + country.toLowerCase() + ".gif");
    };

    function get_alerts(){
	$.get("/alerts/" + country + "/" + vaccine, function (data){
		$("#alerts li").remove();
		var alerts;
		alerts = jQuery.parseJSON(data);
		if (alerts==null){
			$("#module-info").hide();
		} else {
			$("#module-info").show();
		}
		for (a in alerts){
			$("#alerts").append("<li class='" + alerts[a].status + "'>" + alerts[a].text + "</li>");
		}
	});
    };

    function get_stats(){
	$.get("/stats/" + country + "/" + vaccine, function (data){
		$("#stats tbody tr").remove();
		$("#hist tbody tr").remove();
		var stats;
		stats = jQuery.parseJSON(data);
		if (stats==null){
			$("#module-stats").hide();
			$("#module-hist").hide();
		} else {
			$("#module-stats").show();
			$("#module-hist").show();
		}
		for (s in stats){
			$("#stats > tbody:last").append("<tr><td>" + est_daily_cons_txt + ":</td><td>" + stats[s].est_daily_cons + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + days_of_stock_txt + ":</td><td>" + stats[s].days_of_stock + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + coverage_of_annual_need_txt + ":</td><td>" + stats[s].percent_coverage + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + doses_delivered_this_year_txt + ":</td><td>" + stats[s].doses_delivered_this_year + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + doses_on_order_txt + ":</td><td>" + stats[s].doses_on_orders + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + reference_date_txt + ":</td><td>" + stats[s].reference_date + "</td></tr>");
			$("#stats > tbody:last").append("<tr><td>" + analysis_date_txt + ":</td><td>" + stats[s].analyzed + "</td></tr>");

			var first_row;
			first_row = "<tr><td style='font-size:.66em;'><em>" + historical_note_txt + "</em></td>"
			for (y in stats[s].years){
				first_row = first_row + "<td>" + stats[s].years[y] + "</td>"	
			}
			$("#hist > tbody:last").append(first_row + "</tr>")

			var consumed_in_year_row;
			consumed_in_year_row = "<tr><td>" + total_consumed_txt + "</td>"
			for (y in stats[s].years){
				consumed_in_year_row = consumed_in_year_row + "<td>" + stats[s].consumed_in_year[y] + "</td>"
			}
			$("#hist > tbody:last").append(consumed_in_year_row + "</tr>")

			var annual_demand;
			annual_demand = "<tr><td>" + annual_demand_txt + "</td>"
			for (y in stats[s].years){
				annual_demand = annual_demand + "<td>" + stats[s].annual_demand[y] + "</td>"
			}
			$("#hist > tbody:last").append(annual_demand + "</tr>")

			var actual_cons_rate;
			actual_cons_rate = "<tr><td>" + actual_daily_cons_rate_txt + "</td>"
			for (y in stats[s].years){
				actual_cons_rate = actual_cons_rate + "<td>" + stats[s].actual_cons_rate[y] + "</td>"
			}
			$("#hist > tbody:last").append(actual_cons_rate + "</tr>")

			var three_by_year;
			three_by_year = "<tr><td>" + buffer_stock_level_txt + "</td>"
			for (y in stats[s].years){
				three_by_year = three_by_year + "<td>" + stats[s].three_by_year[y] + "</td>"
			}
			$("#hist > tbody:last").append(three_by_year + "</tr>")

			var nine_by_year;
			nine_by_year = "<tr><td>" + overstock_level_txt + "</td>"
			for (y in stats[s].years){
				nine_by_year = nine_by_year + "<td>" + stats[s].nine_by_year[y] + "</td>"
			}
			$("#hist > tbody:last").append(nine_by_year + "</tr>")

			}
	});
    };
});
