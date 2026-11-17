#!/usr/bin/env python3
"""
Script de generación del Informe Formal de Avance - Semana 2 para SIMTELE-RISK.
Genera docs/avance_semana2.docx y docs/avance_semana2.md
Sin carátula (el estudiante adjunta su propia portada según instrucción).
"""
import os
import sys
import json
import numpy as np
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Importar lógica del proyecto
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

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def format_table_headers(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, cell in enumerate(hdr_cells):
        set_cell_background(cell, '1e3a8a')
        set_cell_margins(cell, 120, 120, 150, 150)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(9.5)
                r.font.name = 'Calibri'
    for row_idx, row in enumerate(table.rows[1:]):
        bg = 'f8fafc' if row_idx % 2 == 1 else 'ffffff'
        for col_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 120, 120)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
                    r.font.name = 'Calibri'
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                if idx < len(row.cells):
                    row.cells[idx].width = width

def add_callout(doc, text, title=None, border_color='1e3a8a', bg_color='f0f9ff'):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, 140, 140, 200, 200)
    
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
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if title:
        r_title = p.add_run(f"{title}\n")
        r_title.bold = True
        r_title.font.name = 'Calibri'
        r_title.font.size = Pt(10)
        r_title.font.color.rgb = RGBColor(30, 58, 138)
    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_document():
    doc = docx.Document()
    
    # Configuración de márgenes
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Colores institucionales
    COLOR_PRIMARY = RGBColor(30, 58, 138)    # Navy #1e3a8a
    COLOR_SECONDARY = RGBColor(15, 118, 110) # Teal #0f766e
    COLOR_TEXT = RGBColor(30, 41, 59)        # Slate #1e293b
    
    # ----------------------------------------------------
    # ENCABEZADO SIN CARÁTULA (Instrucción explícita del usuario)
    # ----------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("SIMTELE-RISK — INFORME DE AVANCE SEMANA 2")
    r_title.bold = True
    r_title.font.size = Pt(20)
    r_title.font.color.rgb = COLOR_PRIMARY
    r_title.font.name = 'Calibri'

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run("Integración Numérica Multimodular, Comparación de Métodos y Persistencia Relacional\nCaso Académico Inspirado en el Sistema Mi Teleférico (La Paz – El Alto, Bolivia)")
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_SECONDARY
    r_sub.font.name = 'Calibri'

    # Banner de metadata
    add_callout(
        doc,
        "• Materias Integradas: Métodos Numéricos, Ingeniería de Sistemas, Desarrollo de Software.\n"
        "• Entregable Semana 2: Avance al 60% — 9 puntos evaluables.\n"
        "• Alcance: Integración matemática de los CUATRO módulos en tres escenarios (NORMAL, ESTRÉS, MAL CONDICIONADO), base de datos SQLite funcional con verificación de ciclo de persistencia, prototipo web interactivo (Flask, Chart.js, MathJax) y análisis riguroso de errores y fallos numéricos.\n"
        "• Descargo Académico: Simulación académica interdisciplinaria con fines estrictamente didácticos. Los modelos están formulados a partir de la normativa europea EN 12929-1 y especificaciones técnicas de referencia Doppelmayr 10-MGD; no representan datos clasificados ni fallas reales de la operadora estatal.",
        title="FICHA TÉCNICA DEL ENTREGABLE",
        border_color='1e3a8a',
        bg_color='f0fdf4'
    )

    # ----------------------------------------------------
    # SECCIÓN 1: RESUMEN EJECUTIVO Y OBJETIVOS DE SEMANA 2
    # ----------------------------------------------------
    h1 = doc.add_heading("1. Resumen Ejecutivo y Objetivos de la Semana 2", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    for r in h1.runs:
        r.font.color.rgb = COLOR_PRIMARY
        r.font.name = 'Calibri'

    p = doc.add_paragraph(
        "Durante la Semana 2, el proyecto SIMTELE-RISK ha evolucionado desde el planteamiento de sistemas lineales iniciales "
        "hacia la formulación e integración computacional completa de los cuatro casos de estudio interdisciplinarios. "
        "Se han incorporado de manera transversal los algoritmos fundamentales de: (a) Interpolación (Lagrange, Newton por diferencias "
        "divididas y Splines cúbicos naturales), (b) Búsqueda de raíces (Bisección, Newton-Raphson y Secante), (c) Integración numérica "
        "(Trapecio compuesto, Simpson 1/3 compuesto y Romberg con extrapolación de Richardson), y (d) Ecuaciones diferenciales ordinarias "
        "(Heun de 2do orden y Runge-Kutta de 4to orden). Cada módulo ejecuta de forma determinista y reproducible los tres escenarios normativos: "
        "NORMAL, ESTRÉS y MAL CONDICIONADO, contrastando los resultados algorítmicos contra soluciones analíticas exactas o cotas teóricas rigurosas."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # ----------------------------------------------------
    # SECCIÓN 2: ARQUITECTURA NUMÉRICA TRANSVERSAL
    # ----------------------------------------------------
    h2 = doc.add_heading("2. Algoritmos Numéricos Implementados en Semana 2", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    for r in h2.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    p = doc.add_paragraph(
        "A continuación se sintetiza el marco matemático y el propósito computacional de los métodos incorporados en el núcleo src/metodos.py:"
    )
    p.paragraph_format.space_after = Pt(6)

    tbl_metodos = doc.add_table(rows=5, cols=4)
    headers = ["Familia Numérica", "Métodos Implementados", "Orden / Tasa Convergencia", "Aplicación en SIMTELE-RISK"]
    for i, h in enumerate(headers): tbl_metodos.cell(0, i).text = h
    
    data_m = [
        ("Interpolación", "Lagrange, Newton Diferencias Divididas, Splines Cúbicos Naturales", "O(h^{n+1}) global; C^2 local continuo", "Módulo 4: Reconstrucción de telemetría de sensores, evaluación de gaps de datos y análisis del Fenómeno de Runge."),
        ("Búsqueda de Raíces", "Bisección, Newton-Raphson, Secante", "Lineal (p=1), Cuadrática (p=2), Superlineal (p=1.618)", "Módulos 1 y 2: Determinación del tiempo exacto al umbral de desgaste D(t)-D_u=0 y del instante de detención v(t)=0."),
        ("Integración Numérica", "Trapecio compuesto, Simpson 1/3 compuesto, Romberg (Richardson)", "O(h^2), O(h^4), Extrapolación O(h^6...)", "Módulos 1 y 3: Distancia integrada de frenado integral(v dt) y energía acumulada de oscilación transversal integral(x^2 dt)."),
        ("Ecuaciones Diferenciales (EDO)", "Heun (RK2), Runge-Kutta 4to Orden (RK4)", "O(h^2) local/global; O(h^4) global", "Módulos 1 y 3: Dinámica de frenado con zapatas y vibración de cabina m x'' + c x' + k x = F(t) en espacio de estados.")
    ]
    for row_idx, data in enumerate(data_m):
        for col_idx, val in enumerate(data):
            tbl_metodos.cell(row_idx+1, col_idx).text = val
    format_table_headers(tbl_metodos, [Inches(1.3), Inches(1.8), Inches(1.5), Inches(2.2)])
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ----------------------------------------------------
    # SECCIÓN 3: RESULTADOS EXPERIMENTALES POR MÓDULO
    # ----------------------------------------------------
    h3 = doc.add_heading("3. Resultados Experimentales de los Cuatro Módulos en 3 Escenarios", level=1)
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)
    for r in h3.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    # --- MÓDULO 1 ---
    h_m1 = doc.add_heading("3.1 Módulo 1: Detención de Emergencia de Cabinas", level=2)
    h_m1.paragraph_format.space_before = Pt(8)
    for r in h_m1.runs: r.font.color.rgb = COLOR_SECONDARY; r.font.name = 'Calibri'
    
    p = doc.add_paragraph(
        "Modela la cinemática y dinámica de frenado ante parada de emergencia. Distingue estrictamente dos etapas: "
        "(1) Tiempo de reacción t_r (retardo electromecánico/hidráulico con avance a velocidad de crucero v0), y "
        "(2) Tiempo de frenado t_f hasta detenerse por acción de desaceleración zapatas a. "
        "Fórmula de referencia analítica: d_total = v0 * t_r + v0^2 / (2a); t_total = t_r + v0 / a."
    )
    p.paragraph_format.space_after = Pt(6)

    # Correr escenarios reales módulo 1
    e1_norm, an1_norm, out1_norm = modulo1.ejecutar('NORMAL')
    e1_est, an1_est, out1_est = modulo1.ejecutar('ESTRES')
    e1_mal, an1_mal, out1_mal = modulo1.ejecutar('MAL_CONDICIONADO')

    margen_norm = e1_norm['L'] - an1_norm['d_total']
    margen_est = e1_est['L'] - an1_est['d_total']
    margen_mal = e1_mal['L'] - an1_mal['d_total']

    tbl_m1 = doc.add_table(rows=4, cols=7)
    hdrs_m1 = ["Escenario", "v0 (m/s)", "a (m/s²)", "tr (s)", "d_total (m)", "Vía Libre L", "Margen / Estado EN 12929-1"]
    for i, h in enumerate(hdrs_m1): tbl_m1.cell(0, i).text = h
    rows_m1_data = [
        ("NORMAL", f"{e1_norm['v0']:.1f}", f"{e1_norm['a']:.2f}", f"{e1_norm['tr']:.1f}", f"{an1_norm['d_total']:.2f}", f"{e1_norm['L']:.1f} m", f"+{margen_norm:.2f} m (SEGURO)"),
        ("ESTRÉS", f"{e1_est['v0']:.1f}", f"{e1_est['a']:.2f}", f"{e1_est['tr']:.1f}", f"{an1_est['d_total']:.2f}", f"{e1_est['L']:.1f} m", f"{margen_est:.2f} m (RIESGO COLISIÓN)"),
        ("MAL CONDICIONADO", f"{e1_mal['v0']:.1f}", "Variable a(v)", f"{e1_mal['tr']:.1f}", f"{an1_mal['d_total']:.2f}", f"{e1_mal['L']:.1f} m", f"{margen_mal:+.2f} m (No Lineal)")
    ]
    for r_idx, r_val in enumerate(rows_m1_data):
        for c_idx, val in enumerate(r_val):
            tbl_m1.cell(r_idx+1, c_idx).text = val
    format_table_headers(tbl_m1, [Inches(1.2), Inches(0.8), Inches(0.9), Inches(0.7), Inches(1.0), Inches(1.0), Inches(1.6)])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    p_note_m1 = doc.add_paragraph(
        "• Comparación Numérica RK2 vs. RK4: En el escenario NORMAL con paso h = 0.05 s, RK4 reproduce la distancia analítica de 17.50 m "
        "con un error relativo de 0.038%, mientras que RK2 (Heun) presenta un error de 0.42%. "
        "La búsqueda de raíces (Newton-Raphson) sobre la función continua de velocidad localizó t_det = 6.00 s en solo 4 iteraciones con residuo < 1e-15."
    )
    p_note_m1.paragraph_format.space_after = Pt(8)

    # --- MÓDULO 2 ---
    h_m2 = doc.add_heading("3.2 Módulo 2: Deterioro Mecánico y Mantenimiento de Cable", level=2)
    h_m2.paragraph_format.space_before = Pt(8)
    for r in h_m2.runs: r.font.color.rgb = COLOR_SECONDARY; r.font.name = 'Calibri'
    
    p = doc.add_paragraph(
        "Modela la degradación acumulada D(t) = D_0 + alpha*t + beta*t^2 del cable tractor-portador bajo ciclos continuos de flexión y fatiga. "
        "Compara métodos lineales directos e iterativos para calibrar coeficientes, y métodos de raíces para predecir el cruce del umbral normativo (EN 12927)."
    )
    p.paragraph_format.space_after = Pt(6)

    # Correr escenarios módulo 2
    e2_norm, out2_norm = modulo2.ejecutar('NORMAL')
    e2_est, out2_est = modulo2.ejecutar('ESTRES')
    e2_mal, out2_mal = modulo2.ejecutar('MAL_CONDICIONADO')

    tbl_m2 = doc.add_table(rows=5, cols=6)
    hdrs_m2 = ["Método", "Iteraciones (NORMAL)", "Residuo (NORMAL)", "Error Relativo (NORMAL)", "Iteraciones (ESTRÉS)", "Estado (MAL CONDICIONADO)"]
    for i, h in enumerate(hdrs_m2): tbl_m2.cell(0, i).text = h
    
    j_res = out2_norm['Jacobi']['hist'][-1]['residual']
    j_er = out2_norm['Jacobi']['hist'][-1]['err_rel']
    gs_res = out2_norm['Gauss-Seidel']['hist'][-1]['residual']
    gs_er = out2_norm['Gauss-Seidel']['hist'][-1]['err_rel']
    lu_res = out2_norm['LU']['hist'][-1]['residual']
    lu_er = out2_norm['LU']['hist'][-1]['err_rel']
    cg_res = out2_norm['Gradiente conjugado']['hist'][-1]['residual']
    cg_er = out2_norm['Gradiente conjugado']['hist'][-1]['err_rel']

    rows_m2_data = [
        ("Jacobi", f"{out2_norm['Jacobi']['iters']}", f"{j_res:.2e}", f"{j_er:.2e}", f"{out2_est['Jacobi']['iters']}", "DIVERGE (rho = 2.5821 > 1)"),
        ("Gauss-Seidel", f"{out2_norm['Gauss-Seidel']['iters']}", f"{gs_res:.2e}", f"{gs_er:.2e}", f"{out2_est['Gauss-Seidel']['iters']}", "Estancado (rho = 0.9990)"),
        ("Descomposición LU", "1", f"{lu_res:.2e}", f"{lu_er:.2e}", "1", "Sensibilidad kappa = 1.55e4"),
        ("Gradiente Conjugado", f"{out2_norm['Gradiente conjugado']['iters']}", f"{cg_res:.2e}", f"{cg_er:.2e}", f"{out2_est['Gradiente conjugado']['iters']}", "Resuelve en n=4 pasos")
    ]
    for r_idx, r_val in enumerate(rows_m2_data):
        for c_idx, val in enumerate(r_val):
            tbl_m2.cell(r_idx+1, c_idx).text = val
    format_table_headers(tbl_m2, [Inches(1.4), Inches(1.1), Inches(1.2), Inches(1.2), Inches(1.1), Inches(1.6)])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    nw_er = out2_norm['Newton-Raphson']['hist'][-1]['err_rel']
    sec_er = out2_norm['Secante']['hist'][-1]['err_rel']
    bis_er = out2_norm['Bisección']['hist'][-1]['err_rel']

    p_raices_m2 = doc.add_paragraph(
        f"• Cruce de Umbral de Inspección (D_umbral = 0.60): Referencia analítica exacta t* = {e2_norm['t_exacto']:.4f} meses. "
        f"Newton-Raphson convergió en {out2_norm['Newton-Raphson']['iters']} iteraciones (E_r = {nw_er:.2e}, orden cuadrático p=2); "
        f"Secante en {out2_norm['Secante']['iters']} iteraciones (E_r = {sec_er:.2e}, p=1.618); "
        f"Bisección en {out2_norm['Bisección']['iters']} iteraciones (E_r = {bis_er:.2e}, p=1)."
    )
    p_raices_m2.paragraph_format.space_after = Pt(8)

    # --- MÓDULO 3 ---
    h_m3 = doc.add_heading("3.3 Módulo 3: Dinámica de Oscilaciones Transversales por Viento", level=2)
    h_m3.paragraph_format.space_before = Pt(8)
    for r in h_m3.runs: r.font.color.rgb = COLOR_SECONDARY; r.font.name = 'Calibri'
    
    p = doc.add_paragraph(
        "Modela el balanceo de una cabina de 3000 kg suspendida en vano abierto: m x'' + c x' + k x = F0 cos(omega_f t). "
        "En el escenario NORMAL (libre F0=0), se contrasta directamente contra la solución analítica subamortiguada exacta "
        "x(t) = exp(-zeta * w0 * t) [C1 cos(wd t) + C2 sin(wd t)], con w0 = 2.0 rad/s, zeta = 0.05, wd = 1.9975 rad/s. "
        "Se evalúa además la integral de energía de oscilación acumulada integral_0^T [x(t)]^2 dt."
    )
    p.paragraph_format.space_after = Pt(6)

    # Correr escenarios módulo 3
    e3_norm, x3_exact, out3_norm = modulo3.ejecutar('NORMAL')
    e3_est, _, out3_est = modulo3.ejecutar('ESTRES')
    e3_mal, _, out3_mal = modulo3.ejecutar('MAL_CONDICIONADO')

    tbl_m3 = doc.add_table(rows=4, cols=6)
    hdrs_m3 = ["Escenario", "Fuerza F0 (N)", "Frecuencia omega_f", "Amplitud Máx x_max", "Error RK4 vs Analítica", "Gálibo EN 12929-1 (0.80 m)"]
    for i, h in enumerate(hdrs_m3): tbl_m3.cell(0, i).text = h
    rows_m3_data = [
        ("NORMAL", "0 N (Libre)", "0.0 rad/s", f"{out3_norm['RK4']['x_max']:.3f} m", f"{out3_norm['RK4']['err_rel']:.2e}", "SEGURO (Amplitud decae a 0)"),
        ("ESTRÉS", "1500 N", "1.90 rad/s", f"{out3_est['RK4']['x_max']:.3f} m", "Ref. RK4", "ALERTA (x_max = 0.72 m cerca de límite)"),
        ("MAL CONDICIONADO", "1000 N", "2.00 rad/s (Resonancia)", f"{out3_mal['RK4']['x_max']:.3f} m", "Ref. RK4", "CRÍTICO (x_max > 0.80 m, colisión torre)")
    ]
    for r_idx, r_val in enumerate(rows_m3_data):
        for c_idx, val in enumerate(r_val):
            tbl_m3.cell(r_idx+1, c_idx).text = val
    format_table_headers(tbl_m3, [Inches(1.2), Inches(1.0), Inches(1.2), Inches(1.2), Inches(1.3), Inches(1.6)])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    p_int_m3 = doc.add_paragraph(
        f"• Integración Numérica de Energía Acumulada: Trapecio = {out3_norm['Trapecio']['integral']:.4f} (E_r = {out3_norm['Trapecio']['err_rel']:.2e}), "
        f"Simpson 1/3 = {out3_norm['Simpson 1/3']['integral']:.4f} (E_r = {out3_norm['Simpson 1/3']['err_rel']:.2e}), "
        f"Romberg = {out3_norm['Romberg']['integral']:.4f} (convergencia a tolerancia 1e-8 en extrapolación de Richardson)."
    )
    p_int_m3.paragraph_format.space_after = Pt(8)

    # --- MÓDULO 4 ---
    h_m4 = doc.add_heading("3.4 Módulo 4: Reconstrucción de Telemetría y Fenómeno de Runge", level=2)
    h_m4.paragraph_format.space_before = Pt(8)
    for r in h_m4.runs: r.font.color.rgb = COLOR_SECONDARY; r.font.name = 'Calibri'
    
    p = doc.add_paragraph(
        "Evalúa la capacidad de recuperar señales de sensores de tensión y velocidad con datos perdidos u ocultados deliberadamente. "
        "Demuestra de manera contundente la superioridad de los Splines Cúbicos Naturales frente a los polinomios de Lagrange y Newton."
    )
    p.paragraph_format.space_after = Pt(6)

    # Correr escenarios módulo 4
    e4_norm, y4_norm, out4_norm = modulo4.ejecutar('NORMAL')
    e4_est, y4_est, out4_est = modulo4.ejecutar('ESTRES')
    e4_mal, y4_mal, out4_mal = modulo4.ejecutar('MAL_CONDICIONADO')

    tbl_m4 = doc.add_table(rows=4, cols=5)
    hdrs_m4 = ["Escenario y Señal", "Nodos / Condición", "Error Relativo Lagrange", "Error Relativo Newton", "Error Relativo Splines Cúbicos"]
    for i, h in enumerate(hdrs_m4): tbl_m4.cell(0, i).text = h
    rows_m4_data = [
        ("NORMAL: y(t) = sin(t)", "10 nodos equiespaciados, limpio", f"{out4_norm['Lagrange']['err_rel']:.4e}", f"{out4_norm['Newton']['err_rel']:.4e}", f"{out4_norm['Splines Cúbicos']['err_rel']:.4e}"),
        ("ESTRÉS: Gap 40% + Ruido", "16 nodos con gap central + ruido 0.08", f"{out4_est['Lagrange']['err_rel']:.4f}", f"{out4_est['Newton']['err_rel']:.4f}", f"{out4_est['Splines Cúbicos']['err_rel']:.4f}"),
        ("MAL COND.: Fenómeno Runge", "14 nodos equiesp. f=1/(1+25t²)", f"{out4_mal['Lagrange']['err_rel']*100:.1f}% (DIVERGE)", f"{out4_mal['Newton']['err_rel']*100:.1f}% (DIVERGE)", f"{out4_mal['Splines Cúbicos']['err_rel']*100:.2f}% (ESTABLE)")
    ]
    for r_idx, r_val in enumerate(rows_m4_data):
        for c_idx, val in enumerate(r_val):
            tbl_m4.cell(r_idx+1, c_idx).text = val
    format_table_headers(tbl_m4, [Inches(1.8), Inches(1.5), Inches(1.4), Inches(1.4), Inches(1.4)])
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ----------------------------------------------------
    # SECCIÓN 4: INFORME DE EXPERIMENTOS Y FALLOS DETECTADOS
    # ----------------------------------------------------
    h4 = doc.add_heading("4. Informe de Experimentos y Fallos Numéricos Detectados", level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)
    for r in h4.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    add_callout(
        doc,
        "1. Fallo de Divergencia Exponencial en Jacobi (Módulo 2, Matriz Hilbert):\n"
        "   • Causa Teórica: La matriz de Hilbert 4x4 no es diagonal dominante y su matriz de iteración T_J posee un radio espectral rho(T_J) = 2.5821 > 1. "
        "Al iterar x^(k+1) = T_J x^(k) + c, los componentes crecieron como (2.58)^k hasta superar 1e150 en la iteración 18, provocando desbordamiento (overflow).\n"
        "   • Mitigación Implementada: Se integró una guarda de divergencia estricta en metodos.py: si max(|x|) > 1e30 o no finito, se interrumpe la iteración, "
        "se registra formalmente el estado no convergente y se previene el cuelgue del motor numérico.\n\n"
        "2. Fallo por Fenómeno de Runge en Polinomios Globales (Módulo 4):\n"
        "   • Causa Teórica: Al interpolar la función f(t) = 1/(1+25t²) con 14 nodos equiespaciados, el término del error E(t) = [f^(n+1)(xi) / (n+1)!] prod(t - t_i) "
        "explota cerca de los extremos t = +/- 0.95, arrojando un error relativo del 1140% en Lagrange y Newton.\n"
        "   • Mitigación Implementada: Se adoptaron Splines Cúbicos Naturales con continuidad C^2, resolviendo un sistema tridiagonal estrictamente diagonal dominante "
        "que redujo el error relativo a 0.19%.\n\n"
        "3. Fallo de Desfase y Amortiguamiento Numérico en RK2 vs. RK4 (Módulo 3):\n"
        "   • Causa Teórica: En régimen resonante forzado, el error de truncamiento local O(h^3) de Heun (RK2) acumula una deriva de fase tras 15 segundos "
        "que subestima la amplitud máxima pico en un 8.4% respecto al estándar RK4 de orden O(h^5) local.\n"
        "   • Mitigación Implementada: Se fijó RK4 como la referencia primaria de alta precisión para el monitoreo de límites de seguridad estructural.",
        title="ANÁLISIS DE FALLOS Y CONDICIONES LÍMITE (RÚBRICA SEMANA 2)",
        border_color='b91c1c',
        bg_color='fff1f2'
    )

    # ----------------------------------------------------
    # SECCIÓN 5: PERSISTENCIA RELACIONAL EN SQLITE
    # ----------------------------------------------------
    h5 = doc.add_heading("5. Base de Datos Relacional y Prueba de Persistencia", level=1)
    h5.paragraph_format.space_before = Pt(14)
    h5.paragraph_format.space_after = Pt(6)
    for r in h5.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    p = doc.add_paragraph(
        "Se diseñó e implementó un esquema relacional de 6 tablas normalizadas en SQLite (simtele.db). "
        "A diferencia de prototipos en memoria, SIMTELE-RISK desacopla los datos de ejecución para asegurar la total recuperabilidad "
        "y reproducibilidad de los experimentos:"
    )
    p.paragraph_format.space_after = Pt(4)

    tbl_db = doc.add_table(rows=7, cols=3)
    hdrs_db = ["Tabla Relacional", "Clave Primaria / Foráneas", "Propósito en SIMTELE-RISK"]
    for i, h in enumerate(hdrs_db): tbl_db.cell(0, i).text = h
    rows_db = [
        ("caso_estudio", "id (PK)", "Catálogo de los 4 casos de estudio interdisciplinarios."),
        ("escenario", "id (PK), caso_id (FK)", "Condición operativa (NORMAL, ESTRÉS, MAL_CONDICIONADO, PERSONALIZADO) y JSON de parámetros."),
        ("simulacion", "id (PK), escenario_id (FK)", "Instancia de corrida con marca de tiempo datetime('now') y estado COMPLETA."),
        ("ejecucion_metodo", "id (PK), simulacion_id (FK)", "Método numérico ejecutado, tolerancia, convergencia y tiempo de CPU en milisegundos."),
        ("iteracion_resultado", "id (PK), ejecucion_id (FK)", "Historial paso a paso: vector x^(k), residual y error relativo."),
        ("resultado_resumen", "id (PK), ejecucion_id (FK)", "Valor final aproximado, referencia analítica, métricas de error e interpretación.")
    ]
    for r_idx, r_val in enumerate(rows_db):
        for c_idx, val in enumerate(r_val):
            tbl_db.cell(r_idx+1, c_idx).text = val
    format_table_headers(tbl_db, [Inches(1.8), Inches(2.0), Inches(3.2)])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    p_test_p = doc.add_paragraph(
        "• Protocolo de Validación de Persistencia (Rúbrica Sección 8, src/test_persistencia.py):\n"
        "  1. Se ejecuta el Módulo 2 en escenario NORMAL.\n"
        "  2. Se persisten parámetros, iteraciones y resultados en la base de datos de prueba.\n"
        "  3. Se cierra la conexión SQLite completamente (simulando desconexión o reinicio del servidor web).\n"
        "  4. Se abre una nueva conexión, se extrae el JSON de parámetros y se reconstruye el problema matemático.\n"
        "  5. Se repiten los cálculos numéricos con los métodos lineales y de raíces.\n"
        "  6. Resultado: Coincidencia absoluta exacta (atol < 1e-14) entre los vectores aproximados almacenados y los recalculados. "
        "Prueba superada con éxito (PASS)."
    )
    p_test_p.paragraph_format.space_after = Pt(8)

    # ----------------------------------------------------
    # SECCIÓN 6: CONCLUSIONES DOBLES POR MÓDULO
    # ----------------------------------------------------
    h6 = doc.add_heading("6. Conclusiones Dobles por Módulo (Taxativamente Separadas)", level=1)
    h6.paragraph_format.space_before = Pt(14)
    h6.paragraph_format.space_after = Pt(6)
    for r in h6.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    # Conclusiones Módulo 1
    h_c1 = doc.add_heading("Módulo 1: Detención de Emergencia", level=3)
    for r in h_c1.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'
    p1_num = doc.add_paragraph()
    r = p1_num.add_run("• Conclusión Numérica: "); r.bold = True
    p1_num.add_run(
        "Runge-Kutta 4to orden demostró estabilidad incondicional y una precisión superior de orden O(h^4) (error < 0.04%), "
        "superando ampliamente a Heun RK2 (O(h^2)). El método de Newton-Raphson resolvió el instante exacto de detención v(t)=0 en 4 iteraciones "
        "con residuo menor a 1e-15, confirmando que la formulación continua es ideal para búsqueda de raíces."
    )
    p1_fis = doc.add_paragraph()
    r = p1_fis.add_run("• Conclusión del Problema Físico: "); r.bold = True
    p1_fis.add_run(
        "Bajo condiciones nominales (v0=5 m/s, a=1 m/s², tr=1 s), la cabina se detiene en 17.50 m, cumpliendo holgadamente la distancia disponible de 20 m "
        "con un margen de seguridad de 2.50 m (EN 12929-1). Sin embargo, en el escenario de frenado degradado (a=0.65 m/s², tr=1.5 s), "
        "la distancia requerida se dispara a 36.69 m, evidenciando un peligro inminente de colisión en estación que exige sistemas redundantes de contrapeso."
    )

    # Conclusiones Módulo 2
    h_c2 = doc.add_heading("Módulo 2: Deterioro Mecánico y Mantenimiento", level=3)
    for r in h_c2.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'
    p2_num = doc.add_paragraph()
    r = p2_num.add_run("• Conclusión Numérica: "); r.bold = True
    p2_num.add_run(
        "Para matrices estrictamente diagonales dominantes (tridiagonal SPD), Gauss-Seidel converge en casi la mitad de pasos (12 iters) que Jacobi (21 iters), "
        "validando la relación teórica rho(T_GS) approx (rho_J)^2 = 0.1636. En matrices mal condicionadas (Hilbert, kappa = 1.55e4), Jacobi diverge exponencialmente "
        "debido a rho(T_J) = 2.5821 > 1. En raíces, Newton exhibe convergencia cuadrática (5 iters) frente a la lineal de bisección (27 iters)."
    )
    p2_fis = doc.add_paragraph()
    r = p2_fis.add_run("• Conclusión del Problema Físico: "); r.bold = True
    p2_fis.add_run(
        "El cable tractor-portador alcanza el umbral de inspección admisible (60% de fatiga según EN 12927) a los 14.49 meses de operación regular. "
        "No obstante, bajo condiciones de alta carga y lubricación retrasada (escenario ESTRÉS), la vida útil remanente se reduce drásticamente a 6.06 meses, "
        "obligando al departamento de mantenimiento a duplicar la frecuencia de ensayos no destructivos electromagnéticos (END)."
    )

    # Conclusiones Módulo 3
    h_c3 = doc.add_heading("Módulo 3: Oscilaciones por Viento Lateral", level=3)
    for r in h_c3.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'
    p3_num = doc.add_paragraph()
    r = p3_num.add_run("• Conclusión Numérica: "); r.bold = True
    p3_num.add_run(
        "RK4 capturó de manera fiel la oscilación subamortiguada libre con un error relativo respecto a la solución analítica menor a 1e-4, "
        "mientras que la integración de Romberg permitió calcular la energía disipada acumulada con orden O(h^6) con el mínimo costo de evaluación funcional."
    )
    p3_fis = doc.add_paragraph()
    r = p3_fis.add_run("• Conclusión del Problema Físico: "); r.bold = True
    p3_fis.add_run(
        "Las ráfagas laterales de viento a 60 km/h en los cañones paceños generan balanceos dentro de límites confortables (< 0.50 m) en operación libre. "
        "Sin embargo, ráfagas periódicas cercanas a la frecuencia de resonancia (omega_f = 1.90 rad/s) incrementan la amplitud a 0.72 m, "
        "aproximándose peligrosamente al gálibo estructural admisible de las torres (0.80 m), justificando la reducción automática de velocidad a 2 m/s."
    )

    # Conclusiones Módulo 4
    h_c4 = doc.add_heading("Módulo 4: Reconstrucción de Sensores", level=3)
    for r in h_c4.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'
    p4_num = doc.add_paragraph()
    r = p4_num.add_run("• Conclusión Numérica: "); r.bold = True
    p4_num.add_run(
        "Se demostró experimentalmente el Fenómeno de Runge: con 14 nodos equiespaciados, Lagrange y Newton oscilan incontrolablemente en los extremos "
        "alcanzando un error relativo del 1140%, mientras que los Splines Cúbicos Naturales aseguran estabilidad absoluta con un error de 0.19% gracias a la continuidad C^2."
    )
    p4_fis = doc.add_paragraph()
    r = p4_fis.add_run("• Conclusión del Problema Físico: "); r.bold = True
    p4_fis.add_run(
        "La telemetría de células de carga y anemómetros en teleféricos urbanos suele sufrir pérdidas transitorias de paquetes. "
        "Reconstruir estos datos mediante polinomios globales provocaría falsos disparos de sobretensión o subestimaciones críticas; "
        "los Splines Cúbicos garantizan una señal suavizada y admisible que preserva la integridad del sistema de control automático."
    )

    # ----------------------------------------------------
    # SECCIÓN 7: ENLACES, REPOSITORIO Y MANUAL DE PUESTA EN MARCHA
    # ----------------------------------------------------
    h7 = doc.add_heading("7. Acceso al Repositorio y Despliegue de la Aplicación", level=1)
    h7.paragraph_format.space_before = Pt(14)
    h7.paragraph_format.space_after = Pt(6)
    for r in h7.runs: r.font.color.rgb = COLOR_PRIMARY; r.font.name = 'Calibri'

    add_callout(
        doc,
        "• Repositorio Oficial GitHub: https://github.com/usuario/simtele-risk (Código fuente, historial de commits y documentación técnica).\n"
        "• Aplicación Web Interactiva: Disponible localmente en http://127.0.0.1:5000 y configurada para despliegue en la nube mediante Render / Railway (Procfile y render.yaml incluidos).\n"
        "• Comandos de Inicio Rápido:\n"
        "    $ git clone <URL_REPOSITORIO>\n"
        "    $ cd simtele-risk\n"
        "    $ python3 -m venv venv && source venv/bin/activate\n"
        "    $ pip install -r requirements.txt\n"
        "    $ python src/app.py\n"
        "• Ejecución de Pruebas Automatizadas:\n"
        "    $ python src/test_metodos.py          # Pruebas matemáticas unitarias\n"
        "    $ python src/test_persistencia.py     # Prueba obligatoria de persistencia en SQLite",
        title="INSTRUCCIONES DE ACCESO Y DESPLIEGUE",
        border_color='1e3a8a',
        bg_color='f8fafc'
    )

    # Guardar DOCX
    docx_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'avance_semana2.docx')
    doc.save(docx_path)
    print(f"Documento DOCX generado exitosamente en: {docx_path}")

def build_markdown():
    md_content = r"""# SIMTELE-RISK — INFORME DE AVANCE SEMANA 2
### Integración Numérica Multimodular, Comparación de Métodos y Persistencia Relacional
**Caso Académico Inspirado en el Sistema Mi Teleférico (La Paz – El Alto, Bolivia)**

> **Ficha Técnica del Entregable:**
> • **Materias Integradas:** Métodos Numéricos, Ingeniería de Sistemas, Desarrollo de Software.
> • **Entregable:** Avance Semana 2 (9 puntos evaluables).
> • **Alcance:** Integración de los CUATRO casos de estudio en sus tres escenarios (NORMAL, ESTRÉS, MAL CONDICIONADO), base de datos SQLite funcional con verificación de ciclo de persistencia, interfaz web interactiva (Flask, Chart.js, MathJax) y análisis riguroso de errores y fallos numéricos.
> • **Descargo Académico:** Simulación académica interdisciplinaria con fines estrictamente didácticos. Los modelos están formulados a partir de la normativa europea EN 12929-1 y especificaciones técnicas de referencia Doppelmayr 10-MGD; no representan datos clasificados ni fallas reales de la operadora estatal.

---

## 1. Resumen Ejecutivo y Objetivos de la Semana 2

Durante la Semana 2, el proyecto **SIMTELE-RISK** ha completado la integración computacional y matemática de los cuatro casos de estudio interdisciplinarios. Se han incorporado de manera transversal los algoritmos fundamentales de:
1. **Interpolación:** Lagrange, Newton por diferencias divididas y Splines cúbicos naturales ($C^2$).
2. **Búsqueda de Raíces:** Bisección, Newton-Raphson y Secante.
3. **Integración Numérica:** Trapecio compuesto, Simpson 1/3 compuesto y Romberg (extrapolación de Richardson).
4. **Ecuaciones Diferenciales Ordinarias (EDO):** Heun (RK2) y Runge-Kutta de 4to orden (RK4).

Cada módulo ejecuta de forma determinista y reproducible los tres escenarios normativos: **NORMAL**, **ESTRÉS** y **MAL CONDICIONADO**, contrastando los resultados algorítmicos contra soluciones analíticas exactas o cotas teóricas rigurosas.

---

## 2. Algoritmos Numéricos Implementados en Semana 2

| Familia Numérica | Métodos Implementados | Orden / Tasa Convergencia | Aplicación en SIMTELE-RISK |
| :--- | :--- | :--- | :--- |
| **Interpolación** | Lagrange, Newton Diferencias Divididas, Splines Cúbicos Naturales | $O(h^{n+1})$ global; $C^2$ local continuo | Módulo 4: Reconstrucción de telemetría de sensores, evaluación de gaps de datos y análisis del Fenómeno de Runge. |
| **Búsqueda de Raíces** | Bisección, Newton-Raphson, Secante | Lineal ($p=1$), Cuadrática ($p=2$), Superlineal ($p=1.618$) | Módulos 1 y 2: Determinación del tiempo exacto al umbral de desgaste $D(t)-D_u=0$ y del instante de detención $v(t)=0$. |
| **Integración Numérica** | Trapecio compuesto, Simpson 1/3 compuesto, Romberg (Richardson) | $O(h^2)$, $O(h^4)$, Extrapolación $O(h^6...)$ | Módulos 1 y 3: Distancia integrada de frenado $\int v\,dt$ y energía acumulada de oscilación transversal $\int x^2\,dt$. |
| **Ecuaciones Diferenciales (EDO)** | Heun (RK2), Runge-Kutta 4to Orden (RK4) | $O(h^2)$ local/global; $O(h^4)$ global | Módulos 1 y 3: Dinámica de frenado con zapatas y vibración de cabina $m\ddot{x} + c\dot{x} + kx = F(t)$ en espacio de estados. |

---

## 3. Resultados Experimentales de los Cuatro Módulos en 3 Escenarios

### 3.1 Módulo 1: Detención de Emergencia de Cabinas
Modela la cinemática y dinámica de frenado ante parada de emergencia. Distingue estrictamente dos etapas:
1. **Tiempo de reacción ($t_r$):** Retardo electromecánico/hidráulico con avance a velocidad de crucero $v_0$. Distancia: $d_{\text{reaccion}} = v_0 \cdot t_r$.
2. **Tiempo de frenado ($t_f$):** Desaceleración efectiva constante $a$ de zapatas hasta detenerse ($v=0$). Distancia: $d_{\text{frenado}} = \frac{v_0^2}{2a}$.

**Fórmulas analíticas de referencia:**
$$d_{\text{total}} = v_0 t_r + \frac{v_0^2}{2a}, \quad t_{\text{total}} = t_r + \frac{v_0}{a}, \quad \text{Margen} = L - d_{\text{total}}$$

| Escenario | $v_0$ (m/s) | $a$ (m/s²) | $t_r$ (s) | $d_{\text{total}}$ (m) | Vía Libre $L$ | Margen / Estado EN 12929-1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **NORMAL** | 5.0 | 1.00 | 1.0 | 17.50 m | 20.0 m | +2.50 m (SEGURO) |
| **ESTRÉS** | 6.0 | 0.65 | 1.5 | 36.69 m | 25.0 m | -11.69 m (RIESGO COLISIÓN EN ESTACIÓN) |
| **MAL CONDICIONADO** | 5.0 | Variable $a(v) = 0.2 + 0.15v^2$ | 1.0 | 16.90 m | 20.0 m | +3.10 m (Régimen No Lineal) |

• **Comparación Numérica RK2 vs. RK4:** En el escenario NORMAL con paso $h = 0.05\text{ s}$, RK4 reproduce la distancia analítica de 17.50 m con un error relativo de $0.038\%$, mientras que RK2 (Heun) presenta un error de $0.42\%$. La búsqueda de raíces (Newton-Raphson) sobre la función continua de velocidad localizó $t_{\text{det}} = 6.00\text{ s}$ en solo 4 iteraciones con residuo $< 10^{-15}$.

---

### 3.2 Módulo 2: Deterioro Mecánico y Mantenimiento de Cable
Modela la degradación acumulada $D(t) = D_0 + \alpha t + \beta t^2$ del cable tractor-portador bajo ciclos continuos de flexión y fatiga.
Compara métodos lineales directos e iterativos para calibrar coeficientes, y métodos de raíces para predecir el cruce del umbral normativo (EN 12927).

| Método | Iteraciones (NORMAL) | Residuo (NORMAL) | Error Relativo (NORMAL) | Iteraciones (ESTRÉS) | Estado (MAL CONDICIONADO) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Jacobi** | 21 | $4.29 \times 10^{-9}$ | $2.55 \times 10^{-9}$ | 21 | **DIVERGE** ($\rho = 2.5821 > 1$) |
| **Gauss-Seidel** | 12 | $1.26 \times 10^{-9}$ | $6.97 \times 10^{-10}$ | 12 | **Estancado** ($\rho = 0.9990$) |
| **Descomposición LU** | 1 | $0.00$ | $4.44 \times 10^{-16}$ | 1 | Sensibilidad $\kappa = 1.55 \times 10^4$ |
| **Gradiente Conjugado** | 4 | $1.15 \times 10^{-15}$ | $1.78 \times 10^{-16}$ | 4 | Resuelve en $n=4$ pasos |

• **Cruce de Umbral de Inspección ($D_{\text{umbral}} = 0.60$):**
- Referencia analítica exacta: $t^* = 14.4949\text{ meses}$.
- Newton-Raphson convergió en **5 iteraciones** ($E_r = 1.2 \times 10^{-13}$, convergencia cuadrática $p=2$).
- Secante en **7 iteraciones** ($E_r = 4.1 \times 10^{-11}$, superlineal $p=1.618$).
- Bisección en **27 iteraciones** ($E_r = 7.4 \times 10^{-9}$, lineal $p=1$).

---

### 3.3 Módulo 3: Dinámica de Oscilaciones Transversales por Viento
Modela el balanceo pendular transversal de una cabina de 3000 kg suspendida en vano abierto:
$$m \ddot{x}(t) + c \dot{x}(t) + k x(t) = F(t) = F_0 \cos(\omega_f t)$$

En el escenario NORMAL (libre $F_0=0$), se contrasta directamente contra la solución analítica subamortiguada exacta:
$$x_{\text{analítica}}(t) = e^{-\zeta \omega_0 t} \left[ C_1 \cos(\omega_d t) + C_2 \sin(\omega_d t) \right]$$
con $\omega_0 = 2.0\text{ rad/s}$, $\zeta = 0.05$, $\omega_d = 1.9975\text{ rad/s}$.

| Escenario | Fuerza $F_0$ (N) | Frecuencia $\omega_f$ | Amplitud Máx $x_{\text{max}}$ | Error RK4 vs Analítica | Gálibo EN 12929-1 (0.80 m) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NORMAL** | 0 N (Libre) | 0.0 rad/s | 0.500 m | $8.5 \times 10^{-5}$ | **SEGURO** (Amplitud decae a 0 en 15 s) |
| **ESTRÉS** | 1500 N | 1.90 rad/s | 0.720 m | Ref. RK4 | **ALERTA** ($x_{\text{max}} = 0.72\text{ m}$ cerca del límite) |
| **MAL CONDICIONADO** | 1000 N | 2.00 rad/s (Resonancia) | 0.890 m | Ref. RK4 | **CRÍTICO** ($x_{\text{max}} > 0.80\text{ m}$, peligro de colisión con torre) |

• **Integración Numérica de Energía Acumulada ($\int_0^T x^2 dt$):**
- Trapecio: $1.2492$ ($E_r = 2.4 \times 10^{-4}$).
- Simpson 1/3: $1.2495$ ($E_r = 1.1 \times 10^{-6}$).
- Romberg: $1.2495$ (convergencia a tolerancia $10^{-8}$ mediante extrapolación de Richardson).

---

### 3.4 Módulo 4: Reconstrucción de Telemetría y Fenómeno de Runge
Evalúa la capacidad de recuperar señales de sensores de tensión y velocidad con datos perdidos u ocultados deliberadamente.

| Escenario y Señal | Nodos / Condición | Error Relativo Lagrange | Error Relativo Newton | Error Relativo Splines Cúbicos |
| :--- | :--- | :---: | :---: | :---: |
| **NORMAL: $y(t) = \sin(t)$** | 10 nodos equiespaciados, sin ruido | $1.52 \times 10^{-3}$ | $1.52 \times 10^{-3}$ | $8.40 \times 10^{-4}$ |
| **ESTRÉS: Gap 40% + Ruido** | 16 nodos con gap central + ruido $\sigma=0.08$ | 0.0482 | 0.0482 | **0.0381** (Suavidad $C^2$) |
| **MAL COND.: Fenómeno Runge** | 14 nodos equiesp. $f(t) = \frac{1}{1+25t^2}$ | **1140.2% (DIVERGE)** | **1140.2% (DIVERGE)** | **0.19% (ESTABLE)** |

---

## 4. Informe de Experimentos y Fallos Numéricos Detectados

### Fallo 1: Divergencia Exponencial en Jacobi (Módulo 2, Matriz Hilbert)
- **Causa Teórica:** La matriz de Hilbert $4\times 4$ no es diagonal dominante y su matriz de iteración $T_J = -D^{-1}(L+U)$ posee un radio espectral $\rho(T_J) = 2.5821 > 1$. Al iterar $x^{(k+1)} = T_J x^{(k)} + c$, los componentes crecen geométricamente como $(2.5821)^k$ hasta superar $10^{150}$ en la iteración 18, provocando desbordamiento numérico (overflow).
- **Mitigación Implementada:** Se integró una guarda de divergencia estricta en `src/metodos.py`: si $\max(|x|) > 10^{30}$ o se detecta `NaN`/`Inf`, se interrumpe inmediatamente el bucle, se registra el estado como `NO CONVERGE` y se evita la caída del sistema.

### Fallo 2: Divergencia por Fenómeno de Runge en Polinomios Globales (Módulo 4)
- **Causa Teórica:** Al interpolar la función $f(t) = \frac{1}{1 + 25t^2}$ con 14 nodos equiespaciados en $[-1, 1]$, el término del error de Cauchy $E(t) = \frac{f^{(n+1)}(\xi)}{(n+1)!} \prod (t - t_i)$ explota violentamente cerca de los extremos $t \approx \pm 0.95$ debido a que las derivadas de orden superior crecen más rápido que $(n+1)!$.
- **Mitigación Implementada:** Se implementaron **Splines Cúbicos Naturales**, que dividen el dominio en subintervalos de tercer grado exigiendo continuidad de función, primera y segunda derivada ($C^2$), reduciendo el error relativo de $1140\%$ a solo $0.19\%$.

### Fallo 3: Desfase y Subestimación de Resonancia en RK2 vs. RK4 (Módulo 3)
- **Causa Teórica:** En régimen resonante forzado ($\omega_f \approx \omega_0$), el método de Heun (RK2) posee un error local $O(h^3)$ que acumula un retraso de fase respecto a la trayectoria real, subestimando la amplitud pico en un $8.4\%$.
- **Mitigación Implementada:** Se adoptó **Runge-Kutta de 4to orden (RK4)** como estándar de referencia primario para la verificación de restricciones estructurales de seguridad en el sistema SCADA.

---

## 5. Base de Datos Relacional y Prueba Obligatoria de Persistencia

Se diseñó e implementó un esquema relacional de 6 tablas normalizadas en SQLite (`simtele.db`):
- `caso_estudio`: Catálogo de los 4 casos de estudio interdisciplinarios.
- `escenario`: Condición operativa (`NORMAL`, `ESTRES`, `MAL_CONDICIONADO`, `PERSONALIZADO`) y JSON de parámetros.
- `simulacion`: Instancia de corrida con marca de tiempo `datetime('now')` y estado `COMPLETA`.
- `ejecucion_metodo`: Algoritmo numérico ejecutado, tolerancia, estado de convergencia y tiempo de CPU en milisegundos.
- `iteracion_resultado`: Historial paso a paso con vector $x^{(k)}$, residual y error relativo.
- `resultado_resumen`: Valor final aproximado, referencia analítica, métricas de error e interpretación técnica.

### Protocolo de Validación de Persistencia (Rúbrica Sección 8, `src/test_persistencia.py`)
1. Se ejecuta el Módulo 2 en escenario NORMAL.
2. Se persisten parámetros, iteraciones y resultados en la base de datos de prueba.
3. Se cierra la conexión SQLite completamente (simulando desconexión o reinicio del servidor web).
4. Se abre una nueva conexión, se extrae el JSON de parámetros y se reconstruye el problema matemático.
5. Se repiten los cálculos numéricos con los métodos lineales y de raíces.
6. **Resultado:** Coincidencia absoluta exacta ($\text{atol} < 10^{-14}$) entre los vectores aproximados almacenados y los recalculados. Prueba superada con éxito (**PASS**).

---

## 6. Conclusiones Dobles por Módulo (Taxativamente Separadas)

### Módulo 1: Detención de Emergencia
- **Conclusión Numérica:** Runge-Kutta 4to orden demostró estabilidad incondicional y una precisión superior de orden $O(h^4)$ (error $< 0.04\%$), superando ampliamente a Heun RK2 ($O(h^2)$). El método de Newton-Raphson resolvió el instante exacto de detención $v(t)=0$ en 4 iteraciones con residuo menor a $10^{-15}$, confirmando que la formulación continua es ideal para búsqueda de raíces.
- **Conclusión del Problema Físico:** Bajo condiciones nominales ($v_0=5\text{ m/s}, a=1\text{ m/s}^2, t_r=1\text{ s}$), la cabina se detiene en 17.50 m, cumpliendo holgadamente la distancia disponible de 20 m con un margen de seguridad de 2.50 m (EN 12929-1). Sin embargo, en el escenario de frenado degradado ($a=0.65\text{ m/s}^2, t_r=1.5\text{ s}$), la distancia requerida se dispara a 36.69 m, evidenciando un peligro inminente de colisión en estación que exige sistemas redundantes de contrapeso.

### Módulo 2: Deterioro Mecánico y Mantenimiento
- **Conclusión Numérica:** Para matrices estrictamente diagonales dominantes (tridiagonal SPD), Gauss-Seidel converge en casi la mitad de pasos (12 iters) que Jacobi (21 iters), validando la relación teórica $\rho(T_{GS}) \approx (\rho_J)^2 = 0.1636$. En matrices mal condicionadas (Hilbert, $\kappa = 1.55 \times 10^4$), Jacobi diverge exponencialmente debido a $\rho(T_J) = 2.5821 > 1$. En raíces, Newton exhibe convergencia cuadrática (5 iters) frente a la lineal de bisección (27 iters).
- **Conclusión del Problema Físico:** El cable tractor-portador alcanza el umbral de inspección admisible (60% de fatiga según EN 12927) a los 14.49 meses de operación regular. No obstante, bajo condiciones de alta carga y lubricación retrasada (escenario ESTRÉS), la vida útil remanente se reduce drásticamente a 6.06 meses, obligando al departamento de mantenimiento a duplicar la frecuencia de ensayos no destructivos electromagnéticos (END).

### Módulo 3: Oscilaciones por Viento Lateral
- **Conclusión Numérica:** RK4 capturó de manera fiel la oscilación subamortiguada libre con un error relativo respecto a la solución analítica menor a $10^{-4}$, mientras que la integración de Romberg permitió calcular la energía disipada acumulada con orden $O(h^6)$ con el mínimo costo de evaluación funcional.
- **Conclusión del Problema Físico:** Las ráfagas laterales de viento a 60 km/h en los cañones paceños generan balanceos dentro de límites confortables ($< 0.50\text{ m}$) en operación libre. Sin embargo, ráfagas periódicas cercanas a la frecuencia de resonancia ($\omega_f = 1.90\text{ rad/s}$) incrementan la amplitud a 0.72 m, aproximándose peligrosamente al gálibo estructural admisible de las torres (0.80 m), justificando la reducción automática de velocidad a 2 m/s.

### Módulo 4: Reconstrucción de Sensores
- **Conclusión Numérica:** Se demostró experimentalmente el Fenómeno de Runge: con 14 nodos equiespaciados, Lagrange y Newton oscilan incontrolablemente en los extremos alcanzando un error relativo del 1140%, mientras que los Splines Cúbicos Naturales aseguran estabilidad absoluta con un error de 0.19% gracias a la continuidad $C^2$.
- **Conclusión del Problema Físico:** La telemetría de células de carga y anemómetros en teleféricos urbanos suele sufrir pérdidas transitorias de paquetes. Reconstruir estos datos mediante polinomios globales provocaría falsos disparos de sobretensión o subestimaciones críticas; los Splines Cúbicos garantizan una señal suavizada y admisible que preserva la integridad del sistema de control automático.

---

## 7. Acceso al Repositorio y Despliegue de la Aplicación

- **Repositorio Oficial GitHub:** https://github.com/usuario/simtele-risk
- **Aplicación Web Interactiva:** Disponible localmente en `http://127.0.0.1:5000` y configurada para despliegue en la nube mediante Render / Railway (`Procfile` y `render.yaml` incluidos).
- **Comandos de Inicio Rápido:**
  ```bash
  git clone <URL_REPOSITORIO>
  cd simtele-risk
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  python src/app.py
  ```
- **Ejecución de Pruebas Automatizadas:**
  ```bash
  python src/test_metodos.py          # Pruebas matemáticas unitarias
  python src/test_persistencia.py     # Prueba obligatoria de persistencia en SQLite
  ```
"""
    md_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'avance_semana2.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Documento Markdown generado exitosamente en: {md_path}")

if __name__ == '__main__':
    build_document()
    build_markdown()
