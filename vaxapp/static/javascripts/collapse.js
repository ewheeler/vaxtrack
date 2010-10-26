/* vim:set et ts=4 sw=4 */

jQuery(function() {

    /* allow module h3s with the 'collapsed' or 'expanded' classes to
     * collapse or expand the module. (see modules.css for more.) */
    jQuery("div.module.collapsed h3, div.module.expanded h3").each(function() {
        jQuery('<span class="toggler"></span>').click(function() {
            jQuery(this).parents("div.module").toggleClass("collapsed").toggleClass("expanded");
        }).appendTo(this);
    });
});


jQuery(function() {
    /* maximize the map, by hiding the two outer columns. */
    jQuery("div.toolbar .maximize").click(function() {
        jQuery(this).parents("div.two-columns").toggleClass("max-mod");
    });
});
