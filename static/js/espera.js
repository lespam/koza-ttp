// Espera de la optimización: muestra un aviso con un árbol animado (Lottie)
// mientras el servidor trabaja, y evita lanzar la misma ejecución dos veces.
document.addEventListener('DOMContentLoaded', function () {
    var boton = document.getElementById('boton-ejecutar');
    var espera = document.getElementById('espera');
    var contenedor = document.getElementById('espera-animacion');
    if (!boton || !espera) return;

    var enCurso = false;
    boton.addEventListener('click', function (evento) {
        if (enCurso) { evento.preventDefault(); return; }
        enCurso = true;
        boton.setAttribute('aria-disabled', 'true');
        boton.classList.add('boton-ocupado');
        espera.hidden = false;

        if (!window.lottie || !contenedor) return;
        var sinMovimiento = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var animacion = window.lottie.loadAnimation({
            container: contenedor,
            renderer: 'svg',
            loop: !sinMovimiento,
            autoplay: !sinMovimiento,
            path: contenedor.getAttribute('data-animacion')
        });
        // Con movimiento reducido se muestra el árbol completo, quieto
        if (sinMovimiento) {
            animacion.addEventListener('DOMLoaded', function () { animacion.goToAndStop(56, true); });
        }
    });
});
