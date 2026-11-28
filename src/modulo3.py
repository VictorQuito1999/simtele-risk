"""
Módulo 3: Oscilaciones de Cabinas por Viento Lateral.
Resuelve m x'' + c x' + k x = F(t) mediante EDO (RK2 Heun, RK4) e Integración de energía acumulada int(x^2 dt)
con Trapecio compuesto, Simpson 1/3 compuesto y Romberg.
"""
import time
import numpy as np
from metodos import trapecio_compuesto, simpson_13_compuesto, romberg, splines_cubicos_naturales, splines_eval


def escenario(tipo):
    if tipo == 'NORMAL':
        # Vibración libre subamortiguada: m=3000 kg, c=600 Ns/m, k=12000 N/m, F0=0
        m, c, k, F0, omega_f = 3000.0, 600.0, 12000.0, 0.0, 0.0
        x0, v0 = 0.5, 0.0
        t_max, h = 15.0, 0.02
    elif tipo == 'ESTRES':
        # Ráfaga periódica cercana a resonancia: F0=1500 N, omega_f=1.90 rad/s (w0=2.0)
        m, c, k, F0, omega_f = 3000.0, 600.0, 12000.0, 1500.0, 1.90
        x0, v0 = 0.0, 0.0
        t_max, h = 20.0, 0.02
    else:  # MAL_CONDICIONADO / RESONANCIA PURA
        # Amortiguamiento casi nulo c=6 Ns/m (zeta ~ 0.0005) y resonancia exacta omega_f=w0=2.0 rad/s
        m, c, k, F0, omega_f = 3000.0, 6.0, 12000.0, 1000.0, 2.0
        x0, v0 = 0.0, 0.0
        t_max, h = 25.0, 0.05

    w0 = np.sqrt(k / m)
    zeta = c / (2.0 * np.sqrt(k * m))
    wd = w0 * np.sqrt(max(1.0 - zeta ** 2, 1e-8))

    return dict(
        tipo=tipo, m=m, c=c, k=k, F0=F0, omega_f=omega_f,
        x0=x0, v0=v0, t_max=t_max, h=h, w0=w0, zeta=zeta, wd=wd
    )


def sol_analitica_libre(t_arr, x0, v0, zeta, w0, wd):
    """Solución analítica exacta en régimen subamortiguado libre (F=0)."""
    C1 = x0
    C2 = (v0 + zeta * w0 * x0) / wd
    exp_factor = np.exp(-zeta * w0 * t_arr)
    return exp_factor * (C1 * np.cos(wd * t_arr) + C2 * np.sin(wd * t_arr))


def f_osc(t, y, m, c, k, F0, omega_f):
    """dx/dt = v; dv/dt = (F(t) - c v - k x) / m."""
    x, v = y[0], y[1]
    F_ext = F0 * np.cos(omega_f * t) if F0 > 0 else 0.0
    dvdt = (F_ext - c * v - k * x) / m
    return np.array([v, dvdt])


def simular(metodo, e):
    m, c, k, F0, omega_f = e['m'], e['c'], e['k'], e['F0'], e['omega_f']
    t_max, h = e['t_max'], e['h']

    t_vals = [0.0]
    y_vals = [np.array([float(e['x0']), float(e['v0'])])]

    t = 0.0
    y = np.array([float(e['x0']), float(e['v0'])])

    t0_calc = time.perf_counter()
    k_step = 0
    while t < t_max - 1e-12:
        if metodo == 'RK2 (Heun)':
            k1 = f_osc(t, y, m, c, k, F0, omega_f)
            k2 = f_osc(t + h, y + h * k1, m, c, k, F0, omega_f)
            y_next = y + (h / 2.0) * (k1 + k2)
        else:  # RK4
            k1 = f_osc(t, y, m, c, k, F0, omega_f)
            k2 = f_osc(t + h / 2.0, y + (h / 2.0) * k1, m, c, k, F0, omega_f)
            k3 = f_osc(t + h / 2.0, y + (h / 2.0) * k2, m, c, k, F0, omega_f)
            k4 = f_osc(t + h, y + h * k3, m, c, k, F0, omega_f)
            y_next = y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        t += h
        k_step += 1
        y = y_next
        t_vals.append(t)
        y_vals.append(y.copy())

    tiempo_ms = (time.perf_counter() - t0_calc) * 1000.0
    x_arr = np.array([float(val[0]) for val in y_vals])
    v_arr = np.array([float(val[1]) for val in y_vals])

    return dict(
        metodo=metodo,
        t_vals=t_vals,
        x_vals=x_arr.tolist(),
        v_vals=v_arr.tolist(),
        x_max=float(np.max(np.abs(x_arr))),
        tiempo_ms=tiempo_ms,
        pasos=k_step
    )


