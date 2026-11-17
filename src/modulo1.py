"""
Módulo 1: Detención de Emergencia de Cabinas de Mi Teleférico.
Simulación con EDO (RK2 Heun, RK4), Integración numérica (Trapecio, Simpson 1/3) y Búsqueda de Raíces.
"""
import time
import numpy as np
from metodos import err_abs, err_rel, biseccion, newton_raphson, secante

def escenario(tipo):
    if tipo == 'NORMAL':
        # Caso didáctico: v0=5 m/s, a=1.0 m/s^2, tr=1.0 s, L=20 m -> d_total = 17.5 m <= 20 m
        v0, a, tr, L = 5.0, 1.0, 1.0, 20.0
        h = 0.05
    elif tipo == 'ESTRES':
        # Mayor velocidad y tiempo de reacción: v0=7.0 m/s, a=0.7 m/s^2, tr=2.0 s, L=25 m -> d_total = 14 + 35 = 49 m > 25 m (ALERTA)
        v0, a, tr, L = 7.0, 0.7, 2.0, 25.0
        h = 0.1
    else:  # MAL_CONDICIONADO / COMPLEJO
        # Desaceleración no lineal dependiente de la velocidad a(v) = a0 * sqrt(max(v, 0)/v0)
        v0, a, tr, L = 5.0, 0.8, 1.0, 25.0
        h = 0.01
    return dict(tipo=tipo, v0=v0, a=a, tr=tr, L=L, h=h)

def sol_analitica(v0, a, tr):
    """Solución analítica exacta para desaceleración constante."""
    tf = v0 / a
    t_total = tr + tf
    d_reaccion = v0 * tr
    d_frenado = (v0**2) / (2.0 * a)
    d_total = d_reaccion + d_frenado
    return dict(tf=tf, t_total=t_total, d_reaccion=d_reaccion, d_frenado=d_frenado, d_total=d_total)

def f_edo(t, y, v0, a, tr, no_lineal=False):
    """
    Sistema de EDOs:
    y = [x, v]
    dx/dt = v
    dv/dt = -a(v, t)
    """
    x, v = y[0], max(y[1], 0.0)
    if t <= tr:
        dvdt = 0.0
    else:
        if no_lineal:
            dvdt = -a * np.sqrt(max(v / v0, 0.0) + 1e-12)
        else:
            dvdt = -a if v > 1e-12 else 0.0
    dxdt = v
    return np.array([dxdt, dvdt])

def simular_rk(metodo, v0, a, tr, t_max, h, no_lineal=False):
    """Ejecuta RK2 (Heun) o RK4 hasta t_max o v=0."""
    t_vals = [0.0]
    y_vals = [np.array([0.0, float(v0)])]
    
    t = 0.0
    y = np.array([0.0, float(v0)])
    
    t0_calc = time.perf_counter()
    k_step = 0
    while t < t_max:
        if t > tr and y[1] <= 1e-7:
            break
        
        if metodo == 'RK2 (Heun)':
            k1 = f_edo(t, y, v0, a, tr, no_lineal)
            k2 = f_edo(t + h, y + h * k1, v0, a, tr, no_lineal)
            y_next = y + (h / 2.0) * (k1 + k2)
        else:  # RK4
            k1 = f_edo(t, y, v0, a, tr, no_lineal)
            k2 = f_edo(t + h/2.0, y + (h/2.0) * k1, v0, a, tr, no_lineal)
            k3 = f_edo(t + h/2.0, y + (h/2.0) * k2, v0, a, tr, no_lineal)
            k4 = f_edo(t + h, y + h * k3, v0, a, tr, no_lineal)
            y_next = y + (h / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
        y_next[1] = max(y_next[1], 0.0)
        t += h
        k_step += 1
        y = y_next
        t_vals.append(t)
        y_vals.append(y.copy())
    
    tiempo_ms = (time.perf_counter() - t0_calc) * 1000.0
    d_final = y_vals[-1][0]
    t_final = t_vals[-1]
    
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

def ejecutar(tipo):
    e = escenario(tipo)
    v0, a, tr, L, h = e['v0'], e['a'], e['tr'], e['L'], e['h']
    no_lineal = (tipo == 'MAL_CONDICIONADO')
    
    analitica = sol_analitica(v0, a, tr)
    t_max = max(analitica['t_total'] * 1.5, 30.0)
    
    rk2 = simular_rk('RK2 (Heun)', v0, a, tr, t_max, h, no_lineal)
    rk4 = simular_rk('RK4', v0, a, tr, t_max, h, no_lineal)
    
    # Raíz del instante de detención v(t) = 0 en fase de frenado
    # Función continua: v(t) = v0 - a*(t - tr) para t > tr
    f_v = lambda t: v0 - a * (t - tr)
    df_v = lambda t: -a
    
    xr_t = analitica['t_total']
    r_bis = biseccion(f_v, tr, t_max, xr=xr_t, tol=1e-8)
    r_new = newton_raphson(f_v, df_v, x0=tr + 0.5, xr=xr_t, tol=1e-8)
    r_sec = secante(f_v, x0=tr, x1=t_max, xr=xr_t, tol=1e-8)
    
    # Integración de v(t) para distancia de frenado
    # Trapecio compuesto y Simpson sobre los puntos de RK4
    v_arr = np.array(rk4['v_vals'])
    t_arr = np.array(rk4['t_vals'])
    d_trap = float(np.trapezoid(v_arr, t_arr))
    
    # Errores frente a analítica
    rk2['err_abs'] = abs(rk2['d_final'] - analitica['d_total'])
    rk2['err_rel'] = rk2['err_abs'] / analitica['d_total']
    rk4['err_abs'] = abs(rk4['d_final'] - analitica['d_total'])
    rk4['err_rel'] = rk4['err_abs'] / analitica['d_total']
    
    out = {
        'RK2 (Heun)': rk2,
        'RK4': rk4,
        'Trapecio': dict(d_int=d_trap, err_abs=abs(d_trap - analitica['d_total']), err_rel=abs(d_trap - analitica['d_total'])/analitica['d_total']),
        'Raíces': dict(Bisección=r_bis, Newton=r_new, Secante=r_sec)
    }
    
    return e, analitica, out
