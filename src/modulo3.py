"""
Módulo 3: Oscilaciones de Cabinas por Viento Lateral.
Resuelve m x'' + c x' + k x = F(t) mediante EDO (RK2 Heun, RK4) e Integración de energía acumulada int(x^2 dt).
"""
import time
import numpy as np
from metodos import trapecio_compuesto, simpson_13_compuesto, romberg

def escenario(tipo):
    if tipo == 'NORMAL':
        # Vibración libre subamortiguada: m=3000 kg, c=600 Ns/m, k=12000 N/m, F0=0
        m, c, k, F0, omega_f = 3000.0, 600.0, 12000.0, 0.0, 0.0
        x0, v0 = 0.5, 0.0
        t_max, h = 15.0, 0.02
    elif tipo == 'ESTRES':
        # Ráfaga periódica resonante: F0=1500 N, omega_f=1.90 rad/s (cerca de w0=2.0)
        m, c, k, F0, omega_f = 3000.0, 600.0, 12000.0, 1500.0, 1.90
        x0, v0 = 0.0, 0.0
        t_max, h = 20.0, 0.02
    else: # MAL_CONDICIONADO / RESONANCIA PURA
        # Amortiguamiento casi nulo c=6 Ns/m (zeta ~ 0.0005) y resonancia exacta omega_f=w0=2.0 rad/s
        m, c, k, F0, omega_f = 3000.0, 6.0, 12000.0, 1000.0, 2.0
        x0, v0 = 0.0, 0.0
        t_max, h = 25.0, 0.05
        
    w0 = np.sqrt(k / m)
    zeta = c / (2.0 * np.sqrt(k * m))
    wd = w0 * np.sqrt(max(1.0 - zeta**2, 1e-8))
    
    return dict(
        tipo=tipo, m=m, c=c, k=k, F0=F0, omega_f=omega_f,
        x0=x0, v0=v0, t_max=t_max, h=h, w0=w0, zeta=zeta, wd=wd
    )

def sol_analitica_libre(t_arr, x0, v0, zeta, w0, wd):
    """Solución analítica exacta en régimen subamortiguado libre (F=0)."""
    C1 = x0
    C2 = (v0 + zeta * w0 * x0) / wd
    exp_factor = np.exp(-zeta * w0 * t_arr)
    x_exact = exp_factor * (C1 * np.cos(wd * t_arr) + C2 * np.sin(wd * t_arr))
    return x_exact

def f_osc(t, y, m, c, k, F0, omega_f):
    """
    y = [x, v]
    dx/dt = v
    dv/dt = (F(t) - c v - k x) / m
    """
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
    while t < t_max:
        if metodo == 'RK2 (Heun)':
            k1 = f_osc(t, y, m, c, k, F0, omega_f)
            k2 = f_osc(t + h, y + h * k1, m, c, k, F0, omega_f)
            y_next = y + (h / 2.0) * (k1 + k2)
        else: # RK4
            k1 = f_osc(t, y, m, c, k, F0, omega_f)
            k2 = f_osc(t + h/2.0, y + (h/2.0) * k1, m, c, k, F0, omega_f)
            k3 = f_osc(t + h/2.0, y + (h/2.0) * k2, m, c, k, F0, omega_f)
            k4 = f_osc(t + h, y + h * k3, m, c, k, F0, omega_f)
            y_next = y + (h / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            
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

def ejecutar(tipo):
    e = escenario(tipo)
    rk2 = simular('RK2 (Heun)', e)
    rk4 = simular('RK4', e)
    
    t_arr = np.array(rk4['t_vals'])
    x_arr_rk4 = np.array(rk4['x_vals'])
    
    # Si es NORMAL, hay solución analítica exacta
    if e['tipo'] == 'NORMAL':
        x_exact = sol_analitica_libre(t_arr, e['x0'], e['v0'], e['zeta'], e['w0'], e['wd'])
        rk2['err_abs'] = float(np.max(np.abs(np.array(rk2['x_vals']) - x_exact)))
        rk2['err_rel'] = rk2['err_abs'] / float(np.max(np.abs(x_exact)))
        rk4['err_abs'] = float(np.max(np.abs(x_arr_rk4 - x_exact)))
        rk4['err_rel'] = rk4['err_abs'] / float(np.max(np.abs(x_exact)))
    else:
        # En forzada, tomamos RK4 como referencia de alta precisión
        x_exact = x_arr_rk4
        rk4['err_abs'] = 0.0
        rk4['err_rel'] = 0.0
        rk2['err_abs'] = float(np.max(np.abs(np.array(rk2['x_vals']) - x_arr_rk4)))
        rk2['err_rel'] = rk2['err_abs'] / float(np.max(np.abs(x_arr_rk4)) + 1e-12)
        
    # Integración de la energía acumulada int(x^2 dt)
    # Función x^2 sobre los puntos temporales
    x2_func = lambda t: (sol_analitica_libre(np.array([t]), e['x0'], e['v0'], e['zeta'], e['w0'], e['wd'])[0])**2 if e['tipo']=='NORMAL' else 0.0
    
    if e['tipo'] == 'NORMAL':
        int_trap = trapecio_compuesto(x2_func, 0.0, e['t_max'], 200)
        int_simp = simpson_13_compuesto(x2_func, 0.0, e['t_max'], 200)
        int_romb = romberg(x2_func, 0.0, e['t_max'], tol=1e-8)
        int_ref = int_romb['integral']
    else:
        int_trap = float(np.trapezoid(x_arr_rk4**2, t_arr))
        int_simp = int_trap # aproximación
        int_ref = int_trap
        int_romb = dict(integral=int_ref, steps=1)
        
    out = {
        'RK2 (Heun)': rk2,
        'RK4': rk4,
        'Trapecio': dict(integral=int_trap, err_rel=abs(int_trap - int_ref)/(abs(int_ref)+1e-12)),
        'Simpson 1/3': dict(integral=int_simp, err_rel=abs(int_simp - int_ref)/(abs(int_ref)+1e-12)),
        'Romberg': dict(integral=int_romb['integral'], err_rel=0.0, steps=int_romb.get('steps', 1))
    }
    
    return e, x_exact.tolist(), out
