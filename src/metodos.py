"""SIMTELE-RISK · Semana 1: teoría de errores + sistemas lineales (Ax=b)."""
import numpy as np

# ---------- Teoría de errores (transversal) ----------
def err_abs(x, xr): return float(np.linalg.norm(np.asarray(x) - np.asarray(xr)))
def err_rel(x, xr):
    n = np.linalg.norm(xr)
    return err_abs(x, xr) / n if n > 1e-300 else float('nan')   # sin dividir por cero
def err_pct(x, xr): return 100 * err_rel(x, xr)
def residual(A, x, b): return float(np.linalg.norm(b - A @ x))
def cond(A): return float(np.linalg.cond(A))

def _fila(k, x, A, b, xr):
    return dict(k=k, x=x.tolist(), residual=residual(A, x, b),
                err_abs=err_abs(x, xr), err_rel=err_rel(x, xr))

def directa(A, b):
    return np.linalg.solve(A, b)

# ---------- Métodos ----------
def jacobi(A, b, xr, tol=1e-8, max_iter=5000):
    x = np.zeros_like(b, dtype=float); D = np.diag(A); R = A - np.diagflat(D)
    h = [_fila(0, x, A, b, xr)]; k = 0
    for k in range(1, max_iter + 1):
        x = (b - R @ x) / D
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e30:
            h.append(dict(k=k, x=x.tolist(), residual=float('inf'), err_abs=float('inf'), err_rel=float('inf')))
            return dict(x=x, iters=k, converged=False, hist=h)
        h.append(_fila(k, x, A, b, xr))
        if not np.isfinite(h[-1]['residual']): break
        if h[-1]['residual'] < tol * np.linalg.norm(b): return dict(x=x, iters=k, converged=True, hist=h)
    return dict(x=x, iters=k, converged=False, hist=h)

def gauss_seidel(A, b, xr, tol=1e-8, max_iter=5000):
    n = len(b); x = np.zeros(n); h = [_fila(0, x, A, b, xr)]; k = 0
    for k in range(1, max_iter + 1):
        for i in range(n):
            x[i] = (b[i] - A[i, :i] @ x[:i] - A[i, i+1:] @ x[i+1:]) / A[i, i]
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e30:
            h.append(dict(k=k, x=x.tolist(), residual=float('inf'), err_abs=float('inf'), err_rel=float('inf')))
            return dict(x=x, iters=k, converged=False, hist=h)
        h.append(_fila(k, x.copy(), A, b, xr))
        if not np.isfinite(h[-1]['residual']): break
        if h[-1]['residual'] < tol * np.linalg.norm(b): return dict(x=x, iters=k, converged=True, hist=h)
    return dict(x=x, iters=k, converged=False, hist=h)

def lu(A, b, xr, **_):
    """LU con pivoteo parcial (PA = LU), sustitución adelante y atrás."""
    n = len(b); U = A.astype(float).copy(); L = np.eye(n); p = np.arange(n)
    for j in range(n - 1):
        m = j + np.argmax(abs(U[j:, j]))
        if m != j:
            U[[j, m]] = U[[m, j]]; p[[j, m]] = p[[m, j]]; L[[j, m], :j] = L[[m, j], :j]
        for i in range(j + 1, n):
            L[i, j] = U[i, j] / U[j, j]; U[i, j:] -= L[i, j] * U[j, j:]
    y = np.zeros(n); pb = b[p]
    for i in range(n): y[i] = pb[i] - L[i, :i] @ y[:i]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1): x[i] = (y[i] - U[i, i+1:] @ x[i+1:]) / U[i, i]
    return dict(x=x, iters=1, converged=True, hist=[_fila(1, x, A, b, xr)])

def cg(A, b, xr, tol=1e-8, max_iter=5000):
    """Gradiente conjugado estándar: requiere A simétrica definida positiva."""
    x = np.zeros(len(b)); r = b - A @ x; d = r.copy(); rs = r @ r
    h = [_fila(0, x, A, b, xr)]
    for k in range(1, max_iter + 1):
        Ad = A @ d; a = rs / (d @ Ad); x = x + a * d; r = r - a * Ad
        h.append(_fila(k, x.copy(), A, b, xr))
        rn = r @ r
        if np.sqrt(rn) < tol * np.linalg.norm(b): return dict(x=x, iters=k, converged=True, hist=h)
        d = r + (rn / rs) * d; rs = rn
    return dict(x=x, iters=max_iter, converged=False, hist=h)

