"""
Módulo 1: Detención de Emergencia de Cabinas de Mi Teleférico.
Simulación con EDO (RK2 Heun, RK4), Integración numérica (Trapecio, Simpson 1/3) y Búsqueda de Raíces (v(t) = 0).
"""
import time
import numpy as np
from metodos import biseccion, newton_raphson, secante, trapecio_compuesto, simpson_13_compuesto


def escenario(tipo):
    if tipo == 'NORMAL':
        # Caso didáctico: v0=5 m/s, a=1.0 m/s^2, tr=1.0 s, L=20 m -> d_total = 17.5 m <= 20 m
        v0, a, tr, L = 5.0, 1.0, 1.0, 20.0
        h = 0.05
    elif tipo == 'ESTRES':
        # Mayor velocidad y tiempo de reacción: v0=7.0 m/s, a=0.7 m/s^2, tr=2.0 s, L=25 m -> d_total = 49.0 m > 25 m (ALERTA)
        v0, a, tr, L = 7.0, 0.7, 2.0, 25.0
        h = 0.05
    else:  # MAL_CONDICIONADO
        # Desaceleración no lineal dependiente de velocidad: dv/dt = -a * sqrt(v / v0)
        # Produce raíz de multiplicidad doble en v(t*)=0 (derivada v'(t*)=0), degradando Newton a convergencia lineal.
        v0, a, tr, L = 5.0, 0.8, 1.0, 25.0
        h = 0.02
    return dict(tipo=tipo, v0=v0, a=a, tr=tr, L=L, h=h)


def sol_analitica(v0, a, tr, no_lineal=False):
    """Solución analítica exacta para desaceleración constante o no lineal a(v)=a*sqrt(v/v0)."""
    d_reaccion = v0 * tr
    if no_lineal:
        # dv/dt = -a * sqrt(v/v0) -> v(t) = v0 * (1 - a*(t-tr)/(2*v0))^2
        tf = (2.0 * v0) / a
        t_total = tr + tf
        d_frenado = (2.0 * (v0 ** 2)) / (3.0 * a)
    else:
        tf = v0 / a
        t_total = tr + tf
        d_frenado = (v0 ** 2) / (2.0 * a)
    d_total = d_reaccion + d_frenado
    return dict(tf=tf, t_total=t_total, d_reaccion=d_reaccion, d_frenado=d_frenado, d_total=d_total)


def posicion_exacta(t, v0, a, tr, no_lineal=False):
    """Evalúa x(t) y v(t) exactos en cualquier instante t >= 0."""
    if t <= tr:
        return v0 * t, v0
    dt = t - tr
    if no_lineal:
        tf = (2.0 * v0) / a
        if dt >= tf:
            return v0 * tr + (2.0 * (v0 ** 2)) / (3.0 * a), 0.0
        u = 1.0 - (a * dt) / (2.0 * v0)
        v = v0 * (u ** 2)
        x = v0 * tr + (2.0 * (v0 ** 2) / (3.0 * a)) * (1.0 - (u ** 3))
        return x, v
    tf = v0 / a
    if dt >= tf:
        return v0 * tr + (v0 ** 2) / (2.0 * a), 0.0
    v = v0 - a * dt
    x = v0 * tr + v0 * dt - 0.5 * a * (dt ** 2)
    return x, v


def f_edo(t, y, v0, a, tr, no_lineal=False, braking=None):
    """
    Sistema de EDOs:
    y = [x, v], dx/dt = v, dv/dt = -a(v, t)
    """
    v = max(y[1], 0.0)
    is_braking = braking if braking is not None else (t >= tr - 1e-12)
    if not is_braking:
        dvdt = 0.0
    else:
        if no_lineal:
            dvdt = -a * np.sqrt(max(v / v0, 0.0)) if v > 1e-12 else 0.0
        else:
            dvdt = -a if v > 1e-12 else 0.0
    return np.array([v, dvdt])


