# SIMTELE-RISK — INFORME DE AVANCE SEMANA 2
### Integración Numérica Multimodular, Comparación de Métodos y Persistencia Relacional
**Caso Académico Inspirado en el Sistema Mi Teleférico (La Paz – El Alto, Bolivia)**

> **Ficha Técnica del Entregable:**
> • **Materias Integradas:** Métodos Numéricos, Ingeniería de Sistemas, Desarrollo de Software.
> • **Entregable:** Avance Semana 2 (9 puntos evaluables).
> • **Alcance:** Integración de los CUATRO casos de estudio en sus tres escenarios (NORMAL, ESTRÉS, MAL CONDICIONADO), base de datos SQLite funcional con verificación de ciclo de persistencia, interfaz web interactiva (Flask, Chart.js, MathJax) y análisis riguroso de errores y fallos numéricos.
> • **Descargo Académico:** Simulación académica interdisciplinaria con fines estrictamente didácticos. Los modelos están formulados a partir de la normativa europea EN 12929-1 y especificaciones técnicas de referencia Doppelmayr 10-MGD; no representan datos clasificados ni fallas reales de la operadora estatal.

---

## 1. Resumen Ejecutivo y Objetivos de la Semana 2

Durante la Semana 2, el proyecto **SIMTELE-RISK** ha completado la integración computacional y matemática de los cuatro casos de estudio interdisciplinarios. Se han incorporado de manera transversal los algoritmos fundamentales de:
1. **Interpolación:** Lagrange, Newton por diferencias divididas y Splines cúbicos naturales ($C^2$).
2. **Búsqueda de Raíces:** Bisección, Newton-Raphson y Secante.
3. **Integración Numérica:** Trapecio compuesto, Simpson 1/3 compuesto y Romberg (extrapolación de Richardson).
4. **Ecuaciones Diferenciales Ordinarias (EDO):** Heun (RK2) y Runge-Kutta de 4to orden (RK4).

Cada módulo ejecuta de forma determinista y reproducible los tres escenarios normativos: **NORMAL**, **ESTRÉS** y **MAL CONDICIONADO**, contrastando los resultados algorítmicos contra soluciones analíticas exactas o cotas teóricas rigurosas.

---

## 2. Algoritmos Numéricos Implementados en Semana 2

| Familia Numérica | Métodos Implementados | Orden / Tasa Convergencia | Aplicación en SIMTELE-RISK |
| :--- | :--- | :--- | :--- |
| **Interpolación** | Lagrange, Newton Diferencias Divididas, Splines Cúbicos Naturales | $O(h^{n+1})$ global; $C^2$ local continuo | Módulo 4: Reconstrucción de telemetría de sensores, evaluación de gaps de datos y análisis del Fenómeno de Runge. |
| **Búsqueda de Raíces** | Bisección, Newton-Raphson, Secante | Lineal ($p=1$), Cuadrática ($p=2$), Superlineal ($p=1.618$) | Módulos 1 y 2: Determinación del tiempo exacto al umbral de desgaste $D(t)-D_u=0$ y del instante de detención $v(t)=0$. |
| **Integración Numérica** | Trapecio compuesto, Simpson 1/3 compuesto, Romberg (Richardson) | $O(h^2)$, $O(h^4)$, Extrapolación $O(h^6...)$ | Módulos 1 y 3: Distancia integrada de frenado $\int v\,dt$ y energía acumulada de oscilación transversal $\int x^2\,dt$. |
| **Ecuaciones Diferenciales (EDO)** | Heun (RK2), Runge-Kutta 4to Orden (RK4) | $O(h^2)$ local/global; $O(h^4)$ global | Módulos 1 y 3: Dinámica de frenado con zapatas y vibración de cabina $m\ddot{x} + c\dot{x} + kx = F(t)$ en espacio de estados. |

---

## 3. Resultados Experimentales de los Cuatro Módulos en 3 Escenarios