# ---------- Métodos de Sistemas Lineales ----------
METODOS = {'Jacobi': jacobi, 'Gauss-Seidel': gauss_seidel, 'LU': lu, 'Gradiente conjugado': cg}

# ---------- Métodos de Búsqueda de Raíces (Semana 2) ----------
def biseccion(f, a, b, xr=None, tol=1e-8, max_iter=100):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        return dict(root=None, iters=0, converged=False, error="Intervalo no encierra raíz [f(a)*f(b) > 0]", hist=[], x=[])
    h = []; c_old = a
    for k in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = f(c)
        ea = abs(c - xr) if xr is not None else abs(c - c_old)
        er = (ea / abs(xr) if abs(xr) > 1e-300 else float('nan')) if xr is not None else (ea / abs(c) if abs(c) > 1e-300 else float('nan'))
        h.append(dict(k=k, x=[float(c)], residual=abs(float(fc)), fx=float(fc), err_abs=float(ea), err_rel=float(er)))
        if abs(fc) < tol or (b - a) / 2.0 < tol:
            return dict(root=float(c), iters=k, converged=True, hist=h, x=[float(c)])
        if fa * fc < 0:
            b = c; fb = fc
        else:
            a = c; fa = fc
        c_old = c
    return dict(root=float(c), iters=max_iter, converged=False, hist=h, x=[float(c)])

def newton_raphson(f, df, x0, xr=None, tol=1e-8, max_iter=100):
    x = float(x0); h = []
    # Registrar aproximación inicial k=0
    fx0 = f(x)
    ea0 = abs(x - xr) if xr is not None else float('nan')
    er0 = (ea0 / abs(xr)) if (xr is not None and abs(xr) > 1e-300) else float('nan')
    h.append(dict(k=0, x=[float(x)], residual=abs(float(fx0)), fx=float(fx0), err_abs=float(ea0), err_rel=float(er0)))
    
    for k in range(1, max_iter + 1):
        fx = f(x); dfx = df(x)
        if abs(dfx) < 1e-15:
            ea = abs(x - xr) if xr is not None else float('nan')
            er = (ea / abs(xr) if xr is not None and abs(xr) > 1e-300 else float('nan'))
            return dict(root=float(x), iters=k, converged=False, error="Derivada nula o cuasi-nula", hist=h, x=[float(x)])
        x_next = x - fx / dfx
        ea = abs(x_next - xr) if xr is not None else abs(x_next - x)
        er = (ea / abs(xr) if abs(xr) > 1e-300 else float('nan')) if xr is not None else (ea / abs(x_next) if abs(x_next) > 1e-300 else float('nan'))
        fx_next = f(x_next)
        h.append(dict(k=k, x=[float(x_next)], residual=abs(float(fx_next)), fx=float(fx_next), err_abs=float(ea), err_rel=float(er)))
        if abs(fx_next) < tol or abs(x_next - x) < tol:
            return dict(root=float(x_next), iters=k, converged=True, hist=h, x=[float(x_next)])
        x = x_next
    return dict(root=float(x), iters=max_iter, converged=False, hist=h, x=[float(x)])