def ejecutar_calculo(e):
    """Ejecuta RK2, RK4, y las 3 cuadraturas (Trapecio, Simpson 1/3, Romberg) sobre x(t)^2."""
    rk2 = simular('RK2 (Heun)', e)
    rk4 = simular('RK4', e)

    t_arr = np.array(rk4['t_vals'])
    x_arr_rk4 = np.array(rk4['x_vals'])
    x_arr_rk2 = np.array(rk2['x_vals'])

    if e['F0'] == 0:
        x_exact = sol_analitica_libre(t_arr, e['x0'], e['v0'], e['zeta'], e['w0'], e['wd'])
    else:
        # Referencia numérica de alta precisión (RK4 con paso h/4) para régimen forzado
        e_ref = dict(e, h=e['h'] / 4.0)
        rk4_ref = simular('RK4', e_ref)
        t_ref = np.array(rk4_ref['t_vals'])
        x_ref_dense = np.array(rk4_ref['x_vals'])
        x_exact = np.interp(t_arr, t_ref, x_ref_dense)

    max_ref = float(np.max(np.abs(x_exact))) + 1e-12
    rk2['err_abs'] = float(np.max(np.abs(x_arr_rk2 - x_exact)))
    rk2['err_rel'] = rk2['err_abs'] / max_ref
    rk4['err_abs'] = float(np.max(np.abs(x_arr_rk4 - x_exact)))
    rk4['err_rel'] = rk4['err_abs'] / max_ref

    # Historial muestreado uniformemente hasta t_max para ambos RK
    n_pts = len(t_arr)
    idxs = np.unique(np.linspace(0, n_pts - 1, min(40, n_pts), dtype=int))
    for r_sim, x_arr in ((rk2, x_arr_rk2), (rk4, x_arr_rk4)):
        r_sim['hist'] = [
            dict(
                k=int(i),
                x=[float(x_arr[i])],
                residual=float(r_sim['v_vals'][i]),
                err_abs=float(abs(x_arr[i] - x_exact[i])),
                err_rel=float(abs(x_arr[i] - x_exact[i]) / max_ref)
            )
            for i in idxs
        ]

    # Función continua x(t)^2 para evaluar Trapecio, Simpson 1/3 y Romberg en TODOS los escenarios
    if e['F0'] == 0:
        x2_func = lambda t: float((sol_analitica_libre(np.array([t]), e['x0'], e['v0'], e['zeta'], e['w0'], e['wd'])[0]) ** 2)
    else:
        spl_x = splines_cubicos_naturales(t_arr, x_arr_rk4)
        x2_func = lambda t: float((splines_eval(spl_x, t)[0]) ** 2)

    t0_r = time.perf_counter()
    int_romb = romberg(x2_func, 0.0, float(t_arr[-1]), tol=1e-8, max_k=8)
    t_romb_ms = (time.perf_counter() - t0_r) * 1000.0
    int_ref = int_romb['integral']

    t0_t = time.perf_counter()
    trap_hist = []
    for k_idx, n_sub in enumerate([20, 40, 80, 160], start=1):
        val = trapecio_compuesto(x2_func, 0.0, float(t_arr[-1]), n_sub)
        ea = abs(val - int_ref)
        er = ea / (abs(int_ref) + 1e-12)
        trap_hist.append(dict(k=k_idx, x=[float(val)], residual=float(ea), err_abs=float(ea), err_rel=float(er)))
    int_trap = trap_hist[-1]['x'][0]
    t_trap_ms = (time.perf_counter() - t0_t) * 1000.0

    t0_s = time.perf_counter()
    simp_hist = []
    for k_idx, n_sub in enumerate([20, 40, 80, 160], start=1):
        val = simpson_13_compuesto(x2_func, 0.0, float(t_arr[-1]), n_sub)
        ea = abs(val - int_ref)
        er = ea / (abs(int_ref) + 1e-12)
        simp_hist.append(dict(k=k_idx, x=[float(val)], residual=float(ea), err_abs=float(ea), err_rel=float(er)))
    int_simp = simp_hist[-1]['x'][0]
    t_simp_ms = (time.perf_counter() - t0_s) * 1000.0

    romb_table = int_romb['table']
    romb_hist = []
    for k_idx in range(romb_table.shape[0]):
        val = float(romb_table[k_idx, k_idx])
        ea = abs(val - int_ref)
        er = ea / (abs(int_ref) + 1e-12)
        romb_hist.append(dict(k=k_idx + 1, x=[val], residual=float(ea), err_abs=float(ea), err_rel=float(er)))

    # Datos muestreados para el gráfico físico real
    p_idxs = np.unique(np.linspace(0, n_pts - 1, min(60, n_pts), dtype=int))
    plot_data = dict(
        t=[float(t_arr[i]) for i in p_idxs],
        x_rk4=[float(x_arr_rk4[i]) for i in p_idxs],
        x_rk2=[float(x_arr_rk2[i]) for i in p_idxs],
        x_ref=[float(x_exact[i]) for i in p_idxs]
    )

    out = {
        'RK2 (Heun)': rk2,
        'RK4': rk4,
        'Trapecio': dict(integral=int_trap, err_abs=trap_hist[-1]['err_abs'], err_rel=trap_hist[-1]['err_rel'], tiempo_ms=t_trap_ms, hist=trap_hist),
        'Simpson 1/3': dict(integral=int_simp, err_abs=simp_hist[-1]['err_abs'], err_rel=simp_hist[-1]['err_rel'], tiempo_ms=t_simp_ms, hist=simp_hist),
        'Romberg': dict(integral=int_ref, err_abs=0.0, err_rel=0.0, steps=int_romb.get('steps', 1), tiempo_ms=t_romb_ms, hist=romb_hist),
        'plot_data': plot_data
    }
    return e, x_exact.tolist(), out


def ejecutar(tipo):
    e = escenario(tipo)
    return ejecutar_calculo(e)