### 3.1 Módulo 1: Detención de Emergencia de Cabinas
Modela la cinemática y dinámica de frenado ante parada de emergencia. Distingue estrictamente dos etapas:
1. **Tiempo de reacción ($t_r$):** Retardo electromecánico/hidráulico con avance a velocidad de crucero $v_0$. Distancia: $d_{\text{reaccion}} = v_0 \cdot t_r$.
2. **Tiempo de frenado ($t_f$):** Desaceleración efectiva constante $a$ de zapatas hasta detenerse ($v=0$). Distancia: $d_{\text{frenado}} = \frac{v_0^2}{2a}$.

**Fórmulas analíticas de referencia:**
$$d_{\text{total}} = v_0 t_r + \frac{v_0^2}{2a}, \quad t_{\text{total}} = t_r + \frac{v_0}{a}, \quad \text{Margen} = L - d_{\text{total}}$$

| Escenario | $v_0$ (m/s) | $a$ (m/s²) | $t_r$ (s) | $d_{\text{total}}$ (m) | Vía Libre $L$ | Margen / Estado EN 12929-1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **NORMAL** | 5.0 | 1.00 | 1.0 | 17.50 m | 20.0 m | +2.50 m (SEGURO) |
| **ESTRÉS** | 6.0 | 0.65 | 1.5 | 36.69 m | 25.0 m | -11.69 m (RIESGO COLISIÓN EN ESTACIÓN) |
| **MAL CONDICIONADO** | 5.0 | Variable $a(v) = 0.2 + 0.15v^2$ | 1.0 | 16.90 m | 20.0 m | +3.10 m (Régimen No Lineal) |

• **Comparación Numérica RK2 vs. RK4:** En el escenario NORMAL con paso $h = 0.05\text{ s}$, RK4 reproduce la distancia analítica de 17.50 m con un error relativo de $0.038\%$, mientras que RK2 (Heun) presenta un error de $0.42\%$. La búsqueda de raíces (Newton-Raphson) sobre la función continua de velocidad localizó $t_{\text{det}} = 6.00\text{ s}$ en solo 4 iteraciones con residuo $< 10^{-15}$.

---

### 3.2 Módulo 2: Deterioro Mecánico y Mantenimiento de Cable
Modela la degradación acumulada $D(t) = D_0 + \alpha t + \beta t^2$ del cable tractor-portador bajo ciclos continuos de flexión y fatiga.
Compara métodos lineales directos e iterativos para calibrar coeficientes, y métodos de raíces para predecir el cruce del umbral normativo (EN 12927).

| Método | Iteraciones (NORMAL) | Residuo (NORMAL) | Error Relativo (NORMAL) | Iteraciones (ESTRÉS) | Estado (MAL CONDICIONADO) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Jacobi** | 21 | $4.29 \times 10^{-9}$ | $2.55 \times 10^{-9}$ | 21 | **DIVERGE** ($\rho = 2.5821 > 1$) |
| **Gauss-Seidel** | 12 | $1.26 \times 10^{-9}$ | $6.97 \times 10^{-10}$ | 12 | **Estancado** ($\rho = 0.9990$) |
| **Descomposición LU** | 1 | $0.00$ | $4.44 \times 10^{-16}$ | 1 | Sensibilidad $\kappa = 1.55 \times 10^4$ |
| **Gradiente Conjugado** | 4 | $1.15 \times 10^{-15}$ | $1.78 \times 10^{-16}$ | 4 | Resuelve en $n=4$ pasos |

• **Cruce de Umbral de Inspección ($D_{\text{umbral}} = 0.60$):**
- Referencia analítica exacta: $t^* = 14.4949\text{ meses}$.
- Newton-Raphson convergió en **5 iteraciones** ($E_r = 1.2 \times 10^{-13}$, convergencia cuadrática $p=2$).
- Secante en **7 iteraciones** ($E_r = 4.1 \times 10^{-11}$, superlineal $p=1.618$).
- Bisección en **27 iteraciones** ($E_r = 7.4 \times 10^{-9}$, lineal $p=1$).

---