def secante(f, x0, x1, xr=None, tol=1e-8, max_iter=100):
    x_prev, x_curr = float(x0), float(x1)
    f_prev, f_curr = f(x_prev), f(x_curr)
    h = []
    # Registrar puntos iniciales k=0 y k=1
    ea0 = abs(x_prev - xr) if xr is not None else float('nan')
    er0 = (ea0 / abs(xr)) if (xr is not None and abs(xr) > 1e-300) else float('nan')
    h.append(dict(k=0, x=[float(x_prev)], residual=abs(float(f_prev)), fx=float(f_prev), err_abs=float(ea0), err_rel=float(er0)))
    
    ea1 = abs(x_curr - xr) if xr is not None else abs(x_curr - x_prev)
    er1 = (ea1 / abs(xr)) if (xr is not None and abs(xr) > 1e-300) else float('nan')
    h.append(dict(k=1, x=[float(x_curr)], residual=abs(float(f_curr)), fx=float(f_curr), err_abs=float(ea1), err_rel=float(er1)))
    
    for k in range(2, max_iter + 2):
        denom = f_curr - f_prev
        if abs(denom) < 1e-15:
            return dict(root=float(x_curr), iters=k-1, converged=False, error="División por cero en secante", hist=h, x=[float(x_curr)])
        x_next = x_curr - f_curr * (x_curr - x_prev) / denom
        ea = abs(x_next - xr) if xr is not None else abs(x_next - x_curr)
        er = (ea / abs(xr) if abs(xr) > 1e-300 else float('nan')) if xr is not None else (ea / abs(x_next) if abs(x_next) > 1e-300 else float('nan'))
        fx_next = f(x_next)
        h.append(dict(k=k, x=[float(x_next)], residual=abs(float(fx_next)), fx=float(fx_next), err_abs=float(ea), err_rel=float(er)))
        if abs(fx_next) < tol or abs(x_next - x_curr) < tol:
            return dict(root=float(x_next), iters=k, converged=True, hist=h, x=[float(x_next)])
        x_prev, x_curr = x_curr, x_next
        f_prev, f_curr = f_curr, fx_next
    return dict(root=float(x_curr), iters=max_iter, converged=False, hist=h, x=[float(x_curr)])

METODOS_RAICES = {'Bisección': biseccion, 'Newton-Raphson': newton_raphson, 'Secante': secante}

# ---------- Métodos de Integración Numérica (Semana 2) ----------
def trapecio_compuesto(f, a, b, n):
    """Regla del trapecio compuesto sobre n subintervalos."""
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x], dtype=float)
    return float((h / 2.0) * (y[0] + 2.0 * np.sum(y[1:-1]) + y[-1]))

def simpson_13_compuesto(f, a, b, n):
    """Regla de Simpson 1/3 compuesto sobre n subintervalos (n debe ser par)."""
    if n % 2 != 0: n += 1
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x], dtype=float)
    return float((h / 3.0) * (y[0] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-1:2]) + y[-1]))

def romberg(f, a, b, tol=1e-8, max_k=8):
    """Integración de Romberg mediante extrapolación de Richardson."""
    R = np.zeros((max_k, max_k))
    R[0, 0] = trapecio_compuesto(f, a, b, 1)
    for k in range(1, max_k):
        R[k, 0] = trapecio_compuesto(f, a, b, 2**k)
        for j in range(1, k + 1):
            R[k, j] = R[k, j-1] + (R[k, j-1] - R[k-1, j-1]) / (4.0**j - 1.0)
        if abs(R[k, k] - R[k-1, k-1]) < tol:
            return dict(integral=float(R[k, k]), table=R[:k+1, :k+1], steps=k+1, converged=True)
    return dict(integral=float(R[max_k-1, max_k-1]), table=R, steps=max_k, converged=False)

METODOS_INTEGRACION = {'Trapecio': trapecio_compuesto, 'Simpson 1/3': simpson_13_compuesto, 'Romberg': romberg}

# ---------- Métodos de Interpolación (Semana 2) ----------
def lagrange_eval(x_nodes, y_nodes, x_eval):
    """Evalúa el polinomio interpolador de Lagrange en los puntos x_eval."""
    x_nodes = np.asarray(x_nodes, dtype=float)
    y_nodes = np.asarray(y_nodes, dtype=float)
    res = []
    for x in np.atleast_1d(x_eval):
        term = 0.0
        for i in range(len(x_nodes)):
            L_i = 1.0
            for j in range(len(x_nodes)):
                if i != j:
                    L_i *= (x - x_nodes[j]) / (x_nodes[i] - x_nodes[j])
            term += y_nodes[i] * L_i
        res.append(term)
    return np.array(res, dtype=float)

