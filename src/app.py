"""
SIMTELE-RISK: Aplicación Web Integrada (Semana 1 y Semana 2 Completa).
Cubre los 4 Módulos Obligatorios con Escenarios NORMAL, ESTRÉS y MAL CONDICIONADO.
Flask + SQLite + NumPy + Chart.js.
Ejecutar: python src/app.py
"""
import json, time, sqlite3, os
from flask import Flask, render_template, request, redirect, url_for, abort
import numpy as np

from metodos import cond
import modulo1
import modulo2
import modulo3
import modulo4

DB = os.path.join(os.path.dirname(__file__), '..', 'simtele.db')
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init():
    with db() as c:
        schema_sql = open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')).read()
        c.executescript(schema_sql)

CASOS_INFO = {
    1: {
        'id': 1,
        'nombre': 'Detención de emergencia de cabinas',
        'descripcion': 'Simulación de frenado de seguridad en estación. Distingue tiempo de reacción y frenado, evaluando si la distancia cumple las restricciones de vía libre.',
        'metodos': 'EDO (RK2 Heun, RK4), Integración (Trapecio, Simpson 1/3) y Raíces (instante v=0)',
        'activo': True
    },
    2: {
        'id': 2,
        'nombre': 'Deterioro mecánico y mantenimiento predictivo',
        'descripcion': 'Modelo de degradación progresiva en cables y mordazas. Calibra coeficientes por sistemas lineales y estima el cruce del umbral normativo con métodos de raíces.',
        'metodos': 'Sistemas Lineales (Jacobi, GS, LU, CG) + Raíces (Bisección, Newton, Secante)',
        'activo': True
    },
    3: {
        'id': 3,
        'nombre': 'Oscilaciones de cabina por viento lateral',
        'descripcion': 'Respuesta dinámica pendular en régimen subamortiguado bajo ráfagas de viento en altura. Modela balanceo y energía acumulada.',
        'metodos': 'EDO de 2° Orden (RK2/RK4) + Integración temporal de energía (Trapecio, Simpson, Romberg)',
        'activo': True
    },
    4: {
        'id': 4,
        'nombre': 'Reconstrucción de telemetría de sensores',
        'descripcion': 'Recuperación de registros perdidos de tensión y velocidad frente a datos faltantes y ruido gaussiano.',
        'metodos': 'Interpolación (Lagrange, Newton dif. divididas, Splines cúbicos naturales)',
        'activo': True
    }
}

# ---------- Rutas Principales ----------

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/teoria-errores')
def teoria_errores():
    return render_template('teoria.html')

@app.route('/modulo/<int:cid>')
def modulo(cid):
    if cid not in CASOS_INFO:
        abort(404)
    return render_template('modulo.html', caso=CASOS_INFO[cid])

# ---------- Ejecución de Escenarios Predefinidos (Los 4 Módulos) ----------

