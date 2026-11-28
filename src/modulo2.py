"""Módulo 2 (Deterioro y mantenimiento): calibración A x = b + búsqueda de raíces para D(t) = D_umbral."""
import time
import numpy as np
from metodos import *

# ---------- Parámetros y Escenarios ----------
def escenario(tipo, seed=42):
    if tipo == 'NORMAL':
        # Calibración
        n = 4; A = tridiag(n); xs = np.arange(1, n+1, dtype=float); tol = 1e-8; pert = 0
        # Modelo de deterioro D(t) = D0 + alpha*t + beta*t^2 (t en meses)
        D0, alpha, beta, D_umbral = 0.10, 0.02, 0.001, 0.60
    elif tipo == 'ESTRES':
        # Calibración en dimensión alta con perturbación
        n = 50; A = tridiag(n); xs = np.linspace(1, 4, n); tol = 1e-12; pert = 0.03
        # Mantenimiento retrasado / condiciones severas de altitud (La Paz-El Alto)
        D0, alpha, beta, D_umbral = 0.15, 0.05, 0.004, 0.60
    else:  # MAL_CONDICIONADO
        # Calibración con matriz de Hilbert
        n = 4; A = hilbert(n); xs = np.arange(1, n+1, dtype=float); tol = 1e-8; pert = 1e-6
        # Derivada casi nula en el umbral (raíz casi múltiple, D'(t*) -> 0)
        D0, alpha, beta, D_umbral = 0.5999, 1e-5, 1e-5, 0.60
    
    b = A @ xs
    if pert:
        rng = np.random.default_rng(seed); b = b * (1 + pert * rng.uniform(-1, 1, n))
    
    return dict(tipo=tipo, A=A, b=b, xs=xs, tol=tol, pert=pert,
                D0=D0, alpha=alpha, beta=beta, D_umbral=D_umbral)

def calcular_tiempo_umbral(D0, alpha, beta, D_umbral, tol=1e-8):
    """Calcula el tiempo al umbral t* resolviendo D(t) - D_umbral = 0."""
    disc = alpha**2 - 4 * beta * (D0 - D_umbral)
    if disc >= 0 and beta > 0:
        t_exacto = (-alpha + np.sqrt(disc)) / (2 * beta)
    else:
        t_exacto = (D_umbral - D0) / alpha if alpha > 0 else float('nan')

    f = lambda t: beta * t**2 + alpha * t + (D0 - D_umbral)
    df = lambda t: 2 * beta * t + alpha

    b_sup = max(60.0, 2.0 * t_exacto) if np.isfinite(t_exacto) and t_exacto > 0 else 60.0

    out_raices = {}
    # Bisección
    t0 = time.perf_counter()
    r_bis = biseccion(f, 0.0, b_sup, xr=t_exacto, tol=tol)
    r_bis['tiempo_ms'] = (time.perf_counter() - t0) * 1000.0
    r_bis['x'] = [r_bis['root']] if r_bis['root'] is not None else []
    for h_row in r_bis['hist']: h_row['residual'] = h_row.get('fx')
    out_raices['Bisección'] = r_bis

    # Newton-Raphson
    t0 = time.perf_counter()
    x0 = 1.0 if t_exacto > 1.0 else 0.1
    r_new = newton_raphson(f, df, x0=x0, xr=t_exacto, tol=tol)
    r_new['tiempo_ms'] = (time.perf_counter() - t0) * 1000.0
    r_new['x'] = [r_new['root']] if r_new['root'] is not None else []
    for h_row in r_new['hist']: h_row['residual'] = h_row.get('fx')
    out_raices['Newton-Raphson'] = r_new

    # Secante
    t0 = time.perf_counter()
    r_sec = secante(f, x0=0.0, x1=b_sup, xr=t_exacto, tol=tol)
    r_sec['tiempo_ms'] = (time.perf_counter() - t0) * 1000.0
    r_sec['x'] = [r_sec['root']] if r_sec['root'] is not None else []
    for h_row in r_sec['hist']: h_row['residual'] = h_row.get('fx')
    out_raices['Secante'] = r_sec

    return t_exacto, out_raices

def ejecutar(tipo, max_iter=5000):
    e = escenario(tipo)
    # 1. Calibración lineal
    out_lineal = {}
    for m, f in METODOS.items():
        t0 = time.perf_counter()
        res = f(e['A'], e['b'], e['xs'], tol=e['tol'], max_iter=max_iter)
        res['tiempo_ms'] = (time.perf_counter() - t0) * 1000.0
        out_lineal[m] = res
    
    # 2. Búsqueda de raíces para el tiempo al umbral
    t_exacto, out_raices = calcular_tiempo_umbral(e['D0'], e['alpha'], e['beta'], e['D_umbral'], tol=e['tol'])
    e['t_exacto'] = float(t_exacto)
    e['cond_A'] = float(cond(e['A']))
    if len(e['b']) <= 10:
        e['rho_j'] = float(radio_espectral_jacobi(e['A']))
        e['rho_gs'] = float(radio_espectral_gs(e['A']))
    else:
        e['rho_j'] = None
        e['rho_gs'] = None

    # Salida unificada: 4 métodos lineales + 3 métodos de raíces
    out = {**out_lineal, **out_raices}
    return e, out

if __name__ == '__main__':
    for t in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        e, out = ejecutar(t); A = e['A']
        rho_j = radio_espectral_jacobi(A) if len(e['b']) <= 10 else float('nan')
        rho_gs = radio_espectral_gs(A) if len(e['b']) <= 10 else float('nan')
        out_lin = {m: out[m] for m in METODOS}
        out_r = {m: out[m] for m in METODOS_RAICES}
        print(f"\n==================== ESCENARIO: {t} ====================")
        print(f"1. CALIBRACIÓN LINEAL | n={len(e['b'])} kappa={cond(A):.3e} rho(TJ)={rho_j:.4f} rho(TGS)={rho_gs:.4f}")
        print(f"{'Método':22}{'iter':>6}{'conv':>6}{'tiempo(ms)':>12}{'residuo':>12}{'err_abs':>12}{'err_rel':>12}")
        for m, r in out_lin.items():
            h = r['hist'][-1]
            print(f"{m:22}{r['iters']:>6}{str(r['converged']):>6}{r['tiempo_ms']:>12.2f}{h['residual']:>12.2e}{h['err_abs']:>12.2e}{h['err_rel']:>12.2e}")

        print(f"\n2. BÚSQUEDA DE RAÍCES: Tiempo al umbral D(t) = {e['D_umbral']} | Ref. Analítica: {e['t_exacto']:.4f} meses")
        print(f"{'Método':22}{'iter':>6}{'conv':>6}{'tiempo(ms)':>12}{'raíz (meses)':>14}{'f(t*)':>12}{'err_rel':>12}")
        for m, r in out_r.items():
            h = r['hist'][-1] if r['hist'] else dict(fx=float('nan'), err_rel=float('nan'))
            r_val = f"{r['root']:.6f}" if r['root'] is not None else "None"
            print(f"{m:22}{r['iters']:>6}{str(r['converged']):>6}{r['tiempo_ms']:>12.2f}{r_val:>14}{h['fx']:>12.2e}{h['err_rel']:>12.2e}")
