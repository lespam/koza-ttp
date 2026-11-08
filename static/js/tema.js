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
        var aOscuro = boton.querySelector('.tema-a-oscuro');
        var aClaro = boton.querySelector('.tema-a-claro');

        // El botón dice a qué modo cambia: "Modo claro" si ahora se ve oscuro, y al revés
        function actualizar() {
            var oscuro = esOscuro();
            aOscuro.hidden = oscuro;
            aClaro.hidden = !oscuro;
        }

        boton.hidden = false;
        actualizar();
        boton.addEventListener('click', function () {
            var nuevo = esOscuro() ? 'claro' : 'oscuro';
            raiz.setAttribute('data-tema', nuevo);
            try { localStorage.setItem('tema', nuevo); } catch (e) {}
            actualizar();
        });
        // Si el sistema cambia de modo y la persona no eligió uno, el texto también cambia
        if (window.matchMedia) {
            var consulta = window.matchMedia('(prefers-color-scheme: dark)');
            if (consulta.addEventListener) consulta.addEventListener('change', actualizar);
        }
    });
})();
