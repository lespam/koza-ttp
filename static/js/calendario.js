/* Calendario dinámico: muestra los juegos de un calendario por semana, por mes o por año.
   Lee los datos de <script type="application/json" id="calendario-datos">:
     {juegos: [["2026-11-07", "ATL", "MIA"], ...]  (fecha, en casa, visita),
      equipos: {"ATL": "Atlanta Braves", ...}, textos: {...}}
   - Tres vistas: semana, mes y año. Botones de anterior y siguiente, y una lista de meses.
   - En la vista por año, cada día con juegos es un botón que abre esa semana.
   - Filtro por equipo: marca si juega en casa o de visita, con palabras y con forma
     (relleno o borde punteado), no solo con color.
   - En pantallas angostas, la semana y el mes se ven como agenda (lista por día).
   Sin JavaScript, la página muestra la tabla completa de juegos. */
(function () {
    "use strict";
    const nodo = document.getElementById("calendario-datos");
    const raiz = document.getElementById("calendario-dinamico");
    if (!nodo || !raiz) return;
    const D = JSON.parse(nodo.textContent);
    const T = D.textos;
    const idioma = document.documentElement.lang || "es";
    if (!D.juegos.length) return;

    // Juegos por día: {"2026-11-07": [[casa, visita], ...]}
    const porDia = {};
    for (const [f, h, v] of D.juegos) (porDia[f] = porDia[f] || []).push([h, v]);
    const dias = Object.keys(porDia).sort();
    const primerDia = dias[0];
    const ultimoDia = dias[dias.length - 1];
    const meses = [...new Set(dias.map((d) => d.slice(0, 7)))];
    const anios = [...new Set(dias.map((d) => d.slice(0, 4)))];
    const nombre = (c) => D.equipos[c] || c;

    /* ---------- Fechas (siempre a mediodía, para no cambiar de día por el horario) ---------- */
    const fechaDe = (iso) => new Date(iso + "T12:00:00");
    const isoDe = (f) => `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, "0")}-${String(f.getDate()).padStart(2, "0")}`;
    const sumarDias = (iso, n) => { const f = fechaDe(iso); f.setDate(f.getDate() + n); return isoDe(f); };
    const lunesDe = (iso) => sumarDias(iso, -((fechaDe(iso).getDay() + 6) % 7));
    const fmtMes = new Intl.DateTimeFormat(idioma, { month: "long", year: "numeric" });
    const fmtSoloMes = new Intl.DateTimeFormat(idioma, { month: "long" });
    const fmtDia = new Intl.DateTimeFormat(idioma, { weekday: "long", day: "numeric", month: "long" });
    const fmtCorto = new Intl.DateTimeFormat(idioma, { day: "numeric", month: "short" });
    const fmtSemana = new Intl.DateTimeFormat(idioma, { weekday: "short" });
    const fmtInicial = new Intl.DateTimeFormat(idioma, { weekday: "narrow" });
    const mayuscula = (t) => t.charAt(0).toLocaleUpperCase(idioma) + t.slice(1);
    const poner = (t, v) => t.replace(/\{(\w+)\}/g, (_m, k) => v[k]);
    const crear = (tag, clase, texto) => {
        const e = document.createElement(tag);
        if (clase) e.className = clase;
        if (texto !== undefined) e.textContent = texto;
        return e;
    };

    let vista = "mes";
    let cursor = primerDia; // un día dentro de la semana, el mes o el año que se ve
    let equipo = "";

    /* ---------- Controles ---------- */
    raiz.hidden = false;
    const grupoVista = crear("div", "cal-vistas");
    grupoVista.setAttribute("role", "group");
    grupoVista.setAttribute("aria-label", T.vista);
    const botonesVista = {};
    for (const v of ["semana", "mes", "anio"]) {
        const b = crear("button", "boton-secundario", T["vista_" + v]);
        b.type = "button";
        b.addEventListener("click", () => { vista = v; dibujar(); });
        botonesVista[v] = b;
        grupoVista.appendChild(b);
    }

    const controles = crear("div", "cal-controles");
    const anterior = crear("button", "boton-secundario");
    const siguiente = crear("button", "boton-secundario");
    anterior.type = siguiente.type = "button";
    const etiquetaMes = crear("label", "cal-campo");
    etiquetaMes.append(T.ir_a + " ");
    const selectMes = crear("select");
    meses.forEach((m) => {
        const o = crear("option", "", mayuscula(fmtMes.format(fechaDe(m + "-01"))));
        o.value = m;
        selectMes.appendChild(o);
    });
    etiquetaMes.appendChild(selectMes);
    const etiquetaEquipo = crear("label", "cal-campo");
    etiquetaEquipo.append(T.equipo + " ");
    const selectEquipo = crear("select");
    const todos = crear("option", "", T.todos);
    todos.value = "";
    selectEquipo.appendChild(todos);
    Object.keys(D.equipos).sort((a, b) => nombre(a).localeCompare(nombre(b), idioma)).forEach((c) => {
        const o = crear("option", "", nombre(c));
        o.value = c;
        selectEquipo.appendChild(o);
    });
    etiquetaEquipo.appendChild(selectEquipo);
    controles.append(anterior, etiquetaMes, siguiente, etiquetaEquipo);

    const titulo = crear("h3", "cal-titulo");
    titulo.id = "cal-titulo";
    const estado = crear("p", "nota cal-estado");
    estado.setAttribute("aria-live", "polite");
    const leyenda = crear("p", "nota cal-leyenda");
    const cuerpo = crear("div", "cal-cuerpo");
    raiz.append(grupoVista, controles, titulo, estado, leyenda, cuerpo);

    /* ---------- Juegos ---------- */
    function juegosDelDia(iso) {
        const lista = porDia[iso] || [];
        return equipo ? lista.filter(([h, v]) => h === equipo || v === equipo) : lista;
    }
    function juego([h, v], largo) {
        const li = crear("li", "cal-juego");
        const texto = poner(T.juego, { casa: nombre(h), visita: nombre(v) });
        if (!equipo) {
            if (largo) li.textContent = texto;
            else {
                li.append(crear("span", "cal-casa", h), " – ", crear("span", "", v));
                li.title = texto;
                li.appendChild(crear("span", "visualmente-oculto", " (" + texto + ")"));
            }
            return li;
        }
        const enCasa = h === equipo;
        const rival = enCasa ? v : h;
        li.classList.add(enCasa ? "cal-en-casa" : "cal-de-visita");
        li.append(crear("span", "cal-lugar", enCasa ? T.casa : T.visita), " ",
            crear("span", "", poner(enCasa ? T.contra : T.en, { rival: largo ? nombre(rival) : rival })));
        li.title = texto;
        return li;
    }
    function contar(desde, hasta) {
        let n = 0, casa = 0;
        for (let d = desde; d <= hasta; d = sumarDias(d, 1)) {
            for (const [h] of juegosDelDia(d)) { n++; if (equipo && h === equipo) casa++; }
        }
        return { n, casa };
    }
    function resumen(desde, hasta, periodo) {
        const { n, casa } = contar(desde, hasta);
        return equipo
            ? poner(T.resumen_equipo, { equipo: nombre(equipo), n, casa, visita: n - casa, periodo })
            : poner(T.resumen, { n, periodo });
    }

    /* Agenda: lista de los días con juego (pantallas angostas en semana y mes) */
    function agenda(desde, hasta, largo) {
        const ol = crear("ol", "cal-agenda");
        for (let d = desde; d <= hasta; d = sumarDias(d, 1)) {
            const lista = juegosDelDia(d);
            if (!lista.length) continue;
            const li = crear("li");
            li.appendChild(crear("h4", "cal-dia", fmtDia.format(fechaDe(d))));
            const ul = crear("ul", "cal-lista");
            lista.forEach((j) => ul.appendChild(juego(j, largo)));
            li.appendChild(ul);
            ol.appendChild(li);
        }
        if (!ol.children.length) ol.appendChild(crear("li", "nota", T.sin_juegos));
        return ol;
    }
    function cabeceraSemana(clase) {
        const thead = crear("thead");
        const fila = crear("tr");
        for (let i = 0; i < 7; i++) {
            const th = crear("th", "", fmtSemana.format(new Date(2024, 0, 1 + i, 12))); // 1 ene 2024 fue lunes
            th.scope = "col";
            if (clase) {
                th.textContent = fmtInicial.format(new Date(2024, 0, 1 + i, 12));
                th.title = fmtSemana.format(new Date(2024, 0, 1 + i, 12));
            }
            fila.appendChild(th);
        }
        thead.appendChild(fila);
        return thead;
    }

    /* ---------- Vista por semana ---------- */
    function dibujarSemana() {
        const lunes = lunesDe(cursor);
        const domingo = sumarDias(lunes, 6);
        titulo.textContent = poner(T.titulo_semana, { inicio: fmtCorto.format(fechaDe(lunes)), fin: fmtCorto.format(fechaDe(domingo)) });
        estado.textContent = resumen(lunes, domingo, T.esta_semana);
        anterior.disabled = lunes <= primerDia;
        siguiente.disabled = domingo >= ultimoDia;

        const tabla = crear("table", "cal-mes cal-semana");
        tabla.setAttribute("aria-labelledby", "cal-titulo");
        const thead = crear("thead");
        const filaCab = crear("tr");
        const fila = crear("tr");
        for (let i = 0; i < 7; i++) {
            const d = sumarDias(lunes, i);
            const th = crear("th", "", fmtSemana.format(fechaDe(d)) + " " + fechaDe(d).getDate());
            th.scope = "col";
            filaCab.appendChild(th);
            const td = crear("td");
            const lista = juegosDelDia(d);
            if (lista.length) {
                td.classList.add("cal-con-juegos");
                const ul = crear("ul", "cal-lista");
                lista.forEach((j) => ul.appendChild(juego(j, false)));
                td.appendChild(ul);
            } else td.appendChild(crear("span", "nota", T.descanso));
            fila.appendChild(td);
        }
        thead.appendChild(filaCab);
        const tbody = crear("tbody");
        tbody.appendChild(fila);
        tabla.append(thead, tbody);
        const envoltura = crear("div", "cal-desliza");
        envoltura.appendChild(tabla);
        cuerpo.replaceChildren(envoltura, agenda(lunes, domingo, true));
    }

    /* ---------- Vista por mes ---------- */
    function dibujarMes() {
        const m = cursor.slice(0, 7);
        const [anio, numMes] = m.split("-").map(Number);
        const primero = new Date(anio, numMes - 1, 1, 12);
        const totalDias = new Date(anio, numMes, 0).getDate();
        const desplazar = (primero.getDay() + 6) % 7; // la semana empieza en lunes
        const periodo = fmtMes.format(primero);
        titulo.textContent = mayuscula(periodo);
        const iso = (d) => `${m}-${String(d).padStart(2, "0")}`;
        estado.textContent = resumen(iso(1), iso(totalDias), periodo);
        anterior.disabled = m <= meses[0];
        siguiente.disabled = m >= meses[meses.length - 1];

        const tabla = crear("table", "cal-mes");
        tabla.setAttribute("aria-labelledby", "cal-titulo");
        const tbody = crear("tbody");
        let fila = crear("tr");
        for (let i = 0; i < desplazar; i++) fila.appendChild(crear("td", "cal-vacio"));
        for (let d = 1; d <= totalDias; d++) {
            const td = crear("td");
            const lista = juegosDelDia(iso(d));
            td.appendChild(crear("span", "cal-numero", String(d)));
            if (lista.length) {
                td.classList.add("cal-con-juegos");
                const ul = crear("ul", "cal-lista");
                lista.forEach((j) => ul.appendChild(juego(j, false)));
                td.appendChild(ul);
            }
            fila.appendChild(td);
            if ((desplazar + d) % 7 === 0) { tbody.appendChild(fila); fila = crear("tr"); }
        }
        if (fila.children.length) {
            while (fila.children.length < 7) fila.appendChild(crear("td", "cal-vacio"));
            tbody.appendChild(fila);
        }
        tabla.append(cabeceraSemana(false), tbody);
        const envoltura = crear("div", "cal-desliza");
        envoltura.appendChild(tabla);
        cuerpo.replaceChildren(envoltura, agenda(iso(1), iso(totalDias), false));
    }

    /* ---------- Vista por año: un mes pequeño por cada mes con juegos ---------- */
    function dibujarAnio() {
        const anio = cursor.slice(0, 4);
        titulo.textContent = poner(T.titulo_anio, { anio });
        estado.textContent = resumen(anio + "-01-01", anio + "-12-31", anio);
        anterior.disabled = anio <= anios[0];
        siguiente.disabled = anio >= anios[anios.length - 1];

        const rejilla = crear("div", "cal-anio");
        for (const m of meses.filter((x) => x.startsWith(anio))) {
            const [a, numMes] = m.split("-").map(Number);
            const primero = new Date(a, numMes - 1, 1, 12);
            const totalDias = new Date(a, numMes, 0).getDate();
            const desplazar = (primero.getDay() + 6) % 7;
            const tabla = crear("table", "cal-mini");
            const cap = crear("caption", "", mayuscula(fmtSoloMes.format(primero)));
            tabla.appendChild(cap);
            const tbody = crear("tbody");
            let fila = crear("tr");
            for (let i = 0; i < desplazar; i++) fila.appendChild(crear("td"));
            for (let d = 1; d <= totalDias; d++) {
                const iso = `${m}-${String(d).padStart(2, "0")}`;
                const td = crear("td");
                const lista = juegosDelDia(iso);
                if (lista.length) {
                    const b = crear("button", "cal-mini-dia", String(d));
                    b.type = "button";
                    let detalle;
                    if (equipo) {
                        const [h, v] = lista[0];
                        const enCasa = h === equipo;
                        b.classList.add(enCasa ? "cal-mini-casa" : "cal-mini-visita");
                        detalle = (enCasa ? T.casa : T.visita) + " " + poner(enCasa ? T.contra : T.en, { rival: nombre(enCasa ? v : h) });
                    } else {
                        b.classList.add("cal-mini-juegos");
                        detalle = poner(T.n_juegos, { n: lista.length });
                    }
                    b.setAttribute("aria-label", mayuscula(fmtDia.format(fechaDe(iso))) + ": " + detalle + ". " + T.abrir_semana);
                    b.title = detalle;
                    b.addEventListener("click", () => { cursor = iso; vista = "semana"; dibujar(); titulo.focus(); });
                    td.appendChild(b);
                } else td.appendChild(crear("span", "cal-mini-libre", String(d)));
                fila.appendChild(td);
                if ((desplazar + d) % 7 === 0) { tbody.appendChild(fila); fila = crear("tr"); }
            }
            if (fila.children.length) tbody.appendChild(fila);
            tabla.append(cabeceraSemana(true), tbody);
            rejilla.appendChild(tabla);
        }
        cuerpo.replaceChildren(rejilla);
    }

    /* ---------- Dibujar ---------- */
    function mover(sentido) {
        if (vista === "semana") cursor = sumarDias(lunesDe(cursor), sentido * 7);
        else if (vista === "mes") {
            const i = meses.indexOf(cursor.slice(0, 7)) + sentido;
            cursor = meses[Math.max(0, Math.min(meses.length - 1, i))] + "-01";
        } else {
            const i = anios.indexOf(cursor.slice(0, 4)) + sentido;
            const anio = anios[Math.max(0, Math.min(anios.length - 1, i))];
            cursor = dias.find((d) => d.startsWith(anio));
        }
        dibujar();
    }
    function dibujar() {
        for (const [v, b] of Object.entries(botonesVista)) b.setAttribute("aria-pressed", String(v === vista));
        anterior.textContent = "← " + T["anterior_" + vista];
        siguiente.textContent = T["siguiente_" + vista] + " →";
        etiquetaMes.hidden = vista === "anio";
        selectMes.value = cursor.slice(0, 7);
        raiz.dataset.vista = vista;
        leyenda.textContent = equipo
            ? (vista === "anio" ? T.leyenda_anio_equipo : T.leyenda_equipo)
            : (vista === "anio" ? T.leyenda_anio : T.leyenda);
        if (vista === "semana") dibujarSemana();
        else if (vista === "mes") dibujarMes();
        else dibujarAnio();
    }

    titulo.tabIndex = -1;
    anterior.addEventListener("click", () => mover(-1));
    siguiente.addEventListener("click", () => mover(1));
    selectMes.addEventListener("change", () => {
        // El primer día con juego de ese mes (o el día 1 si no hay)
        cursor = dias.find((d) => d.startsWith(selectMes.value)) || selectMes.value + "-01";
        dibujar();
    });
    selectEquipo.addEventListener("change", () => { equipo = selectEquipo.value; dibujar(); });
    dibujar();
})();
