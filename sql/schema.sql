PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS caso_estudio (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, modelo_version TEXT NOT NULL DEFAULT 'v1');
CREATE TABLE IF NOT EXISTS escenario (
  id INTEGER PRIMARY KEY, caso_id INTEGER NOT NULL REFERENCES caso_estudio(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('NORMAL','ESTRES','MAL_CONDICIONADO','PERSONALIZADO')),
  parametros_json TEXT NOT NULL, fuente_datos TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulacion (
  id INTEGER PRIMARY KEY, escenario_id INTEGER NOT NULL REFERENCES escenario(id),
  fecha TEXT NOT NULL DEFAULT (datetime('now')), equipo TEXT, estado TEXT NOT NULL DEFAULT 'COMPLETA');
CREATE TABLE IF NOT EXISTS ejecucion_metodo (
  id INTEGER PRIMARY KEY, simulacion_id INTEGER NOT NULL REFERENCES simulacion(id) ON DELETE CASCADE,
  metodo TEXT NOT NULL, tolerancia REAL, paso REAL, max_iter INTEGER, convergio INTEGER, tiempo_ms REAL);
CREATE TABLE IF NOT EXISTS iteracion_resultado (
  id INTEGER PRIMARY KEY, ejecucion_id INTEGER NOT NULL REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
  numero INTEGER, aproximacion_json TEXT, residual REAL, error_abs REAL, error_rel REAL);
CREATE TABLE IF NOT EXISTS resultado_resumen (
  id INTEGER PRIMARY KEY, ejecucion_id INTEGER NOT NULL REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
  referencia TEXT, valor_json TEXT, metrica_error_json TEXT, interpretacion TEXT);
INSERT OR IGNORE INTO caso_estudio(id,nombre) VALUES
 (1,'Detención de emergencia'),(2,'Deterioro y mantenimiento'),(3,'Oscilaciones por viento'),(4,'Sensores');