def newton_dif_div(x_nodes, y_nodes):
    """Calcula la tabla de diferencias divididas de Newton."""
    x_nodes = np.asarray(x_nodes, dtype=float)
    y_nodes = np.asarray(y_nodes, dtype=float)
    n = len(x_nodes)
    F = np.zeros((n, n))
    F[:, 0] = y_nodes
    for j in range(1, n):
        for i in range(n - j):
            F[i, j] = (F[i+1, j-1] - F[i, j-1]) / (x_nodes[i+j] - x_nodes[i])
    return F[0, :]

def newton_eval(x_nodes, coefs, x_eval):
    """Evalúa el polinomio en forma de Newton dados los coeficientes y nodos."""
    x_nodes = np.asarray(x_nodes, dtype=float)
    res = []
    for x in np.atleast_1d(x_eval):
        val = coefs[0]
        prod = 1.0
        for i in range(1, len(coefs)):
            prod *= (x - x_nodes[i-1])
            val += coefs[i] * prod
        res.append(val)
    return np.array(res, dtype=float)

def splines_cubicos_naturales(x_nodes, y_nodes):
    """Calcula los trazadores cúbicos naturales (S''(x0)=0, S''(xn)=0)."""
    x = np.asarray(x_nodes, dtype=float)
    y = np.asarray(y_nodes, dtype=float)
    n = len(x) - 1
    h = np.diff(x)
    A = np.zeros((n+1, n+1))
    rhs = np.zeros(n+1)
    A[0, 0] = 1.0; A[n, n] = 1.0
    for i in range(1, n):
        A[i, i-1] = h[i-1]
        A[i, i] = 2.0 * (h[i-1] + h[i])
        A[i, i+1] = h[i]
        rhs[i] = 3.0 * ((y[i+1] - y[i])/h[i] - (y[i] - y[i-1])/h[i-1])
    c = np.linalg.solve(A, rhs)
    b = np.zeros(n)
    d = np.zeros(n)
    a = y[:-1].copy()
    for i in range(n):
        b[i] = (y[i+1] - y[i])/h[i] - (h[i]/3.0) * (2.0*c[i] + c[i+1])
        d[i] = (c[i+1] - c[i]) / (3.0 * h[i])
    return dict(x=x, a=a, b=b, c=c[:-1], d=d)

def splines_eval(spl, x_eval):
    """Evalúa el spline cúbico natural en los puntos x_eval."""
    x = spl['x']; a = spl['a']; b = spl['b']; c = spl['c']; d = spl['d']
    res = []
    for val in np.atleast_1d(x_eval):
        if val <= x[0]: idx = 0
        elif val >= x[-1]: idx = len(a) - 1
        else: idx = np.searchsorted(x, val) - 1
        dx = val - x[idx]
        res.append(a[idx] + b[idx]*dx + c[idx]*(dx**2) + d[idx]*(dx**3))
    return np.array(res, dtype=float)

METODOS_INTERPOLACION = {
    'Lagrange': lagrange_eval,
    'Newton': (newton_dif_div, newton_eval),
    'Splines Cúbicos': (splines_cubicos_naturales, splines_eval)
}

# ---------- Matrices de prueba y propiedades ----------
def tridiag(n):  # SPD y diagonal dominante
    return 4*np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
def hilbert(n):  # SPD pero muy mal condicionada
    return np.array([[1/(i+j+1) for j in range(n)] for i in range(n)])
def es_spd(A): return bool(np.allclose(A, A.T) and np.all(np.linalg.eigvalsh(A) > 0))
def diag_dominante(A):
    return bool(np.all(2*abs(np.diag(A)) > abs(A).sum(axis=1)))
def radio_espectral_jacobi(A):
    """Radio espectral rho(T_J) de la matriz de iteracion de Jacobi T_J = D^(-1)(L+U)."""
    D = np.diag(A); R = A - np.diagflat(D)
    TJ = R / D[:, None]
    return float(np.max(np.abs(np.linalg.eigvals(TJ))))
def radio_espectral_gs(A):
    """Radio espectral rho(T_GS) de la matriz de iteracion de Gauss-Seidel T_GS = (D-L)^(-1) U."""
    D = np.diag(np.diag(A)); L = -np.tril(A, -1); U = -np.triu(A, 1)
    T_gs = np.linalg.inv(D - L) @ U
    return float(np.max(np.abs(np.linalg.eigvals(T_gs))))
