#!/usr/bin/env python3
"""
Script de generación del Informe Final de Semana 3 para SIMTELE-RISK.
Genera docs/informe_final_semana3.docx y docs/informe_final_semana3.md
con los 18 apartados exigidos en la Sección 11 de la consigna oficial,
calculando en tiempo real todos los resultados verificados de los 4 módulos × 3 escenarios.
"""
import os
import sys
import numpy as np
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(__file__))
import metodos
import modulo1
import modulo2
import modulo3
import modulo4


def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_cell_margins(cell, top=90, bottom=90, left=140, right=140):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def format_table(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell in table.rows[0].cells:
        set_cell_background(cell, '1e3a8a')
        set_cell_margins(cell, 110, 110, 130, 130)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(9.0)
                r.font.name = 'Calibri'
    for row_idx, row in enumerate(table.rows[1:]):
        bg = 'f8fafc' if row_idx % 2 == 1 else 'ffffff'
        for cell in row.cells:
            set_cell_background(cell, bg)
            set_cell_margins(cell, 75, 75, 110, 110)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.8)
                    r.font.name = 'Calibri'
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                if idx < len(row.cells):
                    row.cells[idx].width = width


def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.name = 'Calibri'
        r.font.color.rgb = RGBColor(30, 58, 138) if level == 1 else RGBColor(2, 132, 199)
    return h


def add_callout(doc, title, text, border_color='1e3a8a', bg_color='f0f9ff'):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, 130, 130, 180, 180)
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), border_color)
    tcBorders.append(left)
    for side in ['top', 'bottom', 'right']:
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'), 'none')
        tcBorders.append(b)
    tcPr.append(tcBorders)
    p = cell.paragraphs[0]
    if title:
        rt = p.add_run(f"{title}\n")
        rt.bold = True
        rt.font.name = 'Calibri'
        rt.font.size = Pt(10)
        rt.font.color.rgb = RGBColor(30, 58, 138)
    rx = p.add_run(text)
    rx.font.name = 'Calibri'
    rx.font.size = Pt(9.5)
    rx.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, 'f1f5f9')
    set_cell_margins(cell, 100, 100, 140, 140)
    p = cell.paragraphs[0]
    r = p.add_run(code_text)
    r.font.name = 'Consolas'
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 23, 42)
    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_table_data(doc, headers, rows):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    for j, h in enumerate(headers):
        tbl.rows[0].cells[j].text = h
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            tbl.rows[i].cells[j].text = str(val)
    format_table(tbl)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def collect_results():
    """Ejecuta todos los módulos y escenarios para incluir cifras verificadas."""
    data = {'m1': {}, 'm2': {}, 'm3': {}, 'm4': {}}
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        data['m1'][t] = modulo1.ejecutar(t)
        data['m2'][t] = modulo2.ejecutar(t)
        data['m3'][t] = modulo3.ejecutar(t)
        data['m4'][t] = modulo4.ejecutar(t)
    return data