def simular_rk(metodo, v0, a, tr, t_max, h, no_lineal=False):
    """Ejecuta RK2 (Heun) o RK4 hasta t_max o v=0, respetando la discontinuidad exacta en t = tr."""
    t_vals = [0.0]
    y_vals = [np.array([0.0, float(v0)])]

    t = 0.0
    y = np.array([0.0, float(v0)])

    t0_calc = time.perf_counter()
    k_step = 0
    while t < t_max:
        if t >= tr - 1e-12 and y[1] <= 1e-7:
            break

        in_reaction = t < tr - 1e-12
        dt = min(h, tr - t) if in_reaction else h
        braking_flag = not in_reaction

        if metodo == 'RK2 (Heun)':
            k1 = f_edo(t, y, v0, a, tr, no_lineal, braking=braking_flag)
            k2 = f_edo(t + dt, y + dt * k1, v0, a, tr, no_lineal, braking=braking_flag)
            y_next = y + (dt / 2.0) * (k1 + k2)
        else:  # RK4
            k1 = f_edo(t, y, v0, a, tr, no_lineal, braking=braking_flag)
            k2 = f_edo(t + dt / 2.0, y + (dt / 2.0) * k1, v0, a, tr, no_lineal, braking=braking_flag)
            k3 = f_edo(t + dt / 2.0, y + (dt / 2.0) * k2, v0, a, tr, no_lineal, braking=braking_flag)
            k4 = f_edo(t + dt, y + dt * k3, v0, a, tr, no_lineal, braking=braking_flag)
            y_next = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        y_next[1] = max(y_next[1], 0.0)
        t += dt
        k_step += 1
        y = y_next
        t_vals.append(t)
        y_vals.append(y.copy())

    tiempo_ms = (time.perf_counter() - t0_calc) * 1000.0
    d_final = float(y_vals[-1][0])
    t_final = float(t_vals[-1])

    return dict(
        metodo=metodo,
        t_vals=t_vals,
        x_vals=[float(val[0]) for val in y_vals],
        v_vals=[float(val[1]) for val in y_vals],
        d_final=d_final,
        t_final=t_final,
        pasos=k_step,
        tiempo_ms=tiempo_ms
    )


