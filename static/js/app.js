document.addEventListener('DOMContentLoaded', () => {
    // Cambia de idioma en cuanto se elige uno en el selector
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', () => {
            languageSelect.form.submit();
        });
    }

    // Ventana del árbol: <dialog> nativo. Atrapa el foco, cierra con Escape
    // y regresa el foco al botón que la abrió.
    const modal = document.getElementById('svgModal');
    const openTrigger = document.getElementById('open-modal-trigger');
    const closeTrigger = document.getElementById('close-modal-trigger');

    if (modal && openTrigger && typeof modal.showModal === 'function') {
        openTrigger.addEventListener('click', () => {
            modal.showModal();
            if (closeTrigger) closeTrigger.focus();
        });
        if (closeTrigger) {
            closeTrigger.addEventListener('click', () => modal.close());
        }
        // Un clic en el fondo oscuro (fuera del contenido) también cierra
        modal.addEventListener('click', (event) => {
            if (event.target === modal) modal.close();
        });
        modal.addEventListener('close', () => openTrigger.focus());
    }
});