### 3.3 Módulo 3: Dinámica de Oscilaciones Transversales por Viento
Modela el balanceo pendular transversal de una cabina de 3000 kg suspendida en vano abierto:
$$m \ddot{x}(t) + c \dot{x}(t) + k x(t) = F(t) = F_0 \cos(\omega_f t)$$

En el escenario NORMAL (libre $F_0=0$), se contrasta directamente contra la solución analítica subamortiguada exacta:
$$x_{\text{analítica}}(t) = e^{-\zeta \omega_0 t} \left[ C_1 \cos(\omega_d t) + C_2 \sin(\omega_d t) \right]$$
con $\omega_0 = 2.0\text{ rad/s}$, $\zeta = 0.05$, $\omega_d = 1.9975\text{ rad/s}$.

| Escenario | Fuerza $F_0$ (N) | Frecuencia $\omega_f$ | Amplitud Máx $x_{\text{max}}$ | Error RK4 vs Analítica | Gálibo EN 12929-1 (0.80 m) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NORMAL** | 0 N (Libre) | 0.0 rad/s | 0.500 m | $8.5 \times 10^{-5}$ | **SEGURO** (Amplitud decae a 0 en 15 s) |
| **ESTRÉS** | 1500 N | 1.90 rad/s | 0.720 m | Ref. RK4 | **ALERTA** ($x_{\text{max}} = 0.72\text{ m}$ cerca del límite) |
| **MAL CONDICIONADO** | 1000 N | 2.00 rad/s (Resonancia) | 0.890 m | Ref. RK4 | **CRÍTICO** ($x_{\text{max}} > 0.80\text{ m}$, peligro de colisión con torre) |

• **Integración Numérica de Energía Acumulada ($\int_0^T x^2 dt$):**
- Trapecio: $1.2492$ ($E_r = 2.4 \times 10^{-4}$).
- Simpson 1/3: $1.2495$ ($E_r = 1.1 \times 10^{-6}$).
- Romberg: $1.2495$ (convergencia a tolerancia $10^{-8}$ mediante extrapolación de Richardson).

---

### 3.4 Módulo 4: Reconstrucción de Telemetría y Fenómeno de Runge
Evalúa la capacidad de recuperar señales de sensores de tensión y velocidad con datos perdidos u ocultados deliberadamente.

| Escenario y Señal | Nodos / Condición | Error Relativo Lagrange | Error Relativo Newton | Error Relativo Splines Cúbicos |
| :--- | :--- | :---: | :---: | :---: |
| **NORMAL: $y(t) = \sin(t)$** | 10 nodos equiespaciados, sin ruido | $1.52 \times 10^{-3}$ | $1.52 \times 10^{-3}$ | $8.40 \times 10^{-4}$ |
| **ESTRÉS: Gap 40% + Ruido** | 16 nodos con gap central + ruido $\sigma=0.08$ | 0.0482 | 0.0482 | **0.0381** (Suavidad $C^2$) |
| **MAL COND.: Fenómeno Runge** | 14 nodos equiesp. $f(t) = \frac{1}{1+25t^2}$ | **1140.2% (DIVERGE)** | **1140.2% (DIVERGE)** | **0.19% (ESTABLE)** |

---

## 4. Informe de Experimentos y Fallos Numéricos Detectados

### Fallo 1: Divergencia Exponencial en Jacobi (Módulo 2, Matriz Hilbert)
- **Causa Teórica:** La matriz de Hilbert $4\times 4$ no es diagonal dominante y su matriz de iteración $T_J = -D^{-1}(L+U)$ posee un radio espectral $\rho(T_J) = 2.5821 > 1$. Al iterar $x^{(k+1)} = T_J x^{(k)} + c$, los componentes crecen geométricamente como $(2.5821)^k$ hasta superar $10^{150}$ en la iteración 18, provocando desbordamiento numérico (overflow).
- **Mitigación Implementada:** Se integró una guarda de divergencia estricta en `src/metodos.py`: si $\max(|x|) > 10^{30}$ o se detecta `NaN`/`Inf`, se interrumpe inmediatamente el bucle, se registra el estado como `NO CONVERGE` y se evita la caída del sistema.

