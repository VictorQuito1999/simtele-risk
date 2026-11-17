"""
Módulo 4: Reconstrucción de Señales de Sensores de Mi Teleférico.
Compara Interpolación de Lagrange, Newton por Diferencias Divididas y Splines Cúbicos Naturales frente a Nodos Equiespaciados, Ruido y Fenómeno de Runge.
"""
import time
import numpy as np
from metodos import lagrange_eval, newton_dif_div, newton_eval, splines_cubicos_naturales, splines_eval

def escenario(tipo):
    if tipo == 'NORMAL':
        # Señal continua de velocidad/tensión y(t) = sin(t) en [0, pi], 10 nodos, sin ruido
        a, b_dom = 0.0, np.pi
        n_nodos = 10
        t_nodes = np.linspace(a, b_dom, n_nodos)
        func_real = lambda t: np.sin(t)
        ruido_sigma = 0.0
        t_ocultos = (t_nodes[:-1] + t_nodes[1:]) / 2.0 # puntos medios ocultados
    elif tipo == 'ESTRES':
        # Pérdida de un bloque continuo de datos (gap central de 40%) con ruido gaussiano sigma=0.08
        a, b_dom = 0.0, np.pi
        t_all = np.linspace(a, b_dom, 16)
        # Quitar el 40% central
        mascara = (t_all < 1.0) | (t_all > 2.2)
        t_nodes = t_all[mascara]
        func_real = lambda t: np.sin(t)
        ruido_sigma = 0.08
        t_ocultos = t_all[~mascara] # datos perdidos a reconstruir
    else: # MAL_CONDICIONADO: Fenómeno de Runge
        # Función de Runge f(t) = 1 / (1 + 25*t^2) en [-1, 1] con 14 nodos equiespaciados
        a, b_dom = -1.0, 1.0
        n_nodos = 14
        t_nodes = np.linspace(a, b_dom, n_nodos)
        func_real = lambda t: 1.0 / (1.0 + 25.0 * (t**2))
        ruido_sigma = 0.0
        t_ocultos = np.array([-0.95, -0.85, 0.85, 0.95]) # extremos críticos de oscilación
        
    y_nodes_clean = np.array([func_real(ti) for ti in t_nodes])
    if ruido_sigma > 0:
        rng = np.random.default_rng(42)
        y_nodes = y_nodes_clean + rng.normal(0, ruido_sigma, len(t_nodes))
    else:
        y_nodes = y_nodes_clean
        
    return dict(
        tipo=tipo, a=a, b_dom=b_dom, t_nodes=t_nodes, y_nodes=y_nodes,
        func_real=func_real, ruido_sigma=ruido_sigma, t_ocultos=t_ocultos
    )

def ejecutar(tipo):
    e = escenario(tipo)
    t_nodes, y_nodes = e['t_nodes'], e['y_nodes']
    func_real = e['func_real']
    t_ocultos = e['t_ocultos']
    
    # 1. Lagrange
    t0 = time.perf_counter()
    y_lag_eval = lambda x_ev: lagrange_eval(t_nodes, y_nodes, x_ev)
    y_ocultos_lag = y_lag_eval(t_ocultos)
    tiempo_lag = (time.perf_counter() - t0) * 1000.0
    
    # 2. Newton
    t0 = time.perf_counter()
    coefs_new = newton_dif_div(t_nodes, y_nodes)
    y_new_eval = lambda x_ev: newton_eval(t_nodes, coefs_new, x_ev)
    y_ocultos_new = y_new_eval(t_ocultos)
    tiempo_new = (time.perf_counter() - t0) * 1000.0
    
    # 3. Splines Cúbicos
    t0 = time.perf_counter()
    spl = splines_cubicos_naturales(t_nodes, y_nodes)
    y_spl_eval = lambda x_ev: splines_eval(spl, x_ev)
    y_ocultos_spl = y_spl_eval(t_ocultos)
    tiempo_spl = (time.perf_counter() - t0) * 1000.0
    
    # Evaluación de precisión en los puntos ocultados
    y_real_ocultos = np.array([func_real(ti) for ti in t_ocultos])
    
    err_abs_lag = float(np.mean(np.abs(y_ocultos_lag - y_real_ocultos)))
    err_rel_lag = err_abs_lag / float(np.mean(np.abs(y_real_ocultos)) + 1e-12)
    
    err_abs_new = float(np.mean(np.abs(y_ocultos_new - y_real_ocultos)))
    err_rel_new = err_abs_new / float(np.mean(np.abs(y_real_ocultos)) + 1e-12)
    
    err_abs_spl = float(np.mean(np.abs(y_ocultos_spl - y_real_ocultos)))
    err_rel_spl = err_abs_spl / float(np.mean(np.abs(y_real_ocultos)) + 1e-12)
    
    # Puntos densos para graficar la reconstrucción continua
    t_plot = np.linspace(e['a'], e['b_dom'], 80)
    y_real_plot = np.array([func_real(ti) for ti in t_plot])
    y_lag_plot = y_lag_eval(t_plot)
    y_spl_plot = y_spl_eval(t_plot)
    
    out = {
        'Lagrange': dict(
            converged=True,
            iters=len(t_nodes),
            tiempo_ms=tiempo_lag,
            err_abs=err_abs_lag,
            err_rel=err_rel_lag,
            x=[err_rel_lag],
            hist=[dict(k=i, x=[float(y_ocultos_lag[i])], residual=abs(y_ocultos_lag[i] - y_real_ocultos[i]), err_abs=abs(y_ocultos_lag[i] - y_real_ocultos[i]), err_rel=abs(y_ocultos_lag[i] - y_real_ocultos[i])/(abs(y_real_ocultos[i])+1e-12)) for i in range(len(t_ocultos))]
        ),
        'Newton': dict(
            converged=True,
            iters=len(t_nodes),
            tiempo_ms=tiempo_new,
            err_abs=err_abs_new,
            err_rel=err_rel_new,
            x=[err_rel_new],
            hist=[dict(k=i, x=[float(y_ocultos_new[i])], residual=abs(y_ocultos_new[i] - y_real_ocultos[i]), err_abs=abs(y_ocultos_new[i] - y_real_ocultos[i]), err_rel=abs(y_ocultos_new[i] - y_real_ocultos[i])/(abs(y_real_ocultos[i])+1e-12)) for i in range(len(t_ocultos))]
        ),
        'Splines Cúbicos': dict(
            converged=True,
            iters=len(t_nodes),
            tiempo_ms=tiempo_spl,
            err_abs=err_abs_spl,
            err_rel=err_rel_spl,
            x=[err_rel_spl],
            hist=[dict(k=i, x=[float(y_ocultos_spl[i])], residual=abs(y_ocultos_spl[i] - y_real_ocultos[i]), err_abs=abs(y_ocultos_spl[i] - y_real_ocultos[i]), err_rel=abs(y_ocultos_spl[i] - y_real_ocultos[i])/(abs(y_real_ocultos[i])+1e-12)) for i in range(len(t_ocultos))]
        ),
        'plot_data': dict(
            t_plot=t_plot.tolist(),
            y_real=y_real_plot.tolist(),
            y_lag=y_lag_plot.tolist(),
            y_spl=y_spl_plot.tolist(),
            t_nodes=t_nodes.tolist(),
            y_nodes=y_nodes.tolist()
        )
    }
    
    return e, y_real_ocultos.tolist(), out
