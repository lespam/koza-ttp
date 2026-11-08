// Modo claro u oscuro. Se carga en <head> para aplicar el modo guardado antes de pintar.
(function () {
    var raiz = document.documentElement;
    try {
        var guardado = localStorage.getItem('tema');
        if (guardado === 'claro' || guardado === 'oscuro') raiz.setAttribute('data-tema', guardado);
    } catch (e) {}

    function esOscuro() {
        var fijo = raiz.getAttribute('data-tema');
        if (fijo) return fijo === 'oscuro';
        return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }

    document.addEventListener('DOMContentLoaded', function () {
        var boton = document.getElementById('boton-tema');
        if (!boton) return;
        boton.hidden = false;
        boton.setAttribute('aria-pressed', esOscuro() ? 'true' : 'false');
        boton.addEventListener('click', function () {
            var nuevo = esOscuro() ? 'claro' : 'oscuro';
            raiz.setAttribute('data-tema', nuevo);
            try { localStorage.setItem('tema', nuevo); } catch (e) {}
            boton.setAttribute('aria-pressed', nuevo === 'oscuro' ? 'true' : 'false');
        });
    });
})();