def build_reports():
    res = collect_results()
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(0.9)
        s.bottom_margin = Inches(0.9)
        s.left_margin = Inches(0.9)
        s.right_margin = Inches(0.9)

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)

    # 1. PORTADA
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(36)
    r1 = p_top.add_run("DESAFÍO INTEGRADOR FINAL · MÉTODOS NUMÉRICOS\n")
    r1.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = RGBColor(2, 132, 199)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    rt = p_title.add_run("SIMTELE-RISK\n")
    rt.bold = True
    rt.font.size = Pt(28)
    rt.font.color.rgb = RGBColor(30, 58, 138)
    rs = p_title.add_run(
        "Sistema Integrado de Simulación Numérica y Análisis de Riesgos Operacionales\n"
        "Inspirado en el Sistema de Transporte por Cable Urbano Mi Teleférico (La Paz – El Alto)\n\n"
        "INFORME FINAL — SEMANA 3: VALIDACIÓN, CONCLUSIONES Y DEFENSA"
    )
    rs.font.size = Pt(13)
    rs.font.color.rgb = RGBColor(51, 65, 85)

    add_callout(
        doc,
        "DESCARGO ACADÉMICO OBLIGATORIO",
        "Este proyecto es una simulación interdisciplinaria estrictamente educativa. Los datos son sintéticos y los parámetros físicos están inspirados en literatura técnica (Doppelmayr 10-MGD, normas europeas EN 12929-1 y EN 12927). No describen fallas verificadas de Mi Teleférico ni existe conexión con equipos reales de control.",
        border_color='0284c7', bg_color='f0f9ff'
    )

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(24)
    p_meta.add_run(
        "Aplicación Desplegada: https://simtele-risk.vercel.app/\n"
        "Motor de Base de Datos: Turso (LibSQL) + SQLite Local (simtele.db)\n"
        "Año Académico: 2026"
    ).font.size = Pt(10.5)
    doc.add_page_break()

    # 2. PARTICIPANTES Y MENCIÓN
    add_heading_styled(doc, "1. Participantes y Mención", 1)
    add_table_data(
        doc,
        ["Integrante", "Mención / Área", "Aporte Principal en SIMTELE-RISK"],
        [
            ["[Nombre Integrante 1]", "Ingeniería de Sistemas", "Arquitectura de riesgos, DER, modelo relacional, validaciones RF01-RF06 y persistencia."],
            ["[Nombre Integrante 2]", "Desarrollo de Software", "Backend Flask, adaptador HTTP Turso DB, despliegue en Vercel, UI/UX y Chart.js."],
            ["[Nombre Integrante 3]", "Métodos Numéricos / Computación", "Implementación de núcleos numéricos (sistemas lineales, raíces, interpolación, integración, EDO) y pruebas analíticas."],
            ["[Nombre Integrante 4]", "Validación y Análisis", "Diseño de escenarios NORMAL/ESTRÉS/MAL CONDICIONADO, teoría de errores y conclusiones técnicas."]
        ]
    )

    # 3. RESUMEN Y OBJETIVOS
    add_heading_styled(doc, "2. Resumen Ejecutivo", 1)
    doc.add_paragraph(
        "SIMTELE-RISK integra cuatro casos de estudio matemáticos aplicados al transporte por cable urbano: "
        "(1) Detención de emergencia de cabinas, (2) Deterioro mecánico y mantenimiento predictivo, "
        "(3) Oscilaciones transversales por viento lateral y (4) Reconstrucción de telemetría de sensores. "
        "Cada módulo ejecuta de forma reproducible los escenarios NORMAL, ESTRÉS y MAL CONDICIONADO, "
        "además de permitir parámetros personalizados por el usuario y persistir cada corrida en una base de datos relacional de 6 tablas sobre Turso LibSQL / SQLite."
    )

    add_heading_styled(doc, "3. Objetivos", 1)
    doc.add_paragraph(
        "• Objetivo General: Desarrollar, validar y desplegar una aplicación web integral capaz de resolver modelos matemáticos de ingeniería mediante métodos numéricos verificados contra referencias analíticas, analizando errores, estabilidad, condicionamiento y significado físico-operativo.\n"
        "• Objetivos Específicos:\n"
        "  1. Formular los 4 modelos físicos con variables, unidades, hipótesis y límites de validez explícitos.\n"
        "  2. Implementar y comparar todas las familias numéricas exigidas: sistemas lineales (Jacobi, Gauss-Seidel, LU, Gradiente Conjugado), raíces (Bisección, Newton-Raphson, Secante), interpolación (Lagrange, Newton, Splines Cúbicos), integración (Trapecio, Simpson 1/3, Romberg) y EDO (RK2 Heun, RK4).\n"
        "  3. Evaluar transversalmente error absoluto, relativo protegido, porcentual, residual y número de condición κ(A).\n"
        "  4. Garantizar persistencia verificable (guardar, cerrar, recuperar y relanzar dentro de tolerancia) en Turso DB y SQLite."
    )

    # 4. ARQUITECTURA GENERAL Y DER
    add_heading_styled(doc, "4. Arquitectura General y Modelo de Datos (DER)", 1)
    doc.add_paragraph(
        "La aplicación sigue una arquitectura modular en Python/Flask desplegada como Serverless Function en Vercel (vercel.json), conectada mediante pipelines HTTP agrupados (src/db_adapter.py) a una base de datos Turso (LibSQL) en la nube y con respaldo local automático en SQLite (simtele.db). El esquema relacional (sql/schema.sql y docs/DER.md) comprende 6 entidades normalizadas con integridad referencial (ON DELETE CASCADE) y restricciones CHECK:"
    )
    add_table_data(
        doc,
        ["Tabla", "Clave Primaria / Foráneas", "Propósito en el Sistema"],
        [
            ["caso_estudio", "id (PK)", "Catálogo de los 4 casos de estudio obligatorios y su versión."],
            ["escenario", "id (PK), caso_id (FK)", "Tipo (NORMAL, ESTRES, MAL_CONDICIONADO, PERSONALIZADO), parámetros JSON y fuente."],
            ["simulacion", "id (PK), escenario_id (FK)", "Instancia ejecutada con fecha UTC, equipo y estado COMPLETA."],
            ["ejecucion_metodo", "id (PK), simulacion_id (FK)", "Método ejecutado, tolerancia, paso, convergencia y tiempo en ms."],
            ["iteracion_resultado", "id (PK), ejecucion_id (FK)", "Historial paso a paso (aproximación JSON, residual, error_abs, error_rel)."],
            ["resultado_resumen", "id (PK), ejecucion_id (FK)", "Referencia, valor final JSON, métricas resumen e interpretación."]
        ]
    )

    # 5. DEFINICIÓN DE LOS 4 MÓDULOS Y FUNDAMENTOS MATEMÁTICOS
    add_heading_styled(doc, "5. Definición de Módulos y Modelos Matemáticos", 1)
    add_table_data(
        doc,
        ["Módulo", "Pregunta Física", "Ecuaciones / Modelo", "Referencia Verificable"],
        [
            ["M1: Detención de Emergencia", "¿Alcanza la vía libre L al frenar?", "dx/dt = v; dv/dt = -a(v,t); x(0)=0, v(0)=v0", "Constante: d = v0·tr + v0²/(2a). No lineal: d = v0·tr + 2v0²/(3a)."],
            ["M2: Deterioro y Mantenimiento", "¿Cuándo D(t) alcanza el umbral?", "Calibración Ax = b (SPD); D(t) = D0 + αt + βt² = D_u", "Raíz positiva cuadrática t* y vector conocido x* en A·x* = b."],
            ["M3: Oscilaciones por Viento", "¿Supera el gálibo lateral (0.80 m)?", "m·x'' + c·x' + k·x = F0·cos(ωf·t); E = ∫ x(t)² dt", "Libre (F0=0): x(t)=e^(-ζω0t)[C1 cos(ωdt)+C2 sin(ωdt)]. Forzada: RK4 paso h/4."],
            ["M4: Reconstrucción de Sensores", "¿Cómo recuperar datos faltantes?", "Interpolación P_n(t) y Splines C² sobre nodos {t_i, y_i}", "Señales conocidas sin(t) y 1/(1+25t²) evaluadas en puntos ocultados."]
        ]
    )

    # 6. MÉTODOS Y PSEUDOCÓDIGO
    add_heading_styled(doc, "6. Métodos Implementados y Pseudocódigo Resumido", 1)
    add_code_block(
        doc,
        "A) SISTEMAS LINEALES (Jacobi, Gauss-Seidel, LU con pivoteo PA=LU, Gradiente Conjugado):\n"
        "  • Jacobi: x^(k+1) = D^(-1)(b - (L+U)x^(k)) hasta ||b - Ax|| < tol*||b|| o overflow (>1e30).\n"
        "  • Gauss-Seidel: actualiza componente x_i in-place usando valores recién calculados.\n"
        "  • LU: factorización PA = LU con pivoteo parcial + sustitución adelante/atrás.\n"
        "  • Gradiente Conjugado (SPD): direcciones A-ortogonales d_k, paso α_k = (r^T r)/(d^T A d).\n\n"
        "B) BÚSQUEDA DE RAÍCES (Bisección, Newton-Raphson, Secante):\n"
        "  • Bisección: si f(a)f(b)<=0, c=(a+b)/2, reemplaza extremo de igual signo.\n"
        "  • Newton: x_(k+1) = x_k - f(x_k)/f'(x_k) con guarda |f'(x)| < 1e-15.\n"
        "  • Secante: x_(k+1) = x_k - f(x_k)(x_k - x_(k-1))/(f(x_k) - f(x_(k-1))).\n\n"
        "C) INTERPOLACIÓN (Lagrange, Newton Dif. Divididas, Splines Cúbicos Naturales):\n"
        "  • Splines C²: sistema tridiagonal en segundas derivadas c_i con c_0 = c_n = 0.\n\n"
        "D) INTEGRACIÓN (Trapecio, Simpson 1/3, Romberg) y EDO (RK2 Heun, RK4):\n"
        "  • Romberg: R[k,j] = R[k,j-1] + (R[k,j-1]-R[k-1,j-1])/(4^j - 1).\n"
        "  • RK4: y_(n+1) = y_n + (h/6)(k1 + 2k2 + 2k3 + k4)."
    )

    # 7. PRUEBAS ANALÍTICAS Y PERSISTENCIA
    add_heading_styled(doc, "7. Pruebas Analíticas y Verificación de Persistencia", 1)
    doc.add_paragraph(
        "Se verificaron dos suites automatizadas en Python:\n"
        "1. src/test_metodos.py: valida convergencia de sistemas lineales sobre tridiagonal SPD, cota de sensibilidad de Hilbert ||δx||/||x|| ≤ κ(A)||δb||/||b||, radios espectrales ρ(T_J) y ρ(T_GS), raíces de D(t), cuadraturas exactas, EDO de M1 y M3 contra solución analítica, y estabilidad de Splines frente al fenómeno de Runge.\n"
        "2. src/test_persistencia.py: ejecuta M2 NORMAL → guarda en SQLite → cierra conexión → reconecta → recupera parámetros → recalcula → verifica coincidencia exacta con tolerancia atol < 1e-14. Adicionalmente, la ruta /relanzar/<id> permite repetir desde la web tanto escenarios predefinidos como simulaciones PERSONALIZADO recuperando parametros_json."
    )

    # 8. RESULTADOS POR MÓDULO Y ESCENARIO (3 x 4)
    add_heading_styled(doc, "8. Resultados Experimentales (4 Módulos × 3 Escenarios)", 1)

    # Tabla M1
    add_heading_styled(doc, "8.1 Módulo 1 — Detención de Emergencia", 2)
    m1_rows = []
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        e, an, out = res['m1'][t]
        m1_rows.append([
            t,
            f"v0={e['v0']}, a={e['a']}, tr={e['tr']}, L={e['L']}",
            f"{an['d_total']:.4f} m / {an['t_total']:.2f} s",
            f"{out['RK4']['d_final']:.5f} m (Er={out['RK4']['err_rel']:.2e})",
            f"{out['RK2 (Heun)']['d_final']:.5f} m (Er={out['RK2 (Heun)']['err_rel']:.2e})",
            f"Bis:{out['Raíces']['Bisección']['iters']} | New:{out['Raíces']['Newton']['iters']} | Sec:{out['Raíces']['Secante']['iters']}"
        ])
    add_table_data(doc, ["Escenario", "Parámetros", "Analítica (d / t)", "RK4", "RK2 (Heun)", "Iter. Raíces v(t)=0"], m1_rows)

    # Tabla M2
    add_heading_styled(doc, "8.2 Módulo 2 — Deterioro Mecánico y Mantenimiento", 2)
    m2_rows = []
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        e, out = res['m2'][t]
        for m in ['Jacobi', 'Gauss-Seidel', 'LU', 'Gradiente conjugado', 'Bisección', 'Newton-Raphson', 'Secante']:
            r = out[m]
            lh = r['hist'][-1]
            m2_rows.append([
                t, m, f"{e['cond_A']:.2e}", str(r['iters']),
                "Sí" if r['converged'] else "No",
                f"{abs(lh['residual']):.2e}" if np.isfinite(lh['residual']) else "Inf",
                f"{lh['err_rel']:.2e}" if np.isfinite(lh['err_rel']) else "Inf"
            ])
    add_table_data(doc, ["Escenario", "Método", "κ(A)", "Iters", "Conv.", "Residuo", "Error Rel."], m2_rows)

    # Tabla M3
    add_heading_styled(doc, "8.3 Módulo 3 — Oscilaciones por Viento Lateral", 2)
    m3_rows = []
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        e, _, out = res['m3'][t]
        m3_rows.append([
            t,
            f"F0={e['F0']} N, ωf={e['omega_f']}, c={e['c']}",
            f"{out['RK4']['x_max']:.4f} m",
            f"RK2={out['RK2 (Heun)']['err_rel']:.2e} | RK4={out['RK4']['err_rel']:.2e}",
            f"{out['Trapecio']['integral']:.5f} (Er={out['Trapecio']['err_rel']:.2e})",
            f"{out['Simpson 1/3']['integral']:.5f} (Er={out['Simpson 1/3']['err_rel']:.2e})",
            f"{out['Romberg']['integral']:.5f} ({out['Romberg']['steps']} pasos)"
        ])
    add_table_data(doc, ["Escenario", "Parámetros", "x_max", "Error EDO", "Trapecio ∫x²dt", "Simpson 1/3", "Romberg"], m3_rows)

    # Tabla M4
    add_heading_styled(doc, "8.4 Módulo 4 — Reconstrucción de Sensores", 2)
    m4_rows = []
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        e, _, out = res['m4'][t]
        m4_rows.append([
            t, f"{len(e['t_nodes'])} nodos, σ={e['ruido_sigma']}",
            f"{out['Lagrange']['err_rel']:.2e}",
            f"{out['Newton']['err_rel']:.2e}",
            f"{out['Splines Cúbicos']['err_rel']:.2e}"
        ])
    add_table_data(doc, ["Escenario", "Configuración", "Er Lagrange", "Er Newton", "Er Splines C²"], m4_rows)

    # 9. TABLA DE ITERACIONES EJEMPLO
    add_heading_styled(doc, "9. Tablas de Iteraciones y Refinamiento (Muestras Verificadas)", 1)
    _, out_m2_norm = res['m2']['NORMAL']
    iter_rows = []
    for h in out_m2_norm['Newton-Raphson']['hist']:
        iter_rows.append(["M2 NORMAL - Newton", str(h['k']), f"{h['x'][0]:.8f}", f"{abs(h['residual']):.2e}", f"{h['err_rel']:.2e}"])
    for h in out_m2_norm['Gauss-Seidel']['hist'][:6]:
        iter_rows.append(["M2 NORMAL - Gauss-Seidel", str(h['k']), "[" + ", ".join(f"{v:.4f}" for v in h['x']) + "]", f"{h['residual']:.2e}", f"{h['err_rel']:.2e}"])
    add_table_data(doc, ["Método", "Paso k", "Aproximación", "Residuo", "Error Rel."], iter_rows)

    # 10. TEORÍA DE ERRORES TRANSVERSAL Y COMPARACIONES GRÁFICAS
    add_heading_styled(doc, "10. Teoría de Errores Transversal y Comparaciones Gráficas", 1)
    doc.add_paragraph(
        "En todos los módulos se calculan error absoluto E_a = ||x - x*||, error relativo protegido E_r = E_a / ||x*|| (evitando división por cero con umbral 1e-300), error porcentual E_p = 100·E_r, norma residual ||b - Ax|| o |f(x)|, y número de condición κ(A). Se demuestra experimentalmente la diferencia crítica entre:\n"
        "• Falta de convergencia algorítmica: Jacobi sobre Hilbert (ρ(T_J) = 2.5821 > 1) diverge exponencialmente en 72 pasos; Lagrange/Newton con 14 nodos equiespaciados sobre f(t)=1/(1+25t²) alcanzan 1140% de error en bordes (Runge).\n"
        "• Mal condicionamiento del problema: LU y Gradiente Conjugado resuelven Hilbert con residuo ~10⁻¹⁶, pero amplifican la perturbación δb=10⁻⁶ hasta E_r ≈ 1.92×10⁻³ por κ(A) = 1.55×10⁴.\n"
        "• Comparación gráfica: Cada simulación genera en la web dos gráficos interactivos en Chart.js: (1) Curva física del fenómeno junto a umbrales normativos (vía libre L, umbral D_u, gálibo ±0.80 m, o curvas interpoladas superpuestas) y (2) Curva de convergencia del error relativo en escala logarítmica Log₁₀."
    )

    # 11. CONCLUSIONES DOBLES POR MÓDULO
    add_heading_styled(doc, "11. Conclusiones Diferenciadas por Módulo (Numérica y del Problema)", 1)
    conclusiones = [
        ("Módulo 1 — Detención de Emergencia",
         "RK4 (O(h⁴)) logra errores de 1.19×10⁻⁵ en NORMAL y 1.39×10⁻⁹ en no lineal frente a RK2 (Heun, O(h²)), siempre que el paso respete exactamente la discontinuidad en t = t_r. Trapecio y Simpson 1/3 reproducen la distancia integrada. En MAL_CONDICIONADO (a(v)=a√(v/v0)), la raíz doble v'(t*)=0 degrada Newton de 1 a 15 iteraciones.",
         "En operación nominal (v0=5 m/s, a=1 m/s², t_r=1 s), la cabina frena en 17.50 m cumpliendo la vía libre de 20.0 m (+2.50 m de holgura). En ESTRÉS (v0=7 m/s, a=0.7 m/s², t_r=2 s), la distancia sube a 49.00 m, superando los 25.0 m de estación y evidenciando riesgo de colisión que obliga a reducir velocidad de aproximación."),
        ("Módulo 2 — Deterioro Mecánico y Mantenimiento",
         "En tridiagonal SPD (κ=2.36), Gauss-Seidel converge en 12 iteraciones frente a 21 de Jacobi (ρ_GS ≈ ρ_J²). En ESTRÉS (δb=3%), todos convergen con error de 1.06% dictado por la perturbación de entrada. En Hilbert (κ=1.55×10⁴), Jacobi diverge (ρ=2.58>1) y Gauss-Seidel se estanca en 5000 pasos, mientras LU y CG resuelven con error acotado por κ. Newton (5 iters) supera ampliamente a Bisección (27–41 iters).",
         "Bajo operación nominal, el cable alcanza el 60% de umbral de inspección (EN 12927) en 14.49 meses; bajo fatiga severa (ESTRÉS), la vida útil cae a 6.06 meses (-58%), obligando a duplicar ensayos electromagnéticos END. Una calibración mal condicionada de sensores distorsionaría la fecha real de mantenimiento."),
        ("Módulo 3 — Oscilaciones por Viento Lateral",
         "En régimen libre, RK4 coincide con la solución analítica subamortiguada con error 1.57×10⁻⁷ frente a 1.97×10⁻³ de RK2. En régimen forzado/resonante, RK2 acumula desfase hasta 3.95% mientras RK4 mantiene 1.92×10⁻⁵. Romberg alcanza precisión de referencia en 8 pasos acelerando Trapecio y Simpson 1/3 sobre ∫ x² dt.",
         "En vibración libre (0.50 m) el amortiguamiento contiene el balanceo dentro del gálibo seguro (0.80 m). En ESTRÉS (ωf=1.90 rad/s) llega a 0.963 m y en resonancia pura (ωf=ω0=2.0 rad/s, ζ≈0.0005) alcanza 2.005 m, exigiendo ralentización automática a 2 m/s o parada preventiva SCADA."),
        ("Módulo 4 — Reconstrucción de Sensores",
         "Sobre sin(t) sin ruido, Lagrange, Newton y Splines Cúbicos logran errores < 4×10⁻⁵. Sin embargo, con 14 nodos equiespaciados sobre la función de Runge, Lagrange y Newton divergen en los extremos con error de 1140%, mientras los Splines Cúbicos Naturales C² mantienen 0.19% mediante un sistema tridiagonal estable O(n).",
         "Reconstruir pérdidas de telemetría con polinomios globales provocaría falsas alarmas de sobretensión en el control del teleférico. Los Splines Cúbicos garantizan continuidad de posición, pendiente y curvatura física admisible; ante ruido elevado (σ=0.08) y gaps largos (>40%) se requiere además filtrado y redundancia de sensores.")
    ]
    for tit, c_num, c_prob in conclusiones:
        add_heading_styled(doc, tit, 2)
        add_callout(doc, "Conclusión Numérica (Algoritmos y Error)", c_num, border_color='1e3a8a', bg_color='eff6ff')
        add_callout(doc, "Conclusión del Problema Físico / Operativo", c_prob, border_color='16a34a', bg_color='f0fdf4')

    # 12. CONCLUSIÓN GLOBAL INTEGRADORA
    add_heading_styled(doc, "12. Conclusión Global Integradora", 1)
    doc.add_paragraph(
        "El desarrollo completo de SIMTELE-RISK demuestra que la modelación numérica confiable en ingeniería de transporte por cable exige articular rigor matemático, arquitectura de software verificable y criterio físico. Ningún método numérico es universalmente óptimo: Jacobi falla cuando falta dominancia diagonal, Newton pierde su convergencia cuadrática ante raíces múltiples, RK2 acumula error de fase en resonancia y los polinomios globales sufren el fenómeno de Runge. Contrastar cada algoritmo contra referencias analíticas, cuantificar κ(A) y radios espectrales, y almacenar cada corrida en un modelo relacional persistente sobre Turso/SQLite convierte la simulación en una herramienta auditable para la toma de decisiones de seguridad (vía libre, mantenimiento END, gálibo por viento e integridad de telemetría)."
    )

    # 13. LIMITACIONES, REFERENCIAS Y ANEXOS
    add_heading_styled(doc, "13. Limitaciones del Modelo", 1)
    doc.add_paragraph(
        "• Todos los parámetros son sintéticos y educativos; no reemplazan ensayos certificados ni PLCs reales.\n"
        "• M1 modela vía horizontal sin pendiente ni deslizamiento de mordazas; M2 usa un polinomio cuadrático estacionario; M3 considera oscilador plano 1-GDL sin acoplamiento torsional del cable; M4 evalúa señales unidimensionales deterministas más ruido gaussiano estacionario."
    )

    add_heading_styled(doc, "14. Referencias y Anexos con Enlaces", 1)
    doc.add_paragraph(
        "• Aplicación Web en Producción (Vercel + Turso DB): https://simtele-risk.vercel.app/\n"
        "• Norma Europea EN 12929-1: Requisitos de seguridad para instalaciones de transporte por cable destinadas a personas.\n"
        "• Norma Europea EN 12927: Requisitos de seguridad — Cables para instalaciones de transporte por cable.\n"
        "• Burden, R. L., & Faires, J. D. (2017). Análisis Numérico (10.ª ed.). Cengage Learning.\n"
        "• Chapra, S. C., & Canale, R. P. (2015). Métodos Numéricos para Ingenieros (7.ª ed.). McGraw-Hill.\n"
        "• Anexos en Repositorio: sql/schema.sql, docs/DER.md, src/test_metodos.py, src/test_persistencia.py."
    )

    out_docx = os.path.join(os.path.dirname(__file__), '..', 'docs', 'informe_final_semana3.docx')
    doc.save(out_docx)

    # Generar versión Markdown equivalente
    out_md = os.path.join(os.path.dirname(__file__), '..', 'docs', 'informe_final_semana3.md')
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write("# SIMTELE-RISK — Informe Final (Semana 3)\n\n")
        f.write("**Aplicación en Producción:** https://simtele-risk.vercel.app/  \n")
        f.write("**Base de Datos:** Turso (LibSQL) + SQLite local (`simtele.db`)  \n\n")
        f.write("> **Descargo Académico:** Simulación estrictamente educativa inspirada en Mi Teleférico (EN 12929-1 / EN 12927). Sin conexión a sistemas reales.\n\n")
        f.write("## 1. Resultados Verificados (4 Módulos × 3 Escenarios)\n\n")
        f.write("### Módulo 1 — Detención de Emergencia\n")
        f.write("| Escenario | Parámetros | Analítica (d / t) | RK4 | RK2 | Iter. Raíces |\n|---|---|---|---|---|---|\n")
        for row in m1_rows:
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n### Módulo 2 — Deterioro y Mantenimiento\n")
        f.write("| Escenario | Método | κ(A) | Iters | Conv. | Residuo | Error Rel. |\n|---|---|---|---|---|---|---|\n")
        for row in m2_rows:
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n### Módulo 3 — Oscilaciones por Viento\n")
        f.write("| Escenario | Parámetros | x_max | Error EDO | Trapecio ∫x²dt | Simpson 1/3 | Romberg |\n|---|---|---|---|---|---|---|\n")
        for row in m3_rows:
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n### Módulo 4 — Reconstrucción de Sensores\n")
        f.write("| Escenario | Configuración | Er Lagrange | Er Newton | Er Splines C² |\n|---|---|---|---|---|\n")
        for row in m4_rows:
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n## 2. Conclusiones Dobles por Módulo\n\n")
        for tit, c_num, c_prob in conclusiones:
            f.write(f"### {tit}\n- **Conclusión Numérica:** {c_num}\n- **Conclusión del Problema Físico:** {c_prob}\n\n")
        f.write("## 3. Conclusión Global Integradora\n\n")
        f.write(
            "La integración de los 4 módulos en 3 escenarios demuestra que la confiabilidad ingenieril depende tanto de la estabilidad, "
            "condicionamiento y orden de convergencia de los algoritmos numéricos como de su interpretación física en márgenes de seguridad "
            "(vía libre, vida útil END, gálibo por viento e integridad de telemetría), todo respaldado por persistencia verificable en Turso/SQLite.\n"
        )
    print(f"Generados exitosamente:\n - {out_docx}\n - {out_md}")


if __name__ == '__main__':
    build_reports()