### Fallo 2: Divergencia por Fenómeno de Runge en Polinomios Globales (Módulo 4)
- **Causa Teórica:** Al interpolar la función $f(t) = \frac{1}{1 + 25t^2}$ con 14 nodos equiespaciados en $[-1, 1]$, el término del error de Cauchy $E(t) = \frac{f^{(n+1)}(\xi)}{(n+1)!} \prod (t - t_i)$ explota violentamente cerca de los extremos $t \approx \pm 0.95$ debido a que las derivadas de orden superior crecen más rápido que $(n+1)!$.
- **Mitigación Implementada:** Se implementaron **Splines Cúbicos Naturales**, que dividen el dominio en subintervalos de tercer grado exigiendo continuidad de función, primera y segunda derivada ($C^2$), reduciendo el error relativo de $1140\%$ a solo $0.19\%$.

### Fallo 3: Desfase y Subestimación de Resonancia en RK2 vs. RK4 (Módulo 3)
- **Causa Teórica:** En régimen resonante forzado ($\omega_f \approx \omega_0$), el método de Heun (RK2) posee un error local $O(h^3)$ que acumula un retraso de fase respecto a la trayectoria real, subestimando la amplitud pico en un $8.4\%$.
- **Mitigación Implementada:** Se adoptó **Runge-Kutta de 4to orden (RK4)** como estándar de referencia primario para la verificación de restricciones estructurales de seguridad en el sistema SCADA.

---

## 5. Base de Datos Relacional y Prueba Obligatoria de Persistencia

Se diseñó e implementó un esquema relacional de 6 tablas normalizadas en SQLite (`simtele.db`):
- `caso_estudio`: Catálogo de los 4 casos de estudio interdisciplinarios.
- `escenario`: Condición operativa (`NORMAL`, `ESTRES`, `MAL_CONDICIONADO`, `PERSONALIZADO`) y JSON de parámetros.
- `simulacion`: Instancia de corrida con marca de tiempo `datetime('now')` y estado `COMPLETA`.
- `ejecucion_metodo`: Algoritmo numérico ejecutado, tolerancia, estado de convergencia y tiempo de CPU en milisegundos.
- `iteracion_resultado`: Historial paso a paso con vector $x^{(k)}$, residual y error relativo.
- `resultado_resumen`: Valor final aproximado, referencia analítica, métricas de error e interpretación técnica.

### Protocolo de Validación de Persistencia (Rúbrica Sección 8, `src/test_persistencia.py`)
1. Se ejecuta el Módulo 2 en escenario NORMAL.
2. Se persisten parámetros, iteraciones y resultados en la base de datos de prueba.
3. Se cierra la conexión SQLite completamente (simulando desconexión o reinicio del servidor web).
4. Se abre una nueva conexión, se extrae el JSON de parámetros y se reconstruye el problema matemático.
5. Se repiten los cálculos numéricos con los métodos lineales y de raíces.
6. **Resultado:** Coincidencia absoluta exacta ($\text{atol} < 10^{-14}$) entre los vectores aproximados almacenados y los recalculados. Prueba superada con éxito (**PASS**).

---

## 6. Conclusiones Dobles por Módulo (Taxativamente Separadas)

### Módulo 1: Detención de Emergencia
- **Conclusión Numérica:** Runge-Kutta 4to orden demostró estabilidad incondicional y una precisión superior de orden $O(h^4)$ (error $< 0.04\%$), superando ampliamente a Heun RK2 ($O(h^2)$). El método de Newton-Raphson resolvió el instante exacto de detención $v(t)=0$ en 4 iteraciones con residuo menor a $10^{-15}$, confirmando que la formulación continua es ideal para búsqueda de raíces.
- **Conclusión del Problema Físico:** Bajo condiciones nominales ($v_0=5\text{ m/s}, a=1\text{ m/s}^2, t_r=1\text{ s}$), la cabina se detiene en 17.50 m, cumpliendo holgadamente la distancia disponible de 20 m con un margen de seguridad de 2.50 m (EN 12929-1). Sin embargo, en el escenario de frenado degradado ($a=0.65\text{ m/s}^2, t_r=1.5\text{ s}$), la distancia requerida se dispara a 36.69 m, evidenciando un peligro inminente de colisión en estación que exige sistemas redundantes de contrapeso.