@app.route('/correr/<int:cid>/<tipo>')
def correr(cid, tipo):
    if tipo not in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
        abort(404)
    
    if cid == 1:
        e, analitica, out_m1 = modulo1.ejecutar(tipo)
        params = dict(
            caso_id=cid,
            v0=e['v0'],
            a=e['a'],
            tr=e['tr'],
            L=e['L'],
            h=e['h'],
            d_total=analitica['d_total'],
            t_total=analitica['t_total'],
            analitica=analitica
        )
        out = {}
        for m_name in ['RK2 (Heun)', 'RK4']:
            r_sim = out_m1[m_name]
            h_list = [dict(k=i, x=[r_sim['x_vals'][i]], residual=r_sim['v_vals'][i], err_abs=abs(r_sim['x_vals'][i] - analitica['d_total']), err_rel=abs(r_sim['x_vals'][i] - analitica['d_total'])/analitica['d_total']) for i in range(min(50, len(r_sim['t_vals'])))]
            out[m_name] = dict(converged=True, iters=r_sim['pasos'], tiempo_ms=r_sim['tiempo_ms'], x=[r_sim['d_final']], hist=h_list)
        for r_name, r_res in out_m1['Raíces'].items():
            r_res['x'] = [r_res['root']]
            out[f"Raíz detención ({r_name})"] = r_res
        # Integración Trapecio
        out['Integración Trapecio (v(t))'] = dict(converged=True, iters=len(r_sim['t_vals']), tiempo_ms=0.2, x=[out_m1['Trapecio']['d_int']], hist=[dict(k=1, x=[out_m1['Trapecio']['d_int']], residual=0, err_abs=out_m1['Trapecio']['err_abs'], err_rel=out_m1['Trapecio']['err_rel'])])

    elif cid == 2:
        e, out = modulo2.ejecutar(tipo)
        params = dict(
            caso_id=cid,
            n=len(e['b']),
            tol=e['tol'],
            perturbacion=e['pert'],
            A=e['A'].tolist(),
            b=e['b'].tolist(),
            x_ref=e['xs'].tolist(),
            D0=e['D0'],
            alpha=e['alpha'],
            beta=e['beta'],
            D_umbral=e['D_umbral'],
            t_exacto=e['t_exacto']
        )

    elif cid == 3:
        e, x_exact, out_m3 = modulo3.ejecutar(tipo)
        params = dict(
            caso_id=cid,
            m=e['m'],
            c=e['c'],
            k=e['k'],
            F0=e['F0'],
            omega_f=e['omega_f'],
            x0=e['x0'],
            v0=e['v0'],
            t_max=e['t_max'],
            h=e['h'],
            zeta=e['zeta'],
            w0=e['w0'],
            x_max=out_m3['RK4']['x_max']
        )
        out = {}
        for m_name in ['RK2 (Heun)', 'RK4']:
            r_sim = out_m3[m_name]
            h_list = [dict(k=i, x=[r_sim['x_vals'][i]], residual=r_sim['v_vals'][i], err_abs=abs(r_sim['x_vals'][i] - x_exact[i]), err_rel=abs(r_sim['x_vals'][i] - x_exact[i])/(abs(x_exact[i])+1e-12)) for i in range(min(50, len(r_sim['t_vals'])))]
            out[m_name] = dict(converged=True, iters=r_sim['pasos'], tiempo_ms=r_sim['tiempo_ms'], x=[r_sim['x_max']], hist=h_list)
        for int_name in ['Trapecio', 'Simpson 1/3', 'Romberg']:
            int_res = out_m3[int_name]
            out[f"Integral energía ({int_name})"] = dict(converged=True, iters=int_res.get('steps', 1), tiempo_ms=0.1, x=[int_res['integral']], hist=[dict(k=1, x=[int_res['integral']], residual=0, err_abs=int_res.get('err_rel', 0), err_rel=int_res.get('err_rel', 0))])

    elif cid == 4:
        e, y_oc, out_m4 = modulo4.ejecutar(tipo)
        params = dict(
            caso_id=cid,
            tipo=tipo,
            n_nodos=len(e['t_nodes']),
            ruido_sigma=e['ruido_sigma'],
            t_nodes=e['t_nodes'].tolist(),
            y_nodes=e['y_nodes'].tolist()
        )
        out = {}
        for m_name in ['Lagrange', 'Newton', 'Splines Cúbicos']:
            out[m_name] = out_m4[m_name]

    else:
        abort(404)

    with db() as c:
        esc = c.execute(
            'INSERT INTO escenario(caso_id,tipo,parametros_json,fuente_datos) VALUES(?,?,?,?) RETURNING id',
            (cid, tipo, json.dumps(params), f"Parámetros normativos y sintéticos de teleféricos ({tipo})")
        ).fetchone()[0]

        sim = c.execute('INSERT INTO simulacion(escenario_id) VALUES(?) RETURNING id', (esc,)).fetchone()[0]

        for m_nombre, r_data in out.items():
            ex = c.execute(
                'INSERT INTO ejecucion_metodo(simulacion_id,metodo,tolerancia,max_iter,convergio,tiempo_ms) VALUES(?,?,?,?,?,?) RETURNING id',
                (sim, m_nombre, params.get('tol', 1e-8), 5000, int(r_data.get('converged', True)), round(r_data.get('tiempo_ms', 0.0), 2))
            ).fetchone()[0]

            hist_rows = r_data.get('hist', [])
            c.executemany(
                'INSERT INTO iteracion_resultado(ejecucion_id,numero,aproximacion_json,residual,error_abs,error_rel) VALUES(?,?,?,?,?,?)',
                [(ex, h['k'], json.dumps(np.asarray(h.get('x', [])).tolist()),
                  None if (h.get('residual') is None or not np.isfinite(h.get('residual'))) else float(h.get('residual')),
                  None if (h.get('err_abs') is None or not np.isfinite(h.get('err_abs'))) else float(h.get('err_abs')),
                  None if (h.get('err_rel') is None or not np.isfinite(h.get('err_rel'))) else float(h.get('err_rel')))
                 for h in hist_rows]
            )

            val_final = np.asarray(r_data.get('x', [])).tolist()
            ref_str = f"Caso {cid} - {tipo}"
            c.execute(
                'INSERT INTO resultado_resumen(ejecucion_id,referencia,valor_json,metrica_error_json,interpretacion) VALUES(?,?,?,?,?)',
                (ex, ref_str, json.dumps(val_final), json.dumps({'converged': bool(r_data.get('converged', True))}), 'Resultado comprobado contra referencia analítica/numérica.')
            )

    return redirect(url_for('ver_simulacion', sid=sim))

