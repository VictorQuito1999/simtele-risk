# SIMTELE-RISK — Informe Final (Semana 3)

**Aplicación en Producción:** https://simtele-risk.vercel.app/  
**Base de Datos:** Turso (LibSQL) + SQLite local (`simtele.db`)  

> **Descargo Académico:** Simulación estrictamente educativa inspirada en Mi Teleférico (EN 12929-1 / EN 12927). Sin conexión a sistemas reales.

## 1. Resultados Verificados (4 Módulos × 3 Escenarios)

### Módulo 1 — Detención de Emergencia
| Escenario | Parámetros | Analítica (d / t) | RK4 | RK2 | Iter. Raíces |
|---|---|---|---|---|---|
| NORMAL | v0=5.0, a=1.0, tr=1.0, L=20.0 | 17.5000 m / 6.00 s | 17.50021 m (Er=1.19e-05) | 17.50063 m (Er=3.57e-05) | Bis:30 | New:1 | Sec:2 |
| ESTRES | v0=7.0, a=0.7, tr=2.0, L=25.0 | 49.0000 m / 12.00 s | 49.00015 m (Er=2.98e-06) | 49.00044 m (Er=8.93e-06) | Bis:30 | New:1 | Sec:2 |
| MAL_CONDICIONADO | v0=5.0, a=0.8, tr=1.0, L=25.0 | 25.8333 m / 13.50 s | 25.83333 m (Er=1.39e-09) | 25.83332 m (Er=5.10e-07) | Bis:13 | New:15 | Sec:20 |

### Módulo 2 — Deterioro y Mantenimiento
| Escenario | Método | κ(A) | Iters | Conv. | Residuo | Error Rel. |
|---|---|---|---|---|---|---|
| NORMAL | Jacobi | 2.36e+00 | 21 | Sí | 6.65e-08 | 4.97e-09 |
| NORMAL | Gauss-Seidel | 2.36e+00 | 12 | Sí | 3.02e-08 | 1.86e-09 |
| NORMAL | LU | 2.36e+00 | 1 | Sí | 1.78e-15 | 8.11e-17 |
| NORMAL | Gradiente conjugado | 2.36e+00 | 4 | Sí | 4.44e-16 | 2.03e-17 |
| NORMAL | Bisección | 2.36e+00 | 27 | Sí | 7.17e-09 | 1.01e-08 |
| NORMAL | Newton-Raphson | 2.36e+00 | 5 | Sí | 8.70e-14 | 1.23e-13 |
| NORMAL | Secante | 2.36e+00 | 8 | Sí | 6.62e-12 | 9.32e-12 |
| ESTRES | Jacobi | 2.99e+00 | 40 | Sí | 2.85e-11 | 1.06e-02 |
| ESTRES | Gauss-Seidel | 2.99e+00 | 26 | Sí | 1.31e-11 | 1.06e-02 |
| ESTRES | LU | 2.99e+00 | 1 | Sí | 4.72e-15 | 1.06e-02 |
| ESTRES | Gradiente conjugado | 2.99e+00 | 21 | Sí | 1.99e-11 | 1.06e-02 |
| ESTRES | Bisección | 2.99e+00 | 41 | Sí | 3.57e-13 | 5.99e-13 |
| ESTRES | Newton-Raphson | 2.99e+00 | 5 | Sí | 0.00e+00 | 1.47e-16 |
| ESTRES | Secante | 2.99e+00 | 9 | Sí | 3.89e-16 | 5.86e-16 |
| MAL_CONDICIONADO | Jacobi | 1.55e+04 | 72 | No | Inf | Inf |
| MAL_CONDICIONADO | Gauss-Seidel | 1.55e+04 | 5000 | No | 1.08e-06 | 3.45e-03 |
| MAL_CONDICIONADO | LU | 1.55e+04 | 1 | Sí | 2.22e-16 | 1.92e-03 |
| MAL_CONDICIONADO | Gradiente conjugado | 1.55e+04 | 4 | Sí | 1.48e-08 | 1.92e-03 |
| MAL_CONDICIONADO | Bisección | 1.55e+04 | 18 | Sí | 4.47e-09 | 2.58e-05 |
| MAL_CONDICIONADO | Newton-Raphson | 1.55e+04 | 4 | Sí | 3.55e-11 | 2.05e-07 |
| MAL_CONDICIONADO | Secante | 1.55e+04 | 10 | Sí | 2.71e-11 | 1.56e-07 |

### Módulo 3 — Oscilaciones por Viento
| Escenario | Parámetros | x_max | Error EDO | Trapecio ∫x²dt | Simpson 1/3 | Romberg |
|---|---|---|---|---|---|---|
| NORMAL | F0=0.0 N, ωf=0.0, c=600.0 | 0.5000 m | RK2=1.97e-03 | RK4=1.57e-07 | 0.59993 (Er=4.39e-06) | 0.59992 (Er=1.55e-07) | 0.59992 (8 pasos) |
| ESTRES | F0=1500.0 N, ωf=1.9, c=600.0 | 0.9630 m | RK2=3.43e-03 | RK4=2.71e-07 | 5.31436 (Er=4.21e-04) | 5.31213 (Er=1.07e-06) | 5.31212 (8 pasos) |
| MAL_CONDICIONADO | F0=1000.0 N, ωf=2.0, c=6.0 | 2.0046 m | RK2=3.95e-02 | RK4=1.92e-05 | 17.99889 (Er=8.92e-04) | 18.00788 (Er=3.93e-04) | 18.01496 (8 pasos) |

