# SIMTELE-RISK — Sistema Integrado de Simulación Numérica y Análisis de Riesgos
### Métodos Numéricos · Ingeniería de Sistemas · Desarrollo de Software
**Inspirado en el Sistema de Transporte por Cable Urbano tipo Mi Teleférico (La Paz – El Alto, Bolivia)**

> **Descargo de responsabilidad académica:** Este proyecto es una simulación interdisciplinaria de carácter estrictamente educativo. Los modelos y parámetros utilizados están inspirados en especificaciones técnicas de referencia de teleféricos monocable desembragables (tipo Doppelmayr 10-MGD) y normativas internacionales de transporte por cable (EN 12929-1, EN 12927). No describen fallas verificadas de la empresa pública estatal ni existe conexión con sistemas reales de supervisión.

---

## 🚀 Características Principales del Sistema

1. **4 Módulos de Estudio Integrados Funcional y Visualmente:**
   - **Módulo 1: Detención de Emergencia de Cabinas:** Resolución del sistema de EDO de movimiento y frenado con desaceleración zapatas mediante **Heun (RK2)** y **Runge-Kutta de 4to Orden (RK4)**; integración compuesta por **Trapecio**; localización del instante de parada mediante **Newton-Raphson**; evaluación del margen de seguridad respecto a la vía libre disponible ($L - d_{\text{total}} \ge 0$).
   - **Módulo 2: Deterioro Mecánico y Mantenimiento:** Calibración de parámetros mediante sistemas de ecuaciones lineales $Ax=b$ con **Jacobi**, **Gauss-Seidel**, **Descomposición LU** ($PA=LU$) y **Gradiente Conjugado** sobre matrices simétricas definidas positivas; estimación del tiempo al umbral normativo ($D(t) - D_{\text{umbral}} = 0$) con **Bisección**, **Newton-Raphson** y **Secante**.
   - **Módulo 3: Oscilaciones Transversales por Viento:** Dinámica de balanceo pendular en vano abierto $m \ddot{x} + c \dot{x} + k x = F(t)$ bajo régimen subamortiguado libre (contrastado contra solución analítica exacta) y régimen forzado resonante con ráfagas laterales; integración de energía de oscilación $\int x^2 dt$ mediante **Trapecio**, **Simpson 1/3** y **Romberg** (extrapolación de Richardson).
   - **Módulo 4: Reconstrucción de Telemetría de Sensores:** Reconstrucción de registros faltantes en galgas extensométricas de tensión de cable y tacómetros de polea mediante **Interpolación de Lagrange**, **Polinomio de Newton por Diferencias Divididas** y **Splines Cúbicos Naturales ($C^2$)**; demostración empírica del **Fenómeno de Runge** y sensibilidad ante ruido gaussiano.

2. **Teoría de Errores Transversal y Validación Analítica:**
   - Error absoluto ($E_a$), error relativo protegido contra división por cero ($E_r = |x - x^*| / (|x^*| + \epsilon)$), error porcentual ($E_p$), norma residual $\|Ax - b\|$, número de condición espectral $\kappa(A)$, y demostración rigurosa de convergencia mediante radios espectrales ($\rho(T_J) < 1$ vs $\rho(T_J) > 1$).
   - Cada método se compara directamente contra una **solución analítica o de referencia verificable**.

3. **Arquitectura Web Interactiva (Flask + Chart.js + MathJax):**
   - Interfaz moderna, responsiva y dividida en 3 pestañas por caso:
     1. *Modelo Físico & Teoría*: Ecuaciones en LaTeX KaTeX/MathJax, deducción matemática y tabla de parámetros con fuentes de ingeniería.
     2. *Simulador Interactivo*: Botones de 1-clic para escenarios normalizados (**NORMAL**, **ESTRÉS**, **MAL CONDICIONADO**) y formulario para ingresar parámetros físicos personalizados.
     3. *Enfoque Ingeniería de Sistemas*: Especificación de Requisitos Funcionales (RF01-RF08), Matriz FMEA de Riesgos Operativos y diagramas de flujo.
   - **Doble Gráfico por Simulación:** Gráfico 1 (Fenómeno físico continuo con cotas admisibles) y Gráfico 2 (Convergencia y evolución del error relativo en escala logarítmica).
   - **Doble Conclusión Obligatoria:** Separación taxativa entre la **Conclusión Numérica** (estabilidad, tasa de convergencia $p$, residuo, orden del error $O(h^p)$) y la **Conclusión del Problema Físico** (seguridad operativa, margen en estación, vida útil remanente RUL, protocolo SCADA).
   - **Acordeón Desplegable:** Historial detallado paso a paso de las iteraciones de cada algoritmo.

