/* Investigación actual (/documentacion/investigacion/).
   Dibuja 5 figuras en SVG: barras de resultados, modelo por turnos, cadena de
   Kempe, valle (solo mejoras contra recocido) y curvas de temperatura.
   - Cada animación tiene un botón Pausar/Reproducir (WCAG 2.2.2).
   - Con "reducir movimiento" activado, cada figura aparece ya terminada y sin botón. */
(() => {
    "use strict";
    const nodo = document.getElementById("investigacion-datos");
    if (!nodo) return;
    const DATOS = JSON.parse(nodo.textContent);
    const T = DATOS.textos;
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const NS = "http://www.w3.org/2000/svg";
    const lang = document.documentElement.lang || "es-MX";

    function el(tag, attrs, padre) {
        const e = document.createElementNS(NS, tag);
        for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
        if (padre) padre.appendChild(e);
        return e;
    }
    function texto(contenido, attrs, padre) {
        const e = el("text", attrs, padre);
        e.textContent = contenido;
        return e;
    }
    const suave = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
    const mezcla = (a, b, t) => a + (b - a) * t;

    /* Bucle de animación con pausa. dibujar(t) recibe segundos desde el inicio. */
    function animar(nombre, duracion, dibujar) {
        const boton = document.querySelector(`.boton-animacion[data-figura="${nombre}"]`);
        if (quieto) {
            dibujar(null);
            return;
        }
        let corriendo = true, inicio = null, acumulado = 0;
        function cuadro(ahora) {
            if (!corriendo) return;
            if (inicio === null) inicio = ahora - acumulado * 1000;
            acumulado = (ahora - inicio) / 1000;
            dibujar(acumulado % duracion);
            requestAnimationFrame(cuadro);
        }
        if (boton) {
            boton.hidden = false;
            boton.textContent = T.pausar;
            boton.setAttribute("aria-pressed", "false");
            boton.addEventListener("click", () => {
                corriendo = !corriendo;
                boton.textContent = corriendo ? T.pausar : T.reproducir;
                boton.setAttribute("aria-pressed", corriendo ? "false" : "true");
                if (corriendo) { inicio = null; requestAnimationFrame(cuadro); }
            });
        }
        requestAnimationFrame(cuadro);
    }

    /* ---------- 1. Barras de resultados ---------- */
    (function barras() {
        const svg = document.getElementById("fig-barras");
        if (!svg) return;
        const datos = DATOS.barras;
        const izq = 330, der = 680, arriba = 10, alto = 34, hueco = 8;
        const max = 2.4;
        const x = (v) => izq + (v / max) * (der - izq);
        for (const v of [0, 0.5, 1, 1.5, 2]) {
            el("line", { x1: x(v), x2: x(v), y1: arriba, y2: arriba + datos.length * (alto + hueco), class: "svg-rejilla" }, svg);
            texto(v.toLocaleString(lang), { x: x(v), y: arriba + datos.length * (alto + hueco) + 18, "text-anchor": "middle", class: "svg-suave" }, svg);
        }
        texto(T.millones_km, { x: der, y: arriba + datos.length * (alto + hueco) + 38, "text-anchor": "end", class: "svg-suave" }, svg);
        el("line", { x1: x(DATOS.oficial), x2: x(DATOS.oficial), y1: arriba - 4, y2: arriba + datos.length * (alto + hueco), class: "svg-trazo-2", "stroke-width": 2, "stroke-dasharray": "6 4" }, svg);
        const rects = datos.map((d, i) => {
            const y = arriba + i * (alto + hueco);
            texto(d.nombre, { x: izq - 10, y: y + alto / 2 + 5, "text-anchor": "end", class: "svg-texto" }, svg);
            const r = el("rect", { x: izq, y, height: alto, width: 0, rx: 4, class: d.oficial ? "svg-serie-2" : "svg-serie-1" }, svg);
            el("title", {}, r).textContent = `${d.nombre}: ${d.km.toLocaleString(lang)} ${T.millones_km}`;
            const etiqueta = texto(d.km.toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 3 }),
                { x: izq + 6, y: y + alto / 2 + 5, class: "svg-texto svg-halo" }, svg);
            return { r, etiqueta, d };
        });
        function dibujar(f) {
            for (const { r, etiqueta, d } of rects) {
                const w = (x(d.km) - izq) * f;
                r.setAttribute("width", Math.max(0, w));
                etiqueta.setAttribute("x", izq + w + 8);
            }
        }
        if (quieto || !("IntersectionObserver" in window)) { dibujar(1); return; }
        dibujar(0);
        const obs = new IntersectionObserver((entradas) => {
            if (!entradas.some((e) => e.isIntersecting)) return;
            obs.disconnect();
            let inicio = null;
            const paso = (ahora) => {
                if (inicio === null) inicio = ahora;
                const t = Math.min(1, (ahora - inicio) / 1200);
                dibujar(suave(t));
                if (t < 1) requestAnimationFrame(paso);
            };
            requestAnimationFrame(paso);
        }, { threshold: 0.3 });
        obs.observe(svg);
    })();

    /* ---------- 2. Modelo anterior contra modelo por turnos ---------- */
    (function turnos() {
        const svg = document.getElementById("fig-turnos");
        if (!svg) return;
        const equipos = ["NYA", "BOS", "LAN", "SDN", "CHN", "MIL"];
        // Juegos de cada equipo en cada turno (0 = descansa). Turnos pares: 4 días; impares: 3.
        const ahora = [
            [4, 3, 3, 3, 2, 3, 4, 3],
            [3, 3, 4, 0, 4, 3, 3, 3],
            [4, 3, 3, 3, 4, 0, 3, 3],
            [3, 3, 4, 3, 3, 3, 0, 3],
            [2, 3, 4, 3, 0, 3, 4, 3],
            [4, 0, 3, 3, 4, 3, 3, 3],
        ];
        const durAhora = ahora[0].map((_, t) => (t % 2 === 0 ? 4 : 3));
        const izq = 70, ancho = 640, arriba = 64, fila = 34;
        const diasAhora = durAhora.reduce((a, b) => a + b, 0);
        const dia = (ancho - izq) / diasAhora;
        const titulo = texto("", { x: izq, y: 22, class: "svg-texto" }, svg);
        const celdas = [];
        equipos.forEach((e, i) => {
            texto(e, { x: izq - 12, y: arriba + i * fila + 22, "text-anchor": "end", class: "svg-mono" }, svg);
            ahora[i].forEach((n, t) => {
                const r = el("rect", { y: arriba + i * fila + 4, height: fila - 8, rx: 4 }, svg);
                const lbl = texto("", { y: arriba + i * fila + 22, "text-anchor": "middle", class: "svg-texto" }, svg);
                celdas.push({ i, t, n, r, lbl });
            });
        });
        const marcasTurno = durAhora.map((_, t) => texto("", { y: arriba - 12, "text-anchor": "middle", class: "svg-suave" }, svg));
        function inicioTurno(dur, t) { let s = 0; for (let k = 0; k < t; k++) s += dur[k]; return s; }
        function dibujar(segundos) {
            // 0-1.5 s antes, 1.5-3 s cambia, 3-6.5 s ahora, 6.5-8 s regresa
            let f;
            if (segundos === null) f = 1;
            else if (segundos < 1.5) f = 0;
            else if (segundos < 3) f = suave((segundos - 1.5) / 1.5);
            else if (segundos < 6.5) f = 1;
            else f = 1 - suave((segundos - 6.5) / 1.5);
            titulo.textContent = f < 0.5 ? T.antes : T.ahora;
            for (const c of celdas) {
                const xA = izq + inicioTurno(durAhora.map(() => 3), c.t) * dia * diasAhora / 24;
                const wA = 3 * dia * diasAhora / 24;
                const xB = izq + inicioTurno(durAhora, c.t) * dia;
                const wB = Math.max(c.n, 0) * dia;
                const x = mezcla(xA, xB, f), w = mezcla(wA, wB, f);
                const descansa = c.n === 0 && f > 0.5;
                c.r.setAttribute("x", x + 2);
                c.r.setAttribute("width", Math.max(0, (descansa ? durAhora[c.t] * dia : w) - 4));
                c.r.setAttribute("class", descansa ? "svg-hueco" : "svg-serie-1");
                c.r.setAttribute("opacity", c.n === 0 && !descansa ? 1 - f * 1.6 : 1);
                c.lbl.setAttribute("x", x + (descansa ? durAhora[c.t] * dia : w) / 2);
                c.lbl.textContent = descansa ? "" : String(f < 0.5 ? 3 : c.n);
                c.lbl.setAttribute("class", "svg-etiqueta-celda");
            }
            marcasTurno.forEach((m, t) => {
                const xA = izq + (t * 3 + 1.5) * dia * diasAhora / 24;
                const xB = izq + (inicioTurno(durAhora, t) + durAhora[t] / 2) * dia;
                m.setAttribute("x", mezcla(xA, xB, f));
                m.textContent = `${T.turno} ${t + 1}`;
            });
        }
        texto(`${T.turno} 1, 3, 5, 7: ${T.entre_semana} (4) · ${T.turno} 2, 4, 6, 8: ${T.fin_de_semana} (3)`,
            { x: izq, y: arriba + equipos.length * fila + 22, class: "svg-suave" }, svg);
        animar("turnos", 8, dibujar);
    })();

    /* ---------- 3. Cadena de Kempe ---------- */
    (function kempe() {
        const svg = document.getElementById("fig-kempe");
        if (!svg) return;
        const equipos = ["NYA", "BOS", "TOR", "BAL", "SEA", "OAK", "TEX", "HOU"];
        const cx = 230, cy = 180, radio = 115;
        const pos = equipos.map((_, i) => {
            const a = -Math.PI / 2 + (i * 2 * Math.PI) / equipos.length;
            return [cx + radio * Math.cos(a), cy + radio * Math.sin(a)];
        });
        // Turno A: 0-1, 2-3, 4-5, 6-7. Turno B: 1-2, 3-0, 4-6, 5-7. Cadena desde NYA: 0-1, 1-2, 2-3, 3-0.
        const series = [
            { a: 0, b: 1, turno: "A", cadena: 0 }, { a: 1, b: 2, turno: "B", cadena: 1 },
            { a: 2, b: 3, turno: "A", cadena: 2 }, { a: 3, b: 0, turno: "B", cadena: 3 },
            { a: 4, b: 5, turno: "A", cadena: -1 }, { a: 6, b: 7, turno: "A", cadena: -1 },
            { a: 4, b: 6, turno: "B", cadena: -1 }, { a: 5, b: 7, turno: "B", cadena: -1 },
        ];
        const lineas = series.map((s) => el("line", {
            x1: pos[s.a][0], y1: pos[s.a][1], x2: pos[s.b][0], y2: pos[s.b][1], "stroke-linecap": "round",
        }, svg));
        const nodos = equipos.map((e, i) => {
            const c = el("circle", { cx: pos[i][0], cy: pos[i][1], r: 24, class: "svg-nodo" }, svg);
            texto(e, { x: pos[i][0], y: pos[i][1] + 5, "text-anchor": "middle", class: "svg-mono" }, svg);
            return c;
        });
        const paso = texto("", { x: 20, y: 28, class: "svg-texto" }, svg);
        texto(T.turno_a, { x: 450, y: 170, class: "svg-suave" }, svg);
        el("line", { x1: 540, y1: 165, x2: 610, y2: 165, class: "svg-trazo-1", "stroke-width": 4 }, svg);
        texto(T.turno_b, { x: 450, y: 200, class: "svg-suave" }, svg);
        el("line", { x1: 540, y1: 195, x2: 610, y2: 195, class: "svg-trazo-2", "stroke-width": 4, "stroke-dasharray": "8 6" }, svg);
        function dibujar(segundos) {
            // 0-1.5 inicio, 1.5-5.5 cadena (1 s por serie), 5.5-6.5 cambio, 6.5-9 resultado
            const s = segundos === null ? 9 : segundos;
            const iluminadas = s < 1.5 ? 0 : Math.min(4, Math.floor(s - 1.5) + 1);
            const cambio = s < 5.5 ? 0 : Math.min(1, s - 5.5);
            paso.textContent = s < 1.5 ? T.paso_inicio : s < 5.5 ? T.paso_cadena : T.paso_cambio;
            series.forEach((sr, k) => {
                const enCadena = sr.cadena >= 0 && sr.cadena < iluminadas;
                let turno = sr.turno;
                if (sr.cadena >= 0 && cambio >= 0.5) turno = turno === "A" ? "B" : "A";
                const l = lineas[k];
                l.setAttribute("class", turno === "A" ? "svg-trazo-1" : "svg-trazo-2");
                l.setAttribute("stroke-dasharray", turno === "A" ? "none" : "8 6");
                l.setAttribute("stroke-width", enCadena ? 7 : 3.5);
                l.setAttribute("opacity", sr.cadena >= 0 || s < 1.5 ? 1 : 0.45);
            });
            nodos.forEach((c, i) => {
                const activo = (i === 0 && s >= 0.3) || (i < 4 && iluminadas > 0 && i <= iluminadas);
                c.setAttribute("class", activo ? "svg-nodo-activo" : "svg-nodo");
            });
        }
        animar("kempe", 9, dibujar);
    })();

    /* ---------- 4. Valle: solo mejoras contra recocido ---------- */
    (function valle() {
        const svg = document.getElementById("fig-valle");
        if (!svg) return;
        const izq = 60, der = 690, arriba = 30, abajo = 250;
        // Costo con un valle poco profundo (x≈0.28) y uno profundo (x≈0.76)
        const costo = (x) => 0.75 - 0.35 * Math.exp(-Math.pow((x - 0.28) / 0.1, 2))
            - 0.65 * Math.exp(-Math.pow((x - 0.76) / 0.12, 2)) + 0.2 * Math.pow(x - 0.5, 2);
        const px = (x) => izq + x * (der - izq);
        const py = (y) => arriba + (1 - y) * (abajo - arriba);
        let d = "";
        for (let i = 0; i <= 200; i++) {
            const x = i / 200;
            d += `${i ? "L" : "M"}${px(x).toFixed(1)},${py(costo(x)).toFixed(1)}`;
        }
        el("line", { x1: izq, x2: der, y1: abajo, y2: abajo, class: "svg-eje" }, svg);
        el("path", { d, class: "svg-linea-costo" }, svg);
        const ejeY = texto(T.costo, { x: 16, y: 150, class: "svg-suave", transform: "rotate(-90 16 150)", "text-anchor": "middle" }, svg);
        texto(`↓ ${T.mejor}`, { x: 30, y: abajo + 20, class: "svg-suave" }, svg);
        texto(T.valle_local, { x: px(0.28), y: py(costo(0.28)) + 34, "text-anchor": "middle", class: "svg-suave" }, svg);
        texto(T.valle_profundo, { x: px(0.76), y: Math.min(py(costo(0.76)) + 30, abajo - 8), "text-anchor": "middle", class: "svg-suave" }, svg);
        void ejeY;
        const bola = el("circle", { r: 10, class: "svg-serie-1 svg-anillo" }, svg);
        const rombo = el("rect", { width: 16, height: 16, class: "svg-serie-2 svg-anillo" }, svg);
        // Trayectorias en x según el tiempo (0 a 1 de la animación de 8 s)
        const xBola = (t) => (t < 0.35 ? mezcla(0.05, 0.28, suave(t / 0.35)) : 0.28);
        function xRombo(t) {
            if (t < 0.3) return mezcla(0.05, 0.28, suave(t / 0.3));
            if (t < 0.45) return 0.28 + 0.03 * Math.sin((t - 0.3) * 80);   // tantea alrededor del valle
            if (t < 0.65) return mezcla(0.28, 0.5, suave((t - 0.45) / 0.2)); // sube la colina: acepta empeorar
            if (t < 0.85) return mezcla(0.5, 0.76, suave((t - 0.65) / 0.2));
            return 0.76;
        }
        function dibujar(segundos) {
            const t = segundos === null ? 1 : Math.min(1, segundos / 7);
            const xb = xBola(t), xr = xRombo(t);
            bola.setAttribute("cx", px(xb));
            bola.setAttribute("cy", py(costo(xb)) - 12);
            rombo.setAttribute("transform", `translate(${px(xr)} ${py(costo(xr)) - 14}) rotate(45) translate(-8 -8)`);
        }
        animar("valle", 9, dibujar);
    })();

    /* ---------- 5. Curvas de temperatura ---------- */
    (function temperatura() {
        const svg = document.getElementById("fig-temp");
        if (!svg) return;
        const izq = 80, der = 600, arriba = 20, abajo = 260;
        const yMin = Math.log10(30), yMax = Math.log10(30000);
        const px = (a) => izq + a * (der - izq);
        const py = (v) => abajo - ((Math.log10(v) - yMin) / (yMax - yMin)) * (abajo - arriba);
        for (const v of [100, 1000, 10000]) {
            el("line", { x1: izq, x2: der, y1: py(v), y2: py(v), class: "svg-rejilla" }, svg);
            texto(v.toLocaleString(lang), { x: izq - 8, y: py(v) + 5, "text-anchor": "end", class: "svg-suave" }, svg);
        }
        el("line", { x1: izq, x2: der, y1: abajo, y2: abajo, class: "svg-eje" }, svg);
        texto(T.inicio, { x: izq, y: abajo + 22, "text-anchor": "middle", class: "svg-suave" }, svg);
        texto(T.fin, { x: der, y: abajo + 22, "text-anchor": "middle", class: "svg-suave" }, svg);
        texto(T.avance, { x: (izq + der) / 2, y: abajo + 44, "text-anchor": "middle", class: "svg-suave" }, svg);
        texto("km", { x: izq - 8, y: arriba - 4, "text-anchor": "end", class: "svg-suave" }, svg);
        const curvas = [
            { f: (a) => 20000 * Math.pow(50 / 20000, a), clase: "svg-trazo-1", nombre: T.a_mano },
            { f: (a) => (0.587 * 102 * Math.exp(a)) / (a + 0.05), clase: "svg-trazo-2", nombre: T.pg_pocos },
            { f: (a) => (0.587 * 102 * Math.exp(a)) / (a + 0.5), clase: "svg-trazo-3", nombre: T.pg_muchos },
        ].map((c) => {
            let d = "";
            for (let i = 0; i <= 100; i++) {
                const a = i / 100;
                d += `${i ? "L" : "M"}${px(a).toFixed(1)},${py(c.f(a)).toFixed(1)}`;
            }
            const camino = el("path", { d, fill: "none", class: c.clase, "stroke-width": 2.5, "stroke-linejoin": "round" }, svg);
            const largo = camino.getTotalLength ? camino.getTotalLength() : 1000;
            camino.setAttribute("stroke-dasharray", `${largo} ${largo}`);
            const etiqueta = texto(c.nombre, { x: der + 10, y: py(c.f(1)) + 5, class: "svg-texto" }, svg);
            return { camino, largo, etiqueta };
        });
        // Separa las etiquetas finales si quedan encimadas
        const ys = curvas.map((c) => Number(c.etiqueta.getAttribute("y")));
        for (let i = 1; i < ys.length; i++) {
            for (let j = 0; j < i; j++) {
                if (Math.abs(ys[i] - ys[j]) < 18) ys[i] = ys[j] + (ys[i] >= ys[j] ? 18 : -18);
            }
            curvas[i].etiqueta.setAttribute("y", ys[i]);
        }
        function dibujar(segundos) {
            const f = segundos === null ? 1 : Math.min(1, segundos / 4);
            for (const c of curvas) {
                c.camino.setAttribute("stroke-dashoffset", c.largo * (1 - suave(f)));
                c.etiqueta.setAttribute("opacity", f >= 1 ? 1 : 0);
            }
        }
        animar("temp", 8, dibujar);
    })();
})();