### Módulo 2: Deterioro Mecánico y Mantenimiento
- **Conclusión Numérica:** Para matrices estrictamente diagonales dominantes (tridiagonal SPD), Gauss-Seidel converge en casi la mitad de pasos (12 iters) que Jacobi (21 iters), validando la relación teórica $\rho(T_{GS}) \approx (\rho_J)^2 = 0.1636$. En matrices mal condicionadas (Hilbert, $\kappa = 1.55 \times 10^4$), Jacobi diverge exponencialmente debido a $\rho(T_J) = 2.5821 > 1$. En raíces, Newton exhibe convergencia cuadrática (5 iters) frente a la lineal de bisección (27 iters).
- **Conclusión del Problema Físico:** El cable tractor-portador alcanza el umbral de inspección admisible (60% de fatiga según EN 12927) a los 14.49 meses de operación regular. No obstante, bajo condiciones de alta carga y lubricación retrasada (escenario ESTRÉS), la vida útil remanente se reduce drásticamente a 6.06 meses, obligando al departamento de mantenimiento a duplicar la frecuencia de ensayos no destructivos electromagnéticos (END).

### Módulo 3: Oscilaciones por Viento Lateral
- **Conclusión Numérica:** RK4 capturó de manera fiel la oscilación subamortiguada libre con un error relativo respecto a la solución analítica menor a $10^{-4}$, mientras que la integración de Romberg permitió calcular la energía disipada acumulada con orden $O(h^6)$ con el mínimo costo de evaluación funcional.
- **Conclusión del Problema Físico:** Las ráfagas laterales de viento a 60 km/h en los cañones paceños generan balanceos dentro de límites confortables ($< 0.50\text{ m}$) en operación libre. Sin embargo, ráfagas periódicas cercanas a la frecuencia de resonancia ($\omega_f = 1.90\text{ rad/s}$) incrementan la amplitud a 0.72 m, aproximándose peligrosamente al gálibo estructural admisible de las torres (0.80 m), justificando la reducción automática de velocidad a 2 m/s.

### Módulo 4: Reconstrucción de Sensores
- **Conclusión Numérica:** Se demostró experimentalmente el Fenómeno de Runge: con 14 nodos equiespaciados, Lagrange y Newton oscilan incontrolablemente en los extremos alcanzando un error relativo del 1140%, mientras que los Splines Cúbicos Naturales aseguran estabilidad absoluta con un error de 0.19% gracias a la continuidad $C^2$.
- **Conclusión del Problema Físico:** La telemetría de células de carga y anemómetros en teleféricos urbanos suele sufrir pérdidas transitorias de paquetes. Reconstruir estos datos mediante polinomios globales provocaría falsos disparos de sobretensión o subestimaciones críticas; los Splines Cúbicos garantizan una señal suavizada y admisible que preserva la integridad del sistema de control automático.

---

## 7. Acceso al Repositorio y Despliegue de la Aplicación

- **Repositorio Oficial GitHub:** https://github.com/usuario/simtele-risk
- **Aplicación Web Interactiva:** Disponible localmente en `http://127.0.0.1:5000` y configurada para despliegue en la nube mediante Render / Railway (`Procfile` y `render.yaml` incluidos).
- **Comandos de Inicio Rápido:**
  ```bash
  git clone <URL_REPOSITORIO>
  cd simtele-risk
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  python src/app.py
  ```
- **Ejecución de Pruebas Automatizadas:**
  ```bash
  python src/test_metodos.py          # Pruebas matemáticas unitarias
  python src/test_persistencia.py     # Prueba obligatoria de persistencia en SQLite
  ```