def ejecutar_calculo(v0, a, tr, L, h=0.05, no_lineal=False, tipo='PERSONALIZADO'):
    """Ejecuta RK2, RK4, búsqueda de raíces v(t)=0 e integración de v(t) para cualquier configuración."""
    analitica = sol_analitica(v0, a, tr, no_lineal=no_lineal)
    t_max = max(analitica['t_total'] * 1.5, 30.0)

    rk2 = simular_rk('RK2 (Heun)', v0, a, tr, t_max, h, no_lineal=no_lineal)
    rk4 = simular_rk('RK4', v0, a, tr, t_max, h, no_lineal=no_lineal)

    # Muestreo uniforme hasta el final de la trayectoria para historial y error paso a paso
    for r_sim in (rk2, rk4):
        n_pts = len(r_sim['t_vals'])
        idxs = np.unique(np.linspace(0, n_pts - 1, min(40, n_pts), dtype=int))
        hist = []
        for idx in idxs:
            ti = r_sim['t_vals'][idx]
            xi = r_sim['x_vals'][idx]
            vi = r_sim['v_vals'][idx]
            x_ex, _ = posicion_exacta(ti, v0, a, tr, no_lineal=no_lineal)
            ea = abs(xi - x_ex)
            er = ea / abs(x_ex) if abs(x_ex) > 1e-12 else 0.0
            hist.append(dict(k=int(idx), x=[float(xi)], residual=float(vi), err_abs=float(ea), err_rel=float(er)))
        r_sim['hist'] = hist
        r_sim['err_abs'] = abs(r_sim['d_final'] - analitica['d_total'])
        r_sim['err_rel'] = r_sim['err_abs'] / analitica['d_total']

    # Búsqueda de raíces para el instante de parada v(t) = 0 (t >= tr)
    if no_lineal:
        # Formulación continua con cambio de signo y derivada nula en la raíz (multiplicidad par -> convergencia lenta en Newton)
        f_v = lambda t: v0 * (1.0 - a * (t - tr) / (2.0 * v0)) * abs(1.0 - a * (t - tr) / (2.0 * v0))
        df_v = lambda t: -a * abs(1.0 - a * (t - tr) / (2.0 * v0))
    else:
        f_v = lambda t: v0 - a * (t - tr)
        df_v = lambda t: -a

    xr_t = analitica['t_total']
    t0_r = time.perf_counter()
    r_bis = biseccion(f_v, tr, t_max, xr=xr_t, tol=1e-8)
    r_bis['tiempo_ms'] = (time.perf_counter() - t0_r) * 1000.0

    t0_r = time.perf_counter()
    r_new = newton_raphson(f_v, df_v, x0=tr + 0.5, xr=xr_t, tol=1e-8)
    r_new['tiempo_ms'] = (time.perf_counter() - t0_r) * 1000.0

    t0_r = time.perf_counter()
    r_sec = secante(f_v, x0=tr + 0.2, x1=t_max, xr=xr_t, tol=1e-8)
    r_sec['tiempo_ms'] = (time.perf_counter() - t0_r) * 1000.0

    for r in [r_bis, r_new, r_sec]:
        r['x'] = [r['root']] if r.get('root') is not None else []
        for h_row in r.get('hist', []):
            if 'residual' not in h_row or h_row['residual'] is None:
                h_row['residual'] = abs(h_row.get('fx', 0.0))
            if isinstance(h_row.get('x'), (int, float)):
                h_row['x'] = [h_row['x']]

    # Integración numérica de v(t) con Trapecio compuesto y Simpson 1/3 compuesto (refinamiento)
    v_cont = lambda t: posicion_exacta(t, v0, a, tr, no_lineal=no_lineal)[1]
    t_end = analitica['t_total']

    t0_t = time.perf_counter()
    trap_hist = []
    for k_idx, n_sub in enumerate([10, 20, 40, 80, 160], start=1):
        val_n = trapecio_compuesto(v_cont, 0.0, t_end, n_sub)
        ea = abs(val_n - analitica['d_total'])
        er = ea / analitica['d_total']
        trap_hist.append(dict(k=k_idx, x=[float(val_n)], residual=float(ea), fx=val_n - analitica['d_total'], err_abs=float(ea), err_rel=float(er)))
    d_trap = trap_hist[-1]['x'][0]
    t_trap_ms = (time.perf_counter() - t0_t) * 1000.0

    t0_s = time.perf_counter()
    simp_hist = []
    for k_idx, n_sub in enumerate([10, 20, 40, 80, 160], start=1):
        val_n = simpson_13_compuesto(v_cont, 0.0, t_end, n_sub)
        ea = abs(val_n - analitica['d_total'])
        er = ea / analitica['d_total']
        simp_hist.append(dict(k=k_idx, x=[float(val_n)], residual=float(ea), fx=val_n - analitica['d_total'], err_abs=float(ea), err_rel=float(er)))
    d_simp = simp_hist[-1]['x'][0]
    t_simp_ms = (time.perf_counter() - t0_s) * 1000.0

    # Puntos muestreados para el gráfico físico
    n_plot = len(rk4['t_vals'])
    p_idxs = np.unique(np.linspace(0, n_plot - 1, min(40, n_plot), dtype=int))
    plot_data = dict(
        t=[float(rk4['t_vals'][i]) for i in p_idxs],
        x=[float(rk4['x_vals'][i]) for i in p_idxs],
        v=[float(rk4['v_vals'][i]) for i in p_idxs]
    )

    e = dict(tipo=tipo, v0=v0, a=a, tr=tr, L=L, h=h, no_lineal=no_lineal)
    out = {
        'RK2 (Heun)': rk2,
        'RK4': rk4,
        'Trapecio': dict(
            d_int=d_trap,
            err_abs=abs(d_trap - analitica['d_total']),
            err_rel=abs(d_trap - analitica['d_total']) / analitica['d_total'],
            tiempo_ms=t_trap_ms,
            hist=trap_hist
        ),
        'Simpson 1/3': dict(
            d_int=d_simp,
            err_abs=abs(d_simp - analitica['d_total']),
            err_rel=abs(d_simp - analitica['d_total']) / analitica['d_total'],
            tiempo_ms=t_simp_ms,
            hist=simp_hist
        ),
        'Raíces': dict(Bisección=r_bis, Newton=r_new, Secante=r_sec),
        'plot_data': plot_data
    }
    return e, analitica, out


def ejecutar(tipo):
    e = escenario(tipo)
    return ejecutar_calculo(
        e['v0'], e['a'], e['tr'], e['L'],
        h=e['h'], no_lineal=(tipo == 'MAL_CONDICIONADO'), tipo=tipo
    )