4. **Persistencia Relacional en SQLite:**
   - Base de datos en archivo local (`simtele.db`) bajo modelo relacional normalizado de 6 tablas: `caso_estudio`, `escenario`, `simulacion`, `ejecucion_metodo`, `iteracion_resultado`, `resultado_resumen`.
   - Soporte de historial completo, inspección y relanzamiento idéntico de ejecuciones anteriores.

---

## 📂 Estructura del Repositorio

```text
simtele-risk/
├── Procfile                       # Despliegue en PaaS (Render, Railway, Heroku)
├── README.md                      # Documentación general y guía técnica
├── render.yaml                    # Configuración 1-clic de servicio web Render
├── requirements.txt               # Dependencias: flask, numpy, pytest, gunicorn
├── simtele.db                     # Base de datos relacional SQLite
├── docs/
│   ├── avance_semana1.docx        # Informe Word Semana 1 (sin carátula)
│   ├── avance_semana1.md          # Formato Markdown Semana 1
│   ├── avance_semana2.docx        # Informe Word Semana 2 (sin carátula)
│   ├── avance_semana2.md          # Formato Markdown Semana 2
│   └── DER.md                    # Diagrama Entidad-Relación y diccionario de datos
├── sql/
│   └── schema.sql                 # Script DDL de tablas y restricciones CHECK
└── src/
    ├── app.py                     # Servidor Flask, controladores y endpoints
    ├── build_docx.py              # Script automatizado de generación DOCX
    ├── metodos.py                 # Núcleo numérico (errores, sistemas, raíces, EDO, integración, splines)
    ├── modulo1.py                 # Lógica de dominio Caso 1 (Frenado y EDO)
    ├── modulo2.py                 # Lógica de dominio Caso 2 (Deterioro y Sistemas Lineales)
    ├── modulo3.py                 # Lógica de dominio Caso 3 (Oscilaciones por Viento)
    ├── modulo4.py                 # Lógica de dominio Caso 4 (Reconstrucción de Sensores)
    ├── test_metodos.py            # Suite de pruebas unitarias matemáticas
    ├── test_persistencia.py       # Prueba obligatoria de ciclo de persistencia (tol < 1e-14)
    └── templates/
        ├── base.html              # Layout base, navbar y estilos CSS
        ├── historial.html         # Bandeja de ejecuciones guardadas y relanzamiento
        ├── index.html             # Panel principal de los 4 casos de estudio
        ├── modulo.html            # Vista del caso (Teoría, Simulador, Requisitos)
        ├── simulacion.html        # Dashboard de resultados, gráficos duales y conclusiones
        └── teoria.html            # Compendio transversal de teoría de errores
```

---

## 🛠️ Instalación y Puesta en Marcha

### Prerrequisitos
- Python 3.10 o superior.
- Git.

### 1. Clonar el repositorio y preparar el entorno virtual
```bash
git clone <URL_DEL_REPOSITORIO>
cd simtele-risk
python3 -m venv venv
source venv/bin/activate    # En Linux / macOS
# venv\Scripts\activate     # En Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Iniciar el servidor web de desarrollo
```bash
python src/app.py
```
Abra su navegador web en: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 🧪 Ejecución de Pruebas de Calidad y Verificación

### Prueba 1: Verificación de Métodos Numéricos
Verifica la exactitud de los métodos iterativos (Jacobi, Gauss-Seidel), directos (LU, CG), radios espectrales y búsqueda de raíces contra referencias analíticas:
```bash
python src/test_metodos.py
```

### Prueba 2: Prueba Obligatoria de Persistencia (Rúbrica Sección 8)
Ejecuta el ciclo: **Calcular $\rightarrow$ Guardar en BD $\rightarrow$ Desconectar SQLite $\rightarrow$ Reconectar $\rightarrow$ Recuperar parámetros $\rightarrow$ Recalcular $\rightarrow$ Verificar coincidencia absoluta ($\le 10^{-14}$)**:
```bash
python src/test_persistencia.py
```

### Prueba 3: Suite Completa de Casos y Rutas
Verifica la ejecución de los 3 escenarios obligatorios (**NORMAL**, **ESTRÉS**, **MAL CONDICIONADO**) y los formularios de parámetros personalizados en los 4 módulos:
```bash
PYTHONPATH=src python -c "
from app import app
client = app.test_client()
for cid in [1, 2, 3, 4]:
    for tipo in ['NORMAL', 'ESTRES', 'MAL_CONDICIONADO']:
        r = client.get(f'/correr/{cid}/{tipo}', follow_redirects=True)
        assert r.status_code == 200
        print(f'Módulo {cid} - {tipo}: OK (200)')
