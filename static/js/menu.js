// Menú de la cabecera en pantallas angostas: un botón "Menú" lo abre y lo cierra.
// En pantallas anchas el CSS esconde el botón y el menú se ve siempre.
document.addEventListener('DOMContentLoaded', function () {
    var boton = document.getElementById('boton-menu');
    var menu = document.getElementById('cabecera-menu');
    if (!boton || !menu) return;

    function poner(abierto) {
        boton.setAttribute('aria-expanded', abierto ? 'true' : 'false');
        menu.classList.toggle('abierto', abierto);
    }

    boton.addEventListener('click', function () {
        poner(boton.getAttribute('aria-expanded') !== 'true');
    });

    // Escape cierra el menú y regresa el foco al botón
    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape' && boton.getAttribute('aria-expanded') === 'true') {
            poner(false);
            boton.focus();
        }
    });
});
