//funcionalidades comuns para o portal e sistemas externos.

function menuLateralPortal() {
	if ($(window).width() > 767) {
		$('.nav-submenu').hover(function () {
		if ($(this).find('.level-2').length > 0) {
		    $(this).find('.level-2').stop().slideDown('slow');
		}
		},function () {
		    if ($(this).find('.level-2').length > 0) {
		        $(this).find('.level-2').stop().slideUp('slow');
		    }
		});
	} else {
		$('.nav-submenu .seta-lateral').click(function(e){
			e.preventDefault();
			$(this).parent('a').siblings('.level-2').slideToggle();
		});
	}
}