print('Verificación de módulos exitosa.')
"
```

---

## ☁️ Despliegue en la Nube (Producción)

El proyecto incluye soporte nativo para despliegue en plataformas PaaS como **Render** o **Railway**:
- **Comando de Build:** `pip install -r requirements.txt`
- **Comando de Start:** `gunicorn --chdir src app:app`
- **Variables de Entorno:** `PORT=5000` (asignado automáticamente por el proveedor).

---

## 📊 Matriz de Casos de Estudio y Escenarios

| Caso de Estudio | Escenario NORMAL | Escenario ESTRÉS | Escenario MAL CONDICIONADO |
| :--- | :--- | :--- | :--- |
| **Módulo 1: Detención de Emergencia** | $v_0 = 5.0\text{ m/s}, a = 1.0\text{ m/s}^2, t_r = 1.0\text{ s}$. Cumple vía libre ($d = 17.5\text{ m} \le 20\text{ m}$). | $v_0 = 6.0\text{ m/s}, a = 0.65\text{ m/s}^2, t_r = 1.5\text{ s}$. Frenado degradado con riesgo de choque ($d = 36.7\text{ m} > 25\text{ m}$). | Desaceleración variable no lineal $a(v) = 0.2 + 0.15 v^2$. Contraste de paso $h$ y divergencia en aproximaciones de orden bajo. |
| **Módulo 2: Deterioro y Mantenimiento** | Matriz tridiagonal SPD $4\times 4$ ($\kappa = 2.36$). Convergencia lineal de Jacobi ($\rho = 0.4045$) y superlineal de raíces ($t^* = 14.49\text{ meses}$). | Perturbación del 3% en vector de carga ($\delta b$). Análisis de sensibilidad y reducción drástica de vida útil ($t^* = 6.06\text{ meses}$). | Matriz de Hilbert $4\times 4$ ($\kappa \approx 1.55 \times 10^4$). Jacobi diverge ($\rho = 2.5821 > 1$), Gauss-Seidel se estanca ($\rho \approx 0.999$). |
| **Módulo 3: Oscilaciones por Viento** | Vibración libre subamortiguada ($F_0 = 0$). Contraste contra solución analítica exponencial decreciente ($E_r < 10^{-4}$). | Ráfaga oscilatoria periódica $F_0 = 1500\text{ N}$ cercana a resonancia ($\omega_f = 1.90\text{ rad/s}$). Amplitud crece a $0.72\text{ m}$. | Resonancia pura ($\omega_f = \omega_0 = 2.0\text{ rad/s}$) y amortiguamiento crítico casi nulo ($\zeta \approx 0.0005$). Amplitud excede el gálibo lateral de 0.80 m. |
| **Módulo 4: Reconstrucción de Sensores** | Señal armónica $y(t) = \sin(t)$, 10 nodos equiespaciados sin ruido. Error en Splines y Newton $< 10^{-3}$. | Gap central del 40% de telemetría perdida y ruido gaussiano $\sigma = 0.08$. Reconstrucción interpolada con Splines $C^2$. | **Fenómeno de Runge:** $f(t) = \frac{1}{1 + 25t^2}$ con 14 nodos. Lagrange y Newton explotan en bordes ($E_r = 1140\%$), Splines mantienen $E_r = 0.19\%$. |

---

## 👥 Equipo y Autores
- **Proyecto:** SIMTELE-RISK (Desafío Integrador)
- **Materia:** Métodos Numéricos / Ingeniería de Sistemas / Desarrollo de Software
- **Año:** 2026
