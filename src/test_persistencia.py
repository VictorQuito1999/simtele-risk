"""
Prueba obligatoria de persistencia (Rúbrica Sección 8):
ejecutar -> guardar -> cerrar/actualizar -> recuperar parámetros, iteraciones y gráficos -> repetir el cálculo -> demostrar coincidencia dentro de la tolerancia.
"""
import os, sys, json, sqlite3
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from metodos import METODOS, err_abs
import modulo2

TEST_DB = os.path.join(os.path.dirname(__file__), 'test_simtele.db')

def init_test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    with sqlite3.connect(TEST_DB) as conn:
        conn.executescript(open(schema_path).read())

def test_ciclo_persistencia():
    init_test_db()
    
    # 1. EJECUTAR
    tipo = 'NORMAL'
    e, out = modulo2.ejecutar(tipo)
    params = dict(n=len(e['b']), tol=e['tol'], perturbacion=e['pert'],
                  A=e['A'].tolist(), b=e['b'].tolist(), x_ref=e['xs'].tolist())
    
    # 2. GUARDAR
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys=ON;')
    
    esc = c.execute('INSERT INTO escenario(caso_id,tipo,parametros_json,fuente_datos) VALUES(?,?,?,?) RETURNING id',
                    (2, tipo, json.dumps(params), 'Sintético de prueba')).fetchone()[0]
    sim = c.execute('INSERT INTO simulacion(escenario_id) VALUES(?) RETURNING id', (esc,)).fetchone()[0]
    
    for m, r in out.items():
        ex = c.execute('INSERT INTO ejecucion_metodo(simulacion_id,metodo,tolerancia,max_iter,convergio,tiempo_ms) VALUES(?,?,?,?,?,?) RETURNING id',
                       (sim, m, e['tol'], 5000, int(r['converged']), round(r['tiempo_ms'], 2))).fetchone()[0]
        c.executemany('INSERT INTO iteracion_resultado(ejecucion_id,numero,aproximacion_json,residual,error_abs,error_rel) VALUES(?,?,?,?,?,?)',
                      [(ex, h['k'], json.dumps(h['x']), h['residual'], h['err_abs'], h['err_rel']) for h in r['hist']])
    conn.commit()
    
    # 3. CERRAR / ACTUALIZAR (cerrar completamente la conexión a la base de datos)
    conn.close()
    
    # 4. RECUPERAR (abrir nueva conexión como si reiniciara el servidor)
    conn2 = sqlite3.connect(TEST_DB)
    conn2.row_factory = sqlite3.Row
    c2 = conn2.cursor()
    
    sim_rec = c2.execute('SELECT s.*, e.tipo, e.parametros_json FROM simulacion s JOIN escenario e ON e.id=s.escenario_id WHERE s.id=?', (sim,)).fetchone()
    assert sim_rec is not None, "La simulación debe existir en disco"
    
    params_rec = json.loads(sim_rec['parametros_json'])
    A_rec = np.array(params_rec['A'])
    b_rec = np.array(params_rec['b'])
    xs_rec = np.array(params_rec['x_ref'])
    tol_rec = params_rec['tol']
    
    # 5. REPETIR EL CÁLCULO
    out_repetido = {}
    for m in METODOS:
        out_repetido[m] = METODOS[m](A_rec, b_rec, xs_rec, tol=tol_rec, max_iter=5000)
    
    # 6. DEMOSTRAR COINCIDENCIA DENTRO DE LA TOLERANCIA
    ejecs = c2.execute('SELECT id, metodo, convergio FROM ejecucion_metodo WHERE simulacion_id=? AND metodo IN ("Jacobi","Gauss-Seidel","LU","Gradiente conjugado")', (sim,)).fetchall()
    assert len(ejecs) == len(METODOS), "Deben haberse guardado los métodos de calibración"
    
    for ej in ejecs:
        m = ej['metodo']
        r_rec = out_repetido[m]
        assert ej['convergio'] == int(r_rec['converged']), f"Convergencia de {m} no coincide"
        
        # Iteraciones históricas guardadas
        filas_db = c2.execute('SELECT numero, aproximacion_json, residual, error_rel FROM iteracion_resultado WHERE ejecucion_id=? ORDER BY numero', (ej['id'],)).fetchall()
        assert len(filas_db) == len(r_rec['hist']), f"Número de iteraciones guardadas no coincide para {m}"
        
        for f_db, h_rep in zip(filas_db, r_rec['hist']):
            x_db = np.array(json.loads(f_db['aproximacion_json']))
            x_rep = np.array(h_rep['x'])
            assert np.allclose(x_db, x_rep, atol=1e-14), f"Vector de aproximación no coincide en paso {f_db['numero']} de {m}"
            if np.isfinite(h_rep['residual']):
                assert abs(f_db['residual'] - h_rep['residual']) < 1e-14, f"Residuo no coincide en {m}"
            if np.isfinite(h_rep['err_rel']):
                assert abs(f_db['error_rel'] - h_rep['err_rel']) < 1e-14, f"Error relativo no coincide en {m}"
                
    conn2.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print("Prueba de persistencia exitosa: coincidencia exacta (atol < 1e-14) entre BD y recalculo.")

if __name__ == '__main__':
    test_ciclo_persistencia()

