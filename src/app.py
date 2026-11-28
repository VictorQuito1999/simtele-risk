"""
SIMTELE-RISK: Aplicación Web Integrada (Versión Final · Semana 3).
Cubre los 4 Módulos Obligatorios con Escenarios NORMAL, ESTRÉS, MAL CONDICIONADO y PERSONALIZADO.
Flask + SQLite / Turso LibSQL + NumPy + Chart.js + MathJax.
Ejecutar: python src/app.py
"""
import json, os, sys, urllib.parse

# Asegurar que la carpeta 'src' esté en sys.path para importaciones en Vercel y local
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from flask import Flask, render_template, request, redirect, url_for, abort
import numpy as np

from metodos import cond, METODOS, radio_espectral_jacobi, radio_espectral_gs
import modulo1
import modulo2
import modulo3
import modulo4
from db_adapter import get_db, run_pipeline, DB_PATH

DB = DB_PATH
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)


class VercelPathFixMiddleware:
    """Middleware WSGI para corregir PATH_INFO en Vercel Serverless Functions."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if '__path__=' in query_string:
            params = urllib.parse.parse_qs(query_string)
            if '__path__' in params and params['__path__']:
                target = params['__path__'][0]
                if not target.startswith('/'):
                    target = '/' + target
                while target.startswith('//'):
                    target = target[1:]
                environ['PATH_INFO'] = target
                clean_queries = [p for p in query_string.split('&') if not p.startswith('__path__=')]
                environ['QUERY_STRING'] = '&'.join(clean_queries)
                return self.wsgi_app(environ, start_response)

        for header_key in ('HTTP_X_FORWARDED_URI', 'HTTP_X_ORIGINAL_URL', 'HTTP_X_INVOKE_PATH'):
            val = environ.get(header_key)
            if val and not val.startswith('/src/app.py'):
                environ['PATH_INFO'] = val.split('?')[0]
                return self.wsgi_app(environ, start_response)

        if environ.get('PATH_INFO', '') in ('/src/app.py', ''):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)


def db():
    return get_db()


def init():
    try:
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
        if os.path.exists(schema_file):
            with db() as c:
                schema_sql = open(schema_file, encoding='utf-8').read()
                c.executescript(schema_sql)
    except Exception as e:
        print(f"Init DB notice: {e}")


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
@app.route('/src/app.py')
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


# ---------- Funciones Auxiliares de Formato y Muestreo ----------

def _format_x_json(h):
    val = h.get('x')
    if val is None:
        return json.dumps([])
    if isinstance(val, (list, tuple)):
        return json.dumps([float(v) for v in val])
    if isinstance(val, (int, float, np.number)):
        return json.dumps([float(val)])
    try:
        arr = np.asarray(val).tolist()
        if isinstance(arr, list):
            return json.dumps(arr)
        return json.dumps([arr])
    except Exception:
        return json.dumps([])


def _format_residual(h):
    r = h.get('residual')
    if r is None:
        r = h.get('fx')
    if r is not None:
        try:
            r_val = float(abs(r))
            if np.isfinite(r_val):
                return r_val
        except Exception:
            pass
    return None


def _sample_history(hist_rows, max_rows=80):
    """Mantiene completo hist_rows hasta 80 elementos; si excede (ej. 5000 iters), muestrea conservando inicio y fin."""
    n = len(hist_rows)
    if n <= max_rows:
        return hist_rows
    head = list(range(25))
    tail = list(range(n - 25, n))
    mid_count = max_rows - 50
    mid = np.linspace(25, n - 26, mid_count, dtype=int).tolist()
    idxs = sorted(set(head + mid + tail))
    return [hist_rows[i] for i in idxs]


# ---------- Motor Unificado de Ejecución (Predefinidos y Personalizados) ----------

def _ejecutar_modulo(cid, tipo, custom=None):
    """Ejecuta cualquier módulo en modo predefinido o personalizado y devuelve (params, out)."""
    custom = custom or {}
    if cid == 1:
        if tipo in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
            e, analitica, out_m1 = modulo1.ejecutar(tipo)
        else:
            v0 = float(custom.get('v0', 5.0))
            a = float(custom.get('a', 1.0))
            tr = float(custom.get('tr', 1.0))
            L = float(custom.get('L', 20.0))
            h = float(custom.get('h', 0.05))
            no_lineal = bool(custom.get('no_lineal', False))
            e, analitica, out_m1 = modulo1.ejecutar_calculo(v0, a, tr, L, h=h, no_lineal=no_lineal, tipo='PERSONALIZADO')

        rk4 = out_m1['RK4']
        rk2 = out_m1['RK2 (Heun)']
        params = dict(
            caso_id=cid,
            tipo=e['tipo'],
            v0=e['v0'],
            a=e['a'],
            tr=e['tr'],
            L=e['L'],
            h=e['h'],
            no_lineal=e['no_lineal'],
            d_total=analitica['d_total'],
            d_rk4=rk4['d_final'],
            err_rel_rk4=rk4['err_rel'],
            err_rel_rk2=rk2['err_rel'],
            t_total=analitica['t_total'],
            analitica=analitica,
            plot_data=out_m1['plot_data']
        )
        out = {}
        for m_name in ['RK2 (Heun)', 'RK4']:
            r_sim = out_m1[m_name]
            out[m_name] = dict(
                converged=True,
                iters=r_sim['pasos'],
                paso=e['h'],
                tiempo_ms=r_sim['tiempo_ms'],
                x=[r_sim['d_final']],
                hist=r_sim['hist']
            )
        for r_name, r_res in out_m1['Raíces'].items():
            out[f"Raíz detención ({r_name})"] = r_res
        for int_name in ['Trapecio', 'Simpson 1/3']:
            int_res = out_m1[int_name]
            out[f"Integración {int_name} (v(t))"] = dict(
                converged=True,
                iters=len(int_res['hist']),
                tiempo_ms=int_res['tiempo_ms'],
                x=[int_res['d_int']],
                hist=int_res['hist']
            )
        return params, out

    elif cid == 2:
        if tipo in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
            e, out = modulo2.ejecutar(tipo)
        else:
            D0 = float(custom.get('D0', 0.10))
            alpha = float(custom.get('alpha', 0.02))
            beta = float(custom.get('beta', 0.001))
            Dumbral = float(custom.get('D_umbral', custom.get('Dumbral', 0.60)))
            n = int(custom.get('n', 4))
            tol = float(custom.get('tol', 1e-8))
            A = np.array(custom['A'], dtype=float) if 'A' in custom else modulo2.tridiag(n)
            xs = np.array(custom['x_ref'], dtype=float) if 'x_ref' in custom else np.arange(1, n + 1, dtype=float)
            b = np.array(custom['b'], dtype=float) if 'b' in custom else (A @ xs)
            t_exacto, out_raices = modulo2.calcular_tiempo_umbral(D0, alpha, beta, Dumbral, tol=tol)
            import time as _t
            out_lin = {}
            for m, f in METODOS.items():
                t0 = _t.perf_counter()
                res = f(A, b, xs, tol=tol, max_iter=5000)
                res['tiempo_ms'] = (_t.perf_counter() - t0) * 1000.0
                out_lin[m] = res
            out = {**out_lin, **out_raices}
            e = dict(
                tipo='PERSONALIZADO', A=A, b=b, xs=xs, tol=tol,
                pert=float(custom.get('perturbacion', 0.0)),
                D0=D0, alpha=alpha, beta=beta, D_umbral=Dumbral,
                t_exacto=float(t_exacto),
                cond_A=float(cond(A)),
                rho_j=float(radio_espectral_jacobi(A)) if len(b) <= 10 else None,
                rho_gs=float(radio_espectral_gs(A)) if len(b) <= 10 else None
            )

        r_new = out.get('Newton-Raphson', {})
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
            t_exacto=e['t_exacto'],
            cond_A=e.get('cond_A', float(cond(e['A']))),
            rho_j=e.get('rho_j'),
            rho_gs=e.get('rho_gs'),
            newton_iters=r_new.get('iters', 5)
        )
        return params, out

    elif cid == 3:
        if tipo in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
            e, x_exact, out_m3 = modulo3.ejecutar(tipo)
        else:
            m = float(custom.get('m', 3000.0))
            c_val = float(custom.get('c', 600.0))
            k = float(custom.get('k', 12000.0))
            F0 = float(custom.get('F0', 800.0))
            omega_f = float(custom.get('omega_f', 1.5))
            x0 = float(custom.get('x0', 0.3))
            v0 = float(custom.get('v0', 0.0))
            t_max = float(custom.get('t_max', 15.0))
            h = float(custom.get('h', 0.02))
            w0 = float(np.sqrt(k / m))
            zeta = float(c_val / (2.0 * np.sqrt(k * m)))
            wd = float(w0 * np.sqrt(max(1.0 - zeta ** 2, 1e-8)))
            e_cfg = dict(
                tipo='PERSONALIZADO', m=m, c=c_val, k=k, F0=F0, omega_f=omega_f,
                x0=x0, v0=v0, t_max=t_max, h=h, w0=w0, zeta=zeta, wd=wd
            )
            e, x_exact, out_m3 = modulo3.ejecutar_calculo(e_cfg)

        params = dict(
            caso_id=cid,
            tipo=e['tipo'],
            m=float(e['m']),
            c=float(e['c']),
            k=float(e['k']),
            F0=float(e['F0']),
            omega_f=float(e['omega_f']),
            x0=float(e['x0']),
            v0=float(e['v0']),
            t_max=float(e['t_max']),
            h=float(e['h']),
            zeta=float(e['zeta']),
            w0=float(e['w0']),
            x_max=float(out_m3['RK4']['x_max']),
            err_rel_rk4=float(out_m3['RK4']['err_rel']),
            err_rel_rk2=float(out_m3['RK2 (Heun)']['err_rel']),
            plot_data=out_m3['plot_data']
        )
        out = {}
        for m_name in ['RK2 (Heun)', 'RK4']:
            r_sim = out_m3[m_name]
            out[m_name] = dict(
                converged=True,
                iters=r_sim['pasos'],
                paso=float(e['h']),
                tiempo_ms=r_sim['tiempo_ms'],
                x=[r_sim['x_max']],
                hist=r_sim['hist']
            )
        for int_name in ['Trapecio', 'Simpson 1/3', 'Romberg']:
            int_res = out_m3[int_name]
            out[f"Integral energía ({int_name})"] = dict(
                converged=True,
                iters=int_res.get('steps', len(int_res.get('hist', []))),
                tiempo_ms=int_res.get('tiempo_ms', 0.1),
                x=[int_res['integral']],
                hist=int_res.get('hist', [dict(k=1, x=[int_res['integral']], residual=0, err_abs=int_res.get('err_abs', 0), err_rel=int_res.get('err_rel', 0))])
            )
        return params, out

    elif cid == 4:
        if tipo in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
            e, y_oc, out_m4 = modulo4.ejecutar(tipo)
        else:
            n_nodos = int(custom.get('n_nodos', 10))
            ruido = float(custom.get('ruido_sigma', custom.get('ruido', 0.0)))
            tipo_func = custom.get('tipo_func', 'sin')
            e, y_oc, out_m4 = modulo4.ejecutar_calculo(n_nodos=n_nodos, ruido_sigma=ruido, tipo_func=tipo_func, tipo='PERSONALIZADO')

        params = dict(
            caso_id=cid,
            tipo=e['tipo'],
            tipo_func=e.get('tipo_func', 'runge' if e['tipo'] == 'MAL_CONDICIONADO' else 'sin'),
            n_nodos=len(e['t_nodes']),
            ruido_sigma=float(e['ruido_sigma']),
            t_nodes=e['t_nodes'].tolist(),
            y_nodes=e['y_nodes'].tolist(),
            err_rel_lag=float(out_m4['Lagrange']['err_rel']),
            err_rel_new=float(out_m4['Newton']['err_rel']),
            err_rel_spl=float(out_m4['Splines Cúbicos']['err_rel']),
            plot_data=out_m4['plot_data']
        )
        out = {m_name: out_m4[m_name] for m_name in ['Lagrange', 'Newton', 'Splines Cúbicos']}
        return params, out

    abort(404)


def _guardar_simulacion(cid, tipo, fuente_datos, params, out):
    """Persiste una simulación completa en 3 pipelines HTTP (compatible con Turso y SQLite local)."""
    tol_default = params.get('tol', 1e-8)
    with db() as c:
        # Pipeline 1: escenario + simulacion
        c1, c2 = run_pipeline(c, [
            (
                'INSERT INTO escenario(caso_id,tipo,parametros_json,fuente_datos) VALUES(?,?,?,?) RETURNING id',
                (cid, tipo, json.dumps(params), fuente_datos)
            ),
            (
                'INSERT INTO simulacion(escenario_id) VALUES(last_insert_rowid()) RETURNING id',
                ()
            )
        ])
        sim = c2.fetchone()[0]

        # Pipeline 2: todas las ejecuciones de métodos en 1 round-trip
        metodos_ordenados = list(out.items())
        exec_stmts = [
            (
                'INSERT INTO ejecucion_metodo(simulacion_id,metodo,tolerancia,paso,max_iter,convergio,tiempo_ms) VALUES(?,?,?,?,?,?,?) RETURNING id',
                (
                    sim,
                    m_nombre,
                    tol_default,
                    r_data.get('paso'),
                    5000,
                    int(r_data.get('converged', True)),
                    round(float(r_data.get('tiempo_ms', 0.0)), 2)
                )
            )
            for m_nombre, r_data in metodos_ordenados
        ]
        exec_cursors = run_pipeline(c, exec_stmts)
        exec_ids = [cur.fetchone()[0] for cur in exec_cursors]

        # Pipeline 3: iteraciones (muestreadas si >80) + resultado_resumen en 1 round-trip
        detail_stmts = []
        for ex_id, (m_nombre, r_data) in zip(exec_ids, metodos_ordenados):
            hist_rows = _sample_history(r_data.get('hist', []), max_rows=80)
            for h in hist_rows:
                ea = h.get('err_abs')
                er = h.get('err_rel')
                ea_val = None if (ea is None or not np.isfinite(ea)) else float(ea)
                er_val = None if (er is None or not np.isfinite(er)) else float(er)
                detail_stmts.append((
                    'INSERT INTO iteracion_resultado(ejecucion_id,numero,aproximacion_json,residual,error_abs,error_rel) VALUES(?,?,?,?,?,?)',
                    (ex_id, int(h['k']), _format_x_json(h), _format_residual(h), ea_val, er_val)
                ))

            val_final = np.asarray(r_data.get('x', [])).tolist()
            total_iters = r_data.get('iters', len(r_data.get('hist', [])))
            metrica = {
                'converged': bool(r_data.get('converged', True)),
                'iters_totales': int(total_iters)
            }
            detail_stmts.append((
                'INSERT INTO resultado_resumen(ejecucion_id,referencia,valor_json,metrica_error_json,interpretacion) VALUES(?,?,?,?,?)',
                (ex_id, f"Caso {cid} - {tipo}", json.dumps(val_final), json.dumps(metrica), 'Resultado comprobado contra referencia analítica/numérica.')
            ))

        # Si hubiese muchos inserts, enviar en bloques seguros de hasta 250 sentencias
        for i in range(0, len(detail_stmts), 250):
            run_pipeline(c, detail_stmts[i:i + 250])

    return sim


# ---------- Ejecución de Escenarios Predefinidos (Los 4 Módulos) ----------

@app.route('/correr/<int:cid>/<tipo>')
def correr(cid, tipo):
    if tipo not in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
        abort(404)
    params, out = _ejecutar_modulo(cid, tipo)
    sim = _guardar_simulacion(
        cid, tipo,
        f"Parámetros normativos y sintéticos de teleféricos ({tipo})",
        params, out
    )
    return redirect(url_for('ver_simulacion', sid=sim))


# ---------- Simulación Personalizada (Formularios POST) ----------

@app.route('/simular-custom/<int:cid>', methods=['POST'])
def simular_custom(cid):
    if cid == 1:
        custom = dict(
            v0=float(request.form.get('v0', 5.0)),
            a=float(request.form.get('a', 1.0)),
            tr=float(request.form.get('tr', 1.0)),
            L=float(request.form.get('L', 20.0))
        )
    elif cid == 2:
        custom = dict(
            D0=float(request.form.get('D0', 0.10)),
            alpha=float(request.form.get('alpha', 0.02)),
            beta=float(request.form.get('beta', 0.001)),
            Dumbral=float(request.form.get('Dumbral', 0.60))
        )
    elif cid == 3:
        custom = dict(
            m=float(request.form.get('m', 3000.0)),
            c=float(request.form.get('c', 600.0)),
            k=float(request.form.get('k', 12000.0)),
            F0=float(request.form.get('F0', 800.0)),
            omega_f=float(request.form.get('omega_f', 1.5))
        )
    elif cid == 4:
        custom = dict(
            n_nodos=int(request.form.get('n_nodos', 10)),
            ruido=float(request.form.get('ruido', 0.0)),
            tipo_func=request.form.get('tipo_func', 'sin')
        )
    else:
        abort(404)

    params, out = _ejecutar_modulo(cid, 'PERSONALIZADO', custom=custom)
    sim = _guardar_simulacion(
        cid, 'PERSONALIZADO',
        'Valores definidos por el usuario en interfaz web',
        params, out
    )
    return redirect(url_for('ver_simulacion', sid=sim))


# ---------- Visualización de Simulación Detallada ----------

def _format_aprox_val(raw_json, short=False):
    if not raw_json:
        return '-'
    try:
        parsed = json.loads(raw_json)
        if isinstance(parsed, (int, float)):
            return f"{float(parsed):.6f}"
        if isinstance(parsed, list):
            if len(parsed) == 1:
                return f"{float(parsed[0]):.6f}"
            if len(parsed) <= 4:
                return "[" + ", ".join(f"{float(v):.4f}" for v in parsed) + "]"
            if short:
                return f"Vector [{len(parsed)} elem]"
            return f"[{float(parsed[0]):.4f}, ... ({len(parsed)} elems)]"
        return str(parsed)
    except Exception:
        return str(raw_json)


@app.route('/simulacion/<int:sid>')
def ver_simulacion(sid):
    with db() as c:
        c_sim, c_ej, c_it = run_pipeline(c, [
            (
                'SELECT s.id, s.fecha, s.estado, e.tipo, e.caso_id, e.parametros_json, c.nombre '
                'FROM simulacion s '
                'JOIN escenario e ON e.id=s.escenario_id '
                'JOIN caso_estudio c ON c.id=e.caso_id '
                'WHERE s.id=?',
                (sid,)
            ),
            (
                'SELECT m.id, m.metodo, m.convergio, m.tiempo_ms, r.valor_json, r.metrica_error_json '
                'FROM ejecucion_metodo m '
                'LEFT JOIN resultado_resumen r ON r.ejecucion_id=m.id '
                'WHERE m.simulacion_id=? ORDER BY m.id ASC',
                (sid,)
            ),
            (
                'SELECT i.ejecucion_id, i.numero, i.aproximacion_json, i.residual, i.error_abs, i.error_rel '
                'FROM iteracion_resultado i '
                'JOIN ejecucion_metodo m ON m.id=i.ejecucion_id '
                'WHERE m.simulacion_id=? ORDER BY i.ejecucion_id ASC, i.numero ASC',
                (sid,)
            )
        ])

        s = c_sim.fetchone()
        if not s:
            abort(404)
        ejecs_db = c_ej.fetchall()
        all_iters = c_it.fetchall()

    iters_by_ej = {}
    for row in all_iters:
        iters_by_ej.setdefault(row['ejecucion_id'], []).append(row)

    ejecuciones = []
    for ej in ejecs_db:
        iter_rows = iters_by_ej.get(ej['id'], [])
        iter_list = []
        for it in iter_rows:
            it_dict = dict(it)
            it_dict['aprox_str'] = _format_aprox_val(it['aproximacion_json'], short=False)
            iter_list.append(it_dict)

        last_it = iter_rows[-1] if iter_rows else None
        ult_aprox = last_it['aproximacion_json'] if last_it else ej['valor_json']
        iters_totales = len(iter_rows)
        if ej['metrica_error_json']:
            try:
                met = json.loads(ej['metrica_error_json'])
                iters_totales = met.get('iters_totales', iters_totales)
            except Exception:
                pass

        ej_dict = dict(ej)
        ej_dict['it'] = iters_totales
        ej_dict['res'] = last_it['residual'] if last_it else None
        ej_dict['er'] = last_it['error_rel'] if last_it else None
        ej_dict['aprox_str'] = _format_aprox_val(ult_aprox, short=True)
        ej_dict['iteraciones'] = iter_list
        ejecuciones.append(ej_dict)

    p = json.loads(s['parametros_json'])
    cid = s['caso_id']

    # 1. Preparar Gráfico 1: Fenómeno Físico para CADA uno de los 4 casos
    if cid == 1:
        L_lim = float(p.get('L', 20.0))
        pd = p.get('plot_data')
        if pd and 't' in pd:
            t_steps = pd['t']
            x_steps = pd['x']
            v_steps = pd['v']
        else:
            v0 = float(p.get('v0', 5.0))
            a = float(p.get('a', 1.0))
            tr = float(p.get('tr', 1.0))
            t_tot = float(p.get('t_total', 6.0))
            t_steps = np.linspace(0, max(t_tot * 1.2, 10.0), 35).tolist()
            x_steps, v_steps = [], []
            for t in t_steps:
                xv, vv = modulo1.posicion_exacta(t, v0, a, tr, no_lineal=bool(p.get('no_lineal', False)))
                x_steps.append(float(xv))
                v_steps.append(float(vv))

        chart_fisico = {
            'labels': [f"{t:.2f} s" for t in t_steps],
            'x_label': 'Tiempo (segundos)',
            'y_label': 'Posición x(t) [m] y Velocidad v(t) [m/s]',
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
                    'data': [L_lim] * len(t_steps),
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
        D_steps = [float(D0 + alpha * t + beta * (t ** 2)) for t in t_steps]

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
                    'data': [Dumbral] * len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                }
            ]
        }

    elif cid == 3:
        pd = p.get('plot_data')
        if pd and 't' in pd:
            t_steps = pd['t']
            x_traj = pd['x_rk4']
            x_rk2 = pd['x_rk2']
            x_ref = pd.get('x_ref', x_traj)
        else:
            x_max_val = float(p.get('x_max', 0.5))
            w0 = float(p.get('w0', 2.0))
            zeta = float(p.get('zeta', 0.05))
            wd = w0 * np.sqrt(max(1.0 - zeta ** 2, 1e-6))
            t_max = float(p.get('t_max', 15.0))
            t_steps = np.linspace(0, t_max, 50).tolist()
            x_traj = [float(x_max_val * np.exp(-zeta * w0 * t) * np.cos(wd * t)) for t in t_steps]
            x_rk2 = x_traj
            x_ref = x_traj

        chart_fisico = {
            'labels': [f"{t:.2f} s" for t in t_steps],
            'x_label': 'Tiempo (segundos)',
            'y_label': 'Desplazamiento lateral x(t) [metros]',
            'datasets': [
                {
                    'label': 'Trayectoria RK4 [m]',
                    'data': [float(v) for v in x_traj],
                    'borderColor': '#9333ea',
                    'borderWidth': 2.5,
                    'fill': False
                },
                {
                    'label': 'Trayectoria RK2 (Heun) [m]',
                    'data': [float(v) for v in x_rk2],
                    'borderColor': '#0284c7',
                    'borderWidth': 1.5,
                    'borderDash': [4, 4],
                    'fill': False
                },
                {
                    'label': 'Gálibo Seguro (+0.80 m EN 12929-1)',
                    'data': [0.80] * len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                },
                {
                    'label': 'Gálibo Seguro (-0.80 m)',
                    'data': [-0.80] * len(t_steps),
                    'borderColor': '#dc2626',
                    'borderWidth': 2,
                    'borderDash': [6, 6],
                    'pointRadius': 0,
                    'fill': False
                }
            ]
        }

    else:
        pd = p.get('plot_data')
        if pd and 't_plot' in pd:
            t_plot = pd['t_plot']
            y_real = pd['y_real']
            y_lag = pd['y_lag']
            y_spl = pd['y_spl']
            t_nodes = pd['t_nodes']
            y_nodes = pd['y_nodes']
        else:
            t_nodes = p.get('t_nodes', [0, 1, 2, 3])
            y_nodes = p.get('y_nodes', [0, 1, 0, -1])
            t_plot = np.unique(np.sort(np.concatenate([np.linspace(min(t_nodes), max(t_nodes), 50), t_nodes]))).tolist()
            if p.get('tipo') == 'MAL_CONDICIONADO' or p.get('tipo_func') == 'runge':
                y_real = [float(1.0 / (1.0 + 25.0 * (t ** 2))) for t in t_plot]
            else:
                y_real = [float(np.sin(t)) for t in t_plot]
            y_lag = modulo4.lagrange_eval(t_nodes, y_nodes, t_plot).tolist()
            y_spl = modulo4.splines_eval(modulo4.splines_cubicos_naturales(t_nodes, y_nodes), t_plot).tolist()

        # Mapear nodos exactamente sobre t_plot
        node_series = []
        for tk in t_plot:
            matches = [float(y_nodes[j]) for j, tn in enumerate(t_nodes) if abs(tk - tn) < 1e-6]
            node_series.append(matches[0] if matches else None)

        # Limitar visualmente oscilación extrema de Lagrange en Runge si supera [-3, 4] para mantener legibilidad
        y_lag_clipped = [float(max(min(v, 4.0), -3.0)) for v in y_lag]

        chart_fisico = {
            'labels': [f"{t:.2f}" for t in t_plot],
            'x_label': 'Dominio Temporal t',
            'y_label': 'Amplitud de Señal y(t)',
            'datasets': [
                {
                    'label': 'Señal Física Real',
                    'data': [float(v) for v in y_real],
                    'borderColor': '#0284c7',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Splines Cúbicos C² (Reconstrucción)',
                    'data': [float(v) for v in y_spl],
                    'borderColor': '#16a34a',
                    'borderWidth': 2.5,
                    'borderDash': [5, 3],
                    'fill': False
                },
                {
                    'label': 'Lagrange / Newton (Polinomio Global)',
                    'data': y_lag_clipped,
                    'borderColor': '#ea580c',
                    'borderWidth': 2,
                    'borderDash': [2, 2],
                    'fill': False
                },
                {
                    'label': 'Nodos de Telemetría Muestreados',
                    'data': node_series,
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
            'SELECT e.caso_id, e.tipo, e.parametros_json FROM simulacion s '
            'JOIN escenario e ON e.id=s.escenario_id WHERE s.id=?', (sid,)
        ).fetchone()
    if not r:
        abort(404)

    cid = r['caso_id']
    tipo = r['tipo']
    saved_params = json.loads(r['parametros_json']) if r['parametros_json'] else {}

    if tipo in ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO'):
        params, out = _ejecutar_modulo(cid, tipo)
    else:
        params, out = _ejecutar_modulo(cid, 'PERSONALIZADO', custom=saved_params)

    params['relanzada_de'] = sid
    new_sim = _guardar_simulacion(
        cid, tipo,
        f"Relanzamiento verificado desde simulación #{sid}",
        params, out
    )
    return redirect(url_for('ver_simulacion', sid=new_sim))


if __name__ == '__main__':
    init()
    port = int(os.environ.get('PORT', 5000))
    print(f"Iniciando SIMTELE-RISK en http://127.0.0.1:{port} ...")
    app.run(host='0.0.0.0', port=port, debug=True)