### Módulo 4 — Reconstrucción de Sensores
| Escenario | Configuración | Er Lagrange | Er Newton | Er Splines C² |
|---|---|---|---|---|
| NORMAL | 10 nodos, σ=0.0 | 1.05e-07 | 1.05e-07 | 3.99e-05 |
| ESTRES | 10 nodos, σ=0.08 | 9.47e-01 | 9.47e-01 | 4.41e-01 |
| MAL_CONDICIONADO | 14 nodos, σ=0.0 | 1.14e+01 | 1.14e+01 | 1.94e-03 |

## 2. Conclusiones Dobles por Módulo

### Módulo 1 — Detención de Emergencia
- **Conclusión Numérica:** RK4 (O(h⁴)) logra errores de 1.19×10⁻⁵ en NORMAL y 1.39×10⁻⁹ en no lineal frente a RK2 (Heun, O(h²)), siempre que el paso respete exactamente la discontinuidad en t = t_r. Trapecio y Simpson 1/3 reproducen la distancia integrada. En MAL_CONDICIONADO (a(v)=a√(v/v0)), la raíz doble v'(t*)=0 degrada Newton de 1 a 15 iteraciones.
- **Conclusión del Problema Físico:** En operación nominal (v0=5 m/s, a=1 m/s², t_r=1 s), la cabina frena en 17.50 m cumpliendo la vía libre de 20.0 m (+2.50 m de holgura). En ESTRÉS (v0=7 m/s, a=0.7 m/s², t_r=2 s), la distancia sube a 49.00 m, superando los 25.0 m de estación y evidenciando riesgo de colisión que obliga a reducir velocidad de aproximación.

### Módulo 2 — Deterioro Mecánico y Mantenimiento
- **Conclusión Numérica:** En tridiagonal SPD (κ=2.36), Gauss-Seidel converge en 12 iteraciones frente a 21 de Jacobi (ρ_GS ≈ ρ_J²). En ESTRÉS (δb=3%), todos convergen con error de 1.06% dictado por la perturbación de entrada. En Hilbert (κ=1.55×10⁴), Jacobi diverge (ρ=2.58>1) y Gauss-Seidel se estanca en 5000 pasos, mientras LU y CG resuelven con error acotado por κ. Newton (5 iters) supera ampliamente a Bisección (27–41 iters).
- **Conclusión del Problema Físico:** Bajo operación nominal, el cable alcanza el 60% de umbral de inspección (EN 12927) en 14.49 meses; bajo fatiga severa (ESTRÉS), la vida útil cae a 6.06 meses (-58%), obligando a duplicar ensayos electromagnéticos END. Una calibración mal condicionada de sensores distorsionaría la fecha real de mantenimiento.

### Módulo 3 — Oscilaciones por Viento Lateral
- **Conclusión Numérica:** En régimen libre, RK4 coincide con la solución analítica subamortiguada con error 1.57×10⁻⁷ frente a 1.97×10⁻³ de RK2. En régimen forzado/resonante, RK2 acumula desfase hasta 3.95% mientras RK4 mantiene 1.92×10⁻⁵. Romberg alcanza precisión de referencia en 8 pasos acelerando Trapecio y Simpson 1/3 sobre ∫ x² dt.
- **Conclusión del Problema Físico:** En vibración libre (0.50 m) el amortiguamiento contiene el balanceo dentro del gálibo seguro (0.80 m). En ESTRÉS (ωf=1.90 rad/s) llega a 0.963 m y en resonancia pura (ωf=ω0=2.0 rad/s, ζ≈0.0005) alcanza 2.005 m, exigiendo ralentización automática a 2 m/s o parada preventiva SCADA.

### Módulo 4 — Reconstrucción de Sensores
- **Conclusión Numérica:** Sobre sin(t) sin ruido, Lagrange, Newton y Splines Cúbicos logran errores < 4×10⁻⁵. Sin embargo, con 14 nodos equiespaciados sobre la función de Runge, Lagrange y Newton divergen en los extremos con error de 1140%, mientras los Splines Cúbicos Naturales C² mantienen 0.19% mediante un sistema tridiagonal estable O(n).
- **Conclusión del Problema Físico:** Reconstruir pérdidas de telemetría con polinomios globales provocaría falsas alarmas de sobretensión en el control del teleférico. Los Splines Cúbicos garantizan continuidad de posición, pendiente y curvatura física admisible; ante ruido elevado (σ=0.08) y gaps largos (>40%) se requiere además filtrado y redundancia de sensores.

## 3. Conclusión Global Integradora

La integración de los 4 módulos en 3 escenarios demuestra que la confiabilidad ingenieril depende tanto de la estabilidad, condicionamiento y orden de convergencia de los algoritmos numéricos como de su interpretación física en márgenes de seguridad (vía libre, vida útil END, gálibo por viento e integridad de telemetría), todo respaldado por persistencia verificable en Turso/SQLite.
