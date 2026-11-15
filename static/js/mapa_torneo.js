/* Mapa de un torneo: los estadios como puntos y los viajes de un equipo como línea.
   Lee <script id="mapa-datos"> (tesis.mapa_torneo.datos) y, si existe,
   <script id="calendario-datos"> (los juegos, para seguir a un equipo).
   - Cada estadio es un botón: al tocarlo se ven los viajes de ese equipo.
   - La lista "Ver los viajes de un equipo" hace lo mismo con el teclado.
   - El recorrido también se escribe como lista, para quien no ve el mapa.
   Sin JavaScript, la página muestra la tabla de equipos y ciudades. */
(function () {
    "use strict";
    const nodo = document.getElementById("mapa-datos");
    const raiz = document.getElementById("mapa-torneo");
    if (!nodo || !raiz) return;
    const M = JSON.parse(nodo.textContent);
    const T = M.textos;
    const idioma = document.documentElement.lang || "es";
    const nodoCal = document.getElementById("calendario-datos");
    const juegos = nodoCal ? JSON.parse(nodoCal.textContent).juegos : [];
    const porCodigo = Object.fromEntries(M.equipos.map((e) => [e.c, e]));
    const NS = "http://www.w3.org/2000/svg";
    const svgEl = (tag, attrs, padre) => {
        const e = document.createElementNS(NS, tag);
        for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
        if (padre) padre.appendChild(e);
        return e;
    };
    const crear = (tag, clase, texto) => {
        const e = document.createElement(tag);
        if (clase) e.className = clase;
        if (texto !== undefined) e.textContent = texto;
        return e;
    };
    const poner = (t, v) => t.replace(/\{(\w+)\}/g, (_m, k) => v[k]);
    const fmtKm = new Intl.NumberFormat(idioma, { maximumFractionDigits: 0 });

    // Distancia en km entre dos estadios (igual que el algoritmo: radio 6371 km)
    function km(a, b) {
        const r = Math.PI / 180;
        const h = Math.sin((b.lat - a.lat) * r / 2) ** 2
            + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin((b.lon - a.lon) * r / 2) ** 2;
        return 2 * 6371 * Math.asin(Math.sqrt(h));
    }
    // Ciudades por las que pasa un equipo: sale de casa, sigue el calendario y regresa
    function recorrido(c) {
        const paradas = [c];
        for (const [, h, v] of juegos) {
            if (h !== c && v !== c) continue;
            if (paradas[paradas.length - 1] !== h) paradas.push(h);
        }
        if (paradas[paradas.length - 1] !== c) paradas.push(c);
        return paradas;
    }

    /* ---------- Controles ---------- */
    raiz.hidden = false;
    let elegido = "";
    const etiqueta = crear("label", "cal-campo");
    etiqueta.append(T.equipo + " ");
    const select = crear("select");
    const ninguno = crear("option", "", T.ninguno);
    ninguno.value = "";
    select.appendChild(ninguno);
    [...M.equipos].sort((a, b) => a.nombre.localeCompare(b.nombre, idioma)).forEach((e) => {
        const o = crear("option", "", e.nombre);
        o.value = e.c;
        select.appendChild(o);
    });
    etiqueta.appendChild(select);
    if (juegos.length) raiz.appendChild(etiqueta);

    /* ---------- Mapa ---------- */
    const figura = crear("figure", "mapa-figura");
    const svg = svgEl("svg", { viewBox: `0 0 ${M.ancho} ${M.alto}`, role: "group", "aria-labelledby": "mapa-titulo" }, figura);
    svgEl("title", { id: "mapa-titulo" }, svg).textContent = T.titulo;
    svgEl("rect", { class: "mapa-mar", width: M.ancho, height: M.alto }, svg);
    if (M.tierra) svgEl("path", { class: "mapa-tierra", d: M.tierra }, svg);
    if (M.fronteras) svgEl("path", { class: "mapa-fronteras", d: M.fronteras }, svg);
    const defs = svgEl("defs", {}, svg);
    const flecha = svgEl("marker", { id: "mapa-flecha", viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, defs);
    svgEl("path", { d: "M0 0 L10 5 L0 10 z", class: "mapa-flecha" }, flecha);
    const capaRuta = svgEl("g", { class: "mapa-ruta" }, svg);
    const capaPuntos = svgEl("g", {}, svg);

    // Etiquetas: se prueba a la derecha, a la izquierda, arriba y abajo, cerca y luego
    // más lejos, hasta que no tapen otra etiqueta ni otro estadio. Si quedan lejos, una
    // línea fina las une con su punto.
    const ocupado = M.equipos.map((e) => ({ x0: e.x - 8, y0: e.y - 8, x1: e.x + 8, y1: e.y + 8 }));
    const choca = (a) => ocupado.some((b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1)
        || a.x0 < 2 || a.y0 < 2 || a.x1 > M.ancho - 2 || a.y1 > M.alto - 2;
    function lugarDeEtiqueta(e) {
        const w = e.c.length * 9.5 + 2, h = 16;
        for (const d of [11, 24, 40]) {
            const opciones = [
                [e.x + d, e.y - h / 2], [e.x - d - w, e.y - h / 2],
                [e.x - w / 2, e.y - d - h], [e.x - w / 2, e.y + d],
                [e.x + d * 0.7, e.y - d * 0.7 - h], [e.x - d * 0.7 - w, e.y - d * 0.7 - h],
                [e.x + d * 0.7, e.y + d * 0.7], [e.x - d * 0.7 - w, e.y + d * 0.7],
            ];
            for (const [x, y] of opciones) {
                const caja = { x0: x, y0: y, x1: x + w, y1: y + h };
                if (!choca(caja)) { ocupado.push(caja); return { x, y, w, h, lejos: d > 11 }; }
            }
        }
        return { x: e.x + 11, y: e.y - h / 2, w, h, lejos: false };
    }
    const marcas = {};
    for (const e of M.equipos) {
        const g = svgEl("g", { class: "mapa-estadio", tabindex: juegos.length ? 0 : -1, "aria-label": `${e.nombre}, ${e.lugar}` }, capaPuntos);
        if (juegos.length) g.setAttribute("role", "button");
        const l = lugarDeEtiqueta(e);
        if (l.lejos) {
            const cx = Math.max(l.x, Math.min(e.x, l.x + l.w)), cy = Math.max(l.y, Math.min(e.y, l.y + l.h));
            svgEl("line", { x1: e.x, y1: e.y, x2: cx, y2: cy, class: "mapa-guia" }, g);
        }
        svgEl("circle", { cx: e.x, cy: e.y, r: 7 }, g);
        const t = svgEl("text", { x: l.x + 1, y: l.y + 13 }, g);
        t.textContent = e.c;
        svgEl("title", {}, g).textContent = `${e.nombre} · ${e.lugar}`;
        const elegir = () => { elegido = elegido === e.c ? "" : e.c; select.value = elegido; dibujar(); };
        g.addEventListener("click", elegir);
        g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); elegir(); } });
        marcas[e.c] = g;
    }

    const leyenda = crear("figcaption", "nota", T.leyenda);
    figura.appendChild(leyenda);
    raiz.appendChild(figura);
    const estado = crear("p", "mapa-estado");
    estado.setAttribute("aria-live", "polite");
    const detalle = crear("details", "mapa-recorrido");
    const resumenDetalle = crear("summary", "", T.recorrido);
    const lista = crear("ol");
    detalle.append(resumenDetalle, lista);
    if (juegos.length) raiz.append(estado, detalle);

    function dibujar() {
        capaRuta.replaceChildren();
        lista.replaceChildren();
        for (const [c, g] of Object.entries(marcas)) {
            g.classList.toggle("mapa-elegido", c === elegido);
            g.classList.toggle("mapa-apagado", !!elegido && c !== elegido);
            g.setAttribute("aria-pressed", String(c === elegido));
        }
        detalle.hidden = !elegido;
        if (!elegido) { estado.textContent = T.sin_viaje; return; }
        const paradas = recorrido(elegido);
        let total = 0;
        for (let i = 1; i < paradas.length; i++) {
            const a = porCodigo[paradas[i - 1]], b = porCodigo[paradas[i]];
            total += km(a, b);
            // Curva suave: así las idas y vueltas entre dos ciudades no se tapan
            const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
            const dx = b.x - a.x, dy = b.y - a.y;
            const d = `M${a.x} ${a.y} Q${mx - dy * 0.15} ${my + dx * 0.15} ${b.x} ${b.y}`;
            svgEl("path", { d, "marker-end": "url(#mapa-flecha)" }, capaRuta);
        }
        paradas.forEach((c, i) => {
            const e = porCodigo[c];
            let texto = `${e.lugar} (${e.nombre})`;
            if (i === 0) texto += ` · ${T.casa}`;
            else if (i === paradas.length - 1) texto += ` · ${T.regreso}`;
            lista.appendChild(crear("li", "", texto));
        });
        estado.textContent = poner(T.viaje, { equipo: porCodigo[elegido].nombre, km: fmtKm.format(total), n: paradas.length - 1 });
    }
    select.addEventListener("change", () => { elegido = select.value; dibujar(); });
    dibujar();
})();