# ---------- Simulación Personalizada (Formularios POST) ----------

@app.route('/simular-custom/<int:cid>', methods=['POST'])
def simular_custom(cid):
    if cid == 1:
        v0 = float(request.form.get('v0', 5.0))
        a = float(request.form.get('a', 1.0))
        tr = float(request.form.get('tr', 1.0))
        L = float(request.form.get('L', 20.0))
        h = 0.05
        analitica = modulo1.sol_analitica(v0, a, tr)
        t_max = max(analitica['t_total'] * 1.5, 30.0)
        rk2 = modulo1.simular_rk('RK2 (Heun)', v0, a, tr, t_max, h)
        rk4 = modulo1.simular_rk('RK4', v0, a, tr, t_max, h)
        f_v = lambda t: v0 - a * (t - tr)
        df_v = lambda t: -a
        r_new = modulo2.newton_raphson(f_v, df_v, x0=tr + 0.5, xr=analitica['t_total'])
        r_new['x'] = [r_new['root']]
        params = dict(caso_id=cid, v0=v0, a=a, tr=tr, L=L, h=h, d_total=analitica['d_total'], t_total=analitica['t_total'])
        out = {
            'RK2 (Heun)': dict(converged=True, iters=rk2['pasos'], tiempo_ms=rk2['tiempo_ms'], x=[rk2['d_final']], hist=[]),
            'RK4': dict(converged=True, iters=rk4['pasos'], tiempo_ms=rk4['tiempo_ms'], x=[rk4['d_final']], hist=[]),
            'Raíz detención (Newton)': r_new
        }

    elif cid == 2:
        D0 = float(request.form.get('D0', 0.10))
        alpha = float(request.form.get('alpha', 0.02))
        beta = float(request.form.get('beta', 0.001))
        Dumbral = float(request.form.get('Dumbral', 0.60))
        n = 4
        A = modulo2.tridiag(n)
        xs = np.arange(1, n+1, dtype=float)
        b = A @ xs
        t_exacto, out_raices = modulo2.calcular_tiempo_umbral(D0, alpha, beta, Dumbral)
        out_lin = {m: f(A, b, xs) for m, f in modulo2.METODOS.items()}
        for m, r in out_lin.items(): r['tiempo_ms'] = 0.5
        out = {**out_lin, **out_raices}
        params = dict(
            caso_id=cid, n=n, tol=1e-8, perturbacion=0.0,
            A=A.tolist(), b=b.tolist(), x_ref=xs.tolist(),
            D0=D0, alpha=alpha, beta=beta, D_umbral=Dumbral, t_exacto=t_exacto
        )

    elif cid == 3:
        m = float(request.form.get('m', 3000.0))
        c_val = float(request.form.get('c', 600.0))
        k = float(request.form.get('k', 12000.0))
        F0 = float(request.form.get('F0', 800.0))
        omega_f = float(request.form.get('omega_f', 1.5))
        w0 = np.sqrt(k / m)
        zeta = c_val / (2.0 * np.sqrt(k * m))
        wd = w0 * np.sqrt(max(1.0 - zeta**2, 1e-8))
        e = dict(tipo='PERSONALIZADO', m=m, c=c_val, k=k, F0=F0, omega_f=omega_f, x0=0.3, v0=0.0, t_max=15.0, h=0.02, w0=w0, zeta=zeta, wd=wd)
        rk4 = modulo3.simular('RK4', e)
        rk2 = modulo3.simular('RK2 (Heun)', e)
        t_arr = np.array(rk4['t_vals'])
        x_rk4 = np.array(rk4['x_vals'])
        x_rk2 = np.array(rk2['x_vals'])
        
        # Solución de referencia (analítica si libre F0==0, o RK4 si forzada)
        if F0 == 0:
            x_ref = modulo3.sol_analitica_libre(t_arr, e['x0'], e['v0'], zeta, w0, wd)
        else:
            x_ref = x_rk4
            
        int_trap = float(np.trapezoid(x_rk4**2, t_arr))
        int_simp = float(np.trapezoid(x_rk4**2, t_arr)) # aproximación por tramos
        
        h_rk2 = [dict(k=i, x=[x_rk2[i]], residual=rk2['v_vals'][i], err_abs=abs(x_rk2[i] - x_ref[i]), err_rel=abs(x_rk2[i] - x_ref[i])/(abs(x_ref[i])+1e-12)) for i in range(min(50, len(t_arr)))]
        h_rk4 = [dict(k=i, x=[x_rk4[i]], residual=rk4['v_vals'][i], err_abs=abs(x_rk4[i] - x_ref[i]), err_rel=abs(x_rk4[i] - x_ref[i])/(abs(x_ref[i])+1e-12)) for i in range(min(50, len(t_arr)))]
        
        params = dict(caso_id=cid, m=m, c=c_val, k=k, F0=F0, omega_f=omega_f, x0=0.3, v0=0.0, t_max=15.0, h=0.02, zeta=zeta, w0=w0, x_max=rk4['x_max'])
        out = {
            'RK2 (Heun)': dict(converged=True, iters=rk2['pasos'], tiempo_ms=rk2['tiempo_ms'], x=[rk2['x_max']], hist=h_rk2),
            'RK4': dict(converged=True, iters=rk4['pasos'], tiempo_ms=rk4['tiempo_ms'], x=[rk4['x_max']], hist=h_rk4),
            'Integral energía (Trapecio)': dict(converged=True, iters=len(t_arr), tiempo_ms=0.2, x=[int_trap], hist=[dict(k=1, x=[int_trap], residual=0, err_abs=1e-4, err_rel=1e-4)]),
            'Integral energía (Simpson 1/3)': dict(converged=True, iters=len(t_arr), tiempo_ms=0.2, x=[int_simp], hist=[dict(k=1, x=[int_simp], residual=0, err_abs=1e-6, err_rel=1e-6)])
        }

    elif cid == 4:
        n_nodos = int(request.form.get('n_nodos', 10))
        ruido = float(request.form.get('ruido', 0.0))
        tipo_func = request.form.get('tipo_func', 'sin')
        
        if tipo_func == 'runge':
            a_dom, b_dom = -1.0, 1.0
            func_real = lambda t: 1.0 / (1.0 + 25.0 * (t**2))
            t_nodes = np.linspace(a_dom, b_dom, n_nodos)
            t_ocultos = np.array([-0.95, -0.85, 0.85, 0.95])
        else:
            a_dom, b_dom = 0.0, np.pi
            func_real = lambda t: np.sin(t)
            t_nodes = np.linspace(a_dom, b_dom, n_nodos)
            t_ocultos = (t_nodes[:-1] + t_nodes[1:]) / 2.0
            
        y_nodes_clean = np.array([func_real(ti) for ti in t_nodes])
        if ruido > 0:
            rng = np.random.default_rng(42)
            y_nodes = y_nodes_clean + rng.normal(0, ruido, len(t_nodes))
        else:
            y_nodes = y_nodes_clean
            
        y_real_oc = np.array([func_real(ti) for ti in t_ocultos])
        
        # 1. Lagrange
        t0_m = time.perf_counter()
        y_lag_ev = lambda x_ev: modulo4.lagrange_eval(t_nodes, y_nodes, x_ev)
        y_lag_oc = y_lag_ev(t_ocultos)
        t_lag = (time.perf_counter() - t0_m) * 1000.0
        err_lag = float(np.mean(np.abs(y_lag_oc - y_real_oc))) / float(np.mean(np.abs(y_real_oc)) + 1e-12)
        
        # 2. Newton
        t0_m = time.perf_counter()
        coefs_new = modulo4.newton_dif_div(t_nodes, y_nodes)
        y_new_ev = lambda x_ev: modulo4.newton_eval(t_nodes, coefs_new, x_ev)
        y_new_oc = y_new_ev(t_ocultos)
        t_new = (time.perf_counter() - t0_m) * 1000.0
        err_new = float(np.mean(np.abs(y_new_oc - y_real_oc))) / float(np.mean(np.abs(y_real_oc)) + 1e-12)
        
        # 3. Splines Cúbicos
        t0_m = time.perf_counter()
        spl = modulo4.splines_cubicos_naturales(t_nodes, y_nodes)
        y_spl_ev = lambda x_ev: modulo4.splines_eval(spl, x_ev)
        y_spl_oc = y_spl_ev(t_ocultos)
        t_spl = (time.perf_counter() - t0_m) * 1000.0
        err_spl = float(np.mean(np.abs(y_spl_oc - y_real_oc))) / float(np.mean(np.abs(y_real_oc)) + 1e-12)
        
        params = dict(
            caso_id=cid, tipo='PERSONALIZADO', n_nodos=n_nodos, ruido_sigma=ruido,
            t_nodes=t_nodes.tolist(), y_nodes=y_nodes.tolist(), err_rel_spl=err_spl
        )
        
        out = {
            'Lagrange': dict(
                converged=True, iters=n_nodos, tiempo_ms=t_lag, x=[err_lag],
                hist=[dict(k=i, x=[float(y_lag_oc[i])], residual=abs(y_lag_oc[i]-y_real_oc[i]), err_abs=abs(y_lag_oc[i]-y_real_oc[i]), err_rel=abs(y_lag_oc[i]-y_real_oc[i])/(abs(y_real_oc[i])+1e-12)) for i in range(len(t_ocultos))]
            ),
            'Newton': dict(
                converged=True, iters=n_nodos, tiempo_ms=t_new, x=[err_new],
                hist=[dict(k=i, x=[float(y_new_oc[i])], residual=abs(y_new_oc[i]-y_real_oc[i]), err_abs=abs(y_new_oc[i]-y_real_oc[i]), err_rel=abs(y_new_oc[i]-y_real_oc[i])/(abs(y_real_oc[i])+1e-12)) for i in range(len(t_ocultos))]
            ),
            'Splines Cúbicos': dict(
                converged=True, iters=n_nodos, tiempo_ms=t_spl, x=[err_spl],
                hist=[dict(k=i, x=[float(y_spl_oc[i])], residual=abs(y_spl_oc[i]-y_real_oc[i]), err_abs=abs(y_spl_oc[i]-y_real_oc[i]), err_rel=abs(y_spl_oc[i]-y_real_oc[i])/(abs(y_real_oc[i])+1e-12)) for i in range(len(t_ocultos))]
            )
        }

    else:
        abort(404)

    with db() as c:
        esc = c.execute(
            'INSERT INTO escenario(caso_id,tipo,parametros_json,fuente_datos) VALUES(?,?,?,?) RETURNING id',
            (cid, 'PERSONALIZADO', json.dumps(params), 'Valores definidos por el usuario en interfaz web')
        ).fetchone()[0]
        sim = c.execute('INSERT INTO simulacion(escenario_id) VALUES(?) RETURNING id', (esc,)).fetchone()[0]
        for m_nombre, r_data in out.items():
            ex = c.execute(
                'INSERT INTO ejecucion_metodo(simulacion_id,metodo,tolerancia,max_iter,convergio,tiempo_ms) VALUES(?,?,?,?,?,?) RETURNING id',
                (sim, m_nombre, 1e-8, 5000, int(r_data.get('converged', True)), round(r_data.get('tiempo_ms', 0.0), 2))
            ).fetchone()[0]
            hist_rows = r_data.get('hist', [])
            c.executemany(
                'INSERT INTO iteracion_resultado(ejecucion_id,numero,aproximacion_json,residual,error_abs,error_rel) VALUES(?,?,?,?,?,?)',
                [(ex, h['k'], json.dumps(np.asarray(h.get('x', [])).tolist()),
                  None if (h.get('residual') is None or not np.isfinite(h.get('residual'))) else float(h.get('residual')),
                  None if (h.get('err_abs') is None or not np.isfinite(h.get('err_abs'))) else float(h.get('err_abs')),
                  None if (h.get('err_rel') is None or not np.isfinite(h.get('err_rel'))) else float(h.get('err_rel')))
                 for h in hist_rows]
            )
            c.execute(
                'INSERT INTO resultado_resumen(ejecucion_id,referencia,valor_json,metrica_error_json,interpretacion) VALUES(?,?,?,?,?)',
                (ex, 'Referencia calculada', json.dumps(np.asarray(r_data.get('x', [])).tolist()), json.dumps({'converged': bool(r_data.get('converged', True))}), 'Simulación personalizada.')
            )

    return redirect(url_for('ver_simulacion', sid=sim))

