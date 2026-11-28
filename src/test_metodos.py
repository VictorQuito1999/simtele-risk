import numpy as np
from metodos import *

def test_normal():
    A = tridiag(4); xs = np.arange(1, 5.); b = A @ xs
    for f in METODOS.values():
        assert err_abs(f(A, b, xs, tol=1e-10)['x'], xs) < 1e-8

def test_manual():
    A = tridiag(4); xs = np.arange(1, 5.); b = A @ xs
    assert np.allclose(jacobi(A, b, xs, max_iter=1)['x'], [.5, 1, 1.5, 3.25])
    assert np.allclose(gauss_seidel(A, b, xs, max_iter=1)['x'], [.5, 1.125, 1.78125, 3.6953125])

def test_hilbert_cota():
    H = hilbert(4); x = np.arange(1, 5.); db = 1e-6*np.ones(4); b = H @ x
    assert np.linalg.norm(directa(H, b+db)-x)/np.linalg.norm(x) <= cond(H)*np.linalg.norm(db)/np.linalg.norm(b)

def test_radios_espectrales():
    A_tri = tridiag(4)
    H = hilbert(4)
    rho_j_tri = radio_espectral_jacobi(A_tri)
    rho_gs_tri = radio_espectral_gs(A_tri)
    rho_j_h = radio_espectral_jacobi(H)
    rho_gs_h = radio_espectral_gs(H)
    assert rho_j_tri < 1.0, "Jacobi debe converger en tridiagonal"
    assert rho_gs_tri < rho_j_tri, "Gauss-Seidel debe converger mas rapido que Jacobi"
    assert rho_j_h > 1.0, "Jacobi debe divergir en Hilbert (rho > 1)"
    assert rho_gs_h < 1.0, "Gauss-Seidel es teoricamente convergente en Hilbert pero rho muy cercano a 1"

def test_raices_deterioro():
    # Caso analítico cerrado: D(t) = 0.001*t^2 + 0.02*t + 0.10, Dumbral = 0.625 -> t* = 15.0 meses
    f = lambda t: 0.001*t**2 + 0.02*t + 0.10 - 0.625
    df = lambda t: 0.002*t + 0.02
    xr = 15.0

    rb = biseccion(f, 0.0, 25.0, xr=xr, tol=1e-8)
    rn = newton_raphson(f, df, x0=5.0, xr=xr, tol=1e-8)
    rs = secante(f, 0.0, 25.0, xr=xr, tol=1e-8)

    assert rb['converged'] and abs(rb['root'] - xr) < 1e-6, "Bisección falló"
    assert rn['converged'] and abs(rn['root'] - xr) < 1e-6, "Newton-Raphson falló"
    assert rs['converged'] and abs(rs['root'] - xr) < 1e-6, "Secante falló"
    assert rn['iters'] < rb['iters'], "Newton debe converger en menos iteraciones que Bisección"

def test_integracion_y_edo():
    # Integral exacta de x^2 en [0, 3] = 9.0
    f = lambda x: x**2
    assert abs(trapecio_compuesto(f, 0.0, 3.0, 100) - 9.0) < 1e-2
    assert abs(simpson_13_compuesto(f, 0.0, 3.0, 20) - 9.0) < 1e-12
    rb = romberg(f, 0.0, 3.0, tol=1e-10)
    assert rb['converged'] and abs(rb['integral'] - 9.0) < 1e-10

    # Módulo 1 y Módulo 3 contra referencia analítica
    import modulo1, modulo3
    _, an1, out1 = modulo1.ejecutar('NORMAL')
    assert abs(out1['RK4']['d_final'] - an1['d_total']) / an1['d_total'] < 1e-4
    assert out1['Raíces']['Bisección']['converged']
    assert out1['Raíces']['Newton']['converged']
    assert out1['Raíces']['Secante']['converged']

    _, x_ex3, out3 = modulo3.ejecutar('NORMAL')
    assert out3['RK4']['err_rel'] < 1e-5
    assert out3['RK4']['err_rel'] < out3['RK2 (Heun)']['err_rel']

def test_interpolacion_runge():
    import modulo4
    _, _, out4_norm = modulo4.ejecutar('NORMAL')
    assert out4_norm['Splines Cúbicos']['err_rel'] < 1e-3
    _, _, out4_runge = modulo4.ejecutar('MAL_CONDICIONADO')
    assert out4_runge['Lagrange']['err_rel'] > 1.0, "Lagrange debe explotar en Runge"
    assert out4_runge['Splines Cúbicos']['err_rel'] < 0.01, "Splines deben mantenerse estables en Runge"

if __name__ == '__main__':
    test_normal()
    test_manual()
    test_hilbert_cota()
    test_radios_espectrales()
    test_raices_deterioro()
    test_integracion_y_edo()
    test_interpolacion_runge()
    print("Todos los tests de metodos.py (lineales, raíces, integración, EDO, interpolación) pasaron exitosamente.")
