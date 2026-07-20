document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('svgModal');
    const openTrigger = document.getElementById('open-modal-trigger');
    const closeTrigger = document.getElementById('close-modal-trigger');
    const modalWrapper = document.getElementById('modal-content-wrapper');

    // Abre el modal solo si el elemento interactivo existe en el DOM (cuando hay SVG generado)
    if (openTrigger) {
        openTrigger.addEventListener('click', () => {
            modal.style.display = 'block';
        });
    }

    // Cierra el modal al pulsar la 'X'
    if (closeTrigger) {
        closeTrigger.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    // Cierra el modal si se hace clic fuera del contenido del contenedor blanco
    if (modal) {
        modal.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    // Evita que los clics dentro de la tarjeta del modal lo cierren por accidente
    if (modalWrapper) {
        modalWrapper.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    }
});