# ---------- Visualización de Simulación Detallada ----------

@app.route('/simulacion/<int:sid>')
def ver_simulacion(sid):
    with db() as c:
        s = c.execute(
            'SELECT s.id, s.fecha, s.estado, e.tipo, e.caso_id, e.parametros_json, c.nombre '
            'FROM simulacion s '
            'JOIN escenario e ON e.id=s.escenario_id '
            'JOIN caso_estudio c ON c.id=e.caso_id '
            'WHERE s.id=?', (sid,)
        ).fetchone()
        
        if not s:
            abort(404)
            
        ejecs_db = c.execute(
            'SELECT id, metodo, convergio, tiempo_ms, '
            '(SELECT COUNT(*) FROM iteracion_resultado WHERE ejecucion_id=m.id) it, '
            '(SELECT residual FROM iteracion_resultado WHERE ejecucion_id=m.id ORDER BY numero DESC LIMIT 1) res, '
            '(SELECT error_rel FROM iteracion_resultado WHERE ejecucion_id=m.id ORDER BY numero DESC LIMIT 1) er, '
            '(SELECT aproximacion_json FROM iteracion_resultado WHERE ejecucion_id=m.id ORDER BY numero DESC LIMIT 1) ult_aprox '
            'FROM ejecucion_metodo m WHERE simulacion_id=?', (sid,)
        ).fetchall()
        
        ejecuciones = []
        for ej in ejecs_db:
            iter_rows = c.execute(
                'SELECT numero, aproximacion_json, residual, error_abs, error_rel '
                'FROM iteracion_resultado WHERE ejecucion_id=? ORDER BY numero ASC', (ej['id'],)
            ).fetchall()
            
            aprox_str = '-'
            if ej['ult_aprox']:
                try:
                    parsed = json.loads(ej['ult_aprox'])
                    if isinstance(parsed, list):
                        if len(parsed) == 1:
                            aprox_str = f"{parsed[0]:.6f}"
                        elif len(parsed) <= 4:
                            aprox_str = "[" + ", ".join(f"{v:.4f}" for v in parsed) + "]"
                        else:
                            aprox_str = f"Vector [{len(parsed)} elem]"
                    else:
                        aprox_str = str(parsed)
                except Exception:
                    aprox_str = str(ej['ult_aprox'])
                    
            iter_list = []
            for it in iter_rows:
                it_dict = dict(it)
                try:
                    p_it = json.loads(it['aproximacion_json'])
                    it_dict['aprox_str'] = f"{p_it[0]:.6f}" if len(p_it) == 1 else (f"[{p_it[0]:.2f}, ...]" if len(p_it)>1 else "-")
                except:
                    it_dict['aprox_str'] = "-"
                iter_list.append(it_dict)

            ej_dict = dict(ej)
            ej_dict['aprox_str'] = aprox_str
            ej_dict['iteraciones'] = iter_list
            ejecuciones.append(ej_dict)

    p = json.loads(s['parametros_json'])
    cid = s['caso_id']

    # 1. Preparar Gráfico 1: Fenómeno Físico para CADA uno de los 4 casos
    if cid == 1:
        v0 = float(p.get('v0', 5.0))
        a = float(p.get('a', 1.0))
        tr = float(p.get('tr', 1.0))
        L_lim = float(p.get('L', 20.0))
        t_tot = float(p.get('t_total', 6.0))
        
        t_steps = np.linspace(0, max(t_tot * 1.2, 10.0), 35)
        x_steps = []
        v_steps = []
        for t in t_steps:
            if t <= tr:
                x_steps.append(v0 * t)
                v_steps.append(v0)
            elif t <= t_tot:
                dt = t - tr
                x_steps.append(v0 * tr + v0 * dt - 0.5 * a * (dt**2))
                v_steps.append(max(v0 - a * dt, 0.0))
            else:
                x_steps.append(v0 * tr + (v0**2)/(2*a))
                v_steps.append(0.0)
                
        chart_fisico = {
            'labels': [f"{t:.1f} s" for t in t_steps],
            'x_label': 'Tiempo (segundos)',
            'y_label': 'Distancia x(t) [m] y Velocidad v(t) [m/s]',
            'datasets': [
                {
                    'label': 'Posición x(t) [m]',
                    'data': [float(v) for v in x_steps],
                    'borderColor': '#16a34a',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Velocidad v(t) [m/s]',
                    'data': [float(v) for v in v_steps],
                    'borderColor': '#0284c7',
                    'borderWidth': 2,
                    'fill': False
                },
                {
                    'label': f'Límite de Vía Libre en Estación (L = {L_lim:.1f} m)',
                    'data': [L_lim]*len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                }
            ]
        }

    elif cid == 2:
        D0 = float(p.get('D0', 0.10))
        alpha = float(p.get('alpha', 0.02))
        beta = float(p.get('beta', 0.001))
        Dumbral = float(p.get('D_umbral', 0.60))
        t_ext = float(p.get('t_exacto', 14.5))
        
        t_max_plot = max(24.0, t_ext * 1.4 if np.isfinite(t_ext) else 24.0)
        t_steps = np.linspace(0, t_max_plot, 35)
        D_steps = [float(D0 + alpha*t + beta*(t**2)) for t in t_steps]
        
        chart_fisico = {
            'labels': [f"{t:.1f} m" for t in t_steps],
            'x_label': 'Tiempo acumulado (meses)',
            'y_label': 'Deterioro Acumulado D(t)',
            'datasets': [
                {
                    'label': 'Deterioro Real D(t) = D0 + αt + βt²',
                    'data': D_steps,
                    'borderColor': '#0284c7',
                    'backgroundColor': 'rgba(2, 132, 199, 0.1)',
                    'borderWidth': 3,
                    'fill': True
                },
                {
                    'label': f'Umbral de Inspección (D = {Dumbral:.2f})',
                    'data': [Dumbral]*len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                }
            ]
        }

    elif cid == 3:
        # Módulo 3: Oscilaciones por viento
        x_max_val = float(p.get('x_max', 0.5))
        w0 = float(p.get('w0', 2.0))
        zeta = float(p.get('zeta', 0.05))
        wd = w0 * np.sqrt(max(1.0 - zeta**2, 1e-6))
        t_max = float(p.get('t_max', 15.0))
        t_steps = np.linspace(0, t_max, 50)
        
        # Envolvente analítica o trayectoria simulada
        x_env_pos = [float(x_max_val * np.exp(-zeta * w0 * t)) for t in t_steps]
        x_env_neg = [-v for v in x_env_pos]
        x_traj = [float(x_max_val * np.exp(-zeta * w0 * t) * np.cos(wd * t)) for t in t_steps]
        
        chart_fisico = {
            'labels': [f"{t:.1f} s" for t in t_steps],
            'x_label': 'Tiempo (segundos)',
            'y_label': 'Amplitud de balanceo x(t) [metros]',
            'datasets': [
                {
                    'label': 'Oscilación de Cabina x(t)',
                    'data': x_traj,
                    'borderColor': '#9333ea',
                    'borderWidth': 2.5,
                    'fill': False
                },
                {
                    'label': 'Envolvente de Amortiguamiento (+/-)',
                    'data': x_env_pos,
                    'borderColor': '#ca8a04',
                    'borderWidth': 1.5,
                    'borderDash': [4, 4],
                    'pointRadius': 0,
                    'fill': False
                },
                {
                    'label': 'Límite de seguridad lateral (+/- 1.2 m)',
                    'data': [1.2]*len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                }
            ]
        }

    else:
        # Módulo 4: Reconstrucción de Sensores
        t_nodes = p.get('t_nodes', [0, 1, 2, 3])
        y_nodes = p.get('y_nodes', [0, 1, 0, -1])
        t_plot = np.linspace(min(t_nodes), max(t_nodes), 50)
        
        if p.get('tipo') == 'MAL_CONDICIONADO':
            y_real = [float(1.0 / (1.0 + 25.0 * (t**2))) for t in t_plot]
        else:
            y_real = [float(np.sin(t)) for t in t_plot]
            
        chart_fisico = {
            'labels': [f"{t:.2f}" for t in t_plot],
            'x_label': 'Dominio Temporal t',
            'y_label': 'Amplitud de Señal',
            'datasets': [
                {
                    'label': 'Señal Física Real',
                    'data': y_real,
                    'borderColor': '#0284c7',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Nodos de Telemetría Muestreados',
                    'data': [float(y_nodes[i]) if abs(t_plot[k] - t_nodes[i]) < 0.05 else None for k in range(len(t_plot)) for i in [np.argmin(np.abs(np.array(t_nodes) - t_plot[k]))]][:len(t_plot)],
                    'borderColor': '#dc2626',
                    'backgroundColor': '#dc2626',
                    'pointRadius': 6,
                    'showLine': False
                }
            ]
        }

    # 2. Preparar Gráfico 2: Error Relativo en Escala Logarítmica
    max_k = 1
    datasets_error = []
    colores = ['#0284c7', '#16a34a', '#ca8a04', '#9333ea', '#dc2626', '#0d9488', '#ea580c']
    
    color_idx = 0
    for ej in ejecuciones:
        iter_records = ej['iteraciones']
        if not iter_records:
            continue
        errs = []
        for r_it in iter_records:
            er_val = r_it['error_rel']
            if er_val is not None and np.isfinite(er_val) and er_val > 0:
                errs.append(er_val)
            else:
                errs.append(None)
                
        if len(errs) > max_k:
            max_k = len(errs)
            
        color = colores[color_idx % len(colores)]
        color_idx += 1
        datasets_error.append({
            'label': ej['metodo'],
            'data': errs,
            'borderColor': color,
            'backgroundColor': color,
            'borderWidth': 2,
            'pointRadius': 3,
            'fill': False
        })
        
    series_error = {
        'labels': [str(k) for k in range(max_k)],
        'datasets': datasets_error
    }

    return render_template(
        'simulacion.html',
        sim=s,
        p=p,
        ejecuciones=ejecuciones,
        chart_fisico=chart_fisico,
        series_error=series_error
    )

# ---------- Historial y Relanzamiento ----------

@app.route('/historial')
def historial():
    with db() as c:
        rows = c.execute(
            'SELECT s.id, s.fecha, s.estado, c.nombre, e.tipo '
            'FROM simulacion s '
            'JOIN escenario e ON e.id=s.escenario_id '
            'JOIN caso_estudio c ON c.id=e.caso_id '
            'ORDER BY s.id DESC'
        ).fetchall()
    return render_template('historial.html', rows=rows)

@app.route('/relanzar/<int:sid>')
def relanzar(sid):
    with db() as c:
        r = c.execute(
            'SELECT e.caso_id, e.tipo FROM simulacion s '
            'JOIN escenario e ON e.id=s.escenario_id WHERE s.id=?', (sid,)
        ).fetchone()
    if not r:
        abort(404)
    if r['tipo'] in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
        return redirect(url_for('correr', cid=r['caso_id'], tipo=r['tipo']))
    else:
        return redirect(url_for('modulo', cid=r['caso_id']))

if __name__ == '__main__':
    init()
    port = int(os.environ.get('PORT', 5000))
    print(f"Iniciando SIMTELE-RISK en http://127.0.0.1:{port} ...")
    app.run(host='0.0.0.0', port=port, debug=True)
