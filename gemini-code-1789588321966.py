import streamlit as st
import pandas as pd
import datetime
import sqlite3
import os

# Configuración de la página
st.set_page_config(
    page_title="MEGA TRAM - ERP Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS avanzados
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #f8fafc !important;
    }
    .stRadio label {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #f1f5f9 !important;
        padding: 6px 0px;
    }
    .stMetric {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }
    .stMetric label { color: #94a3b8 !important; font-weight: 600 !important; }
    .stMetric div[data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 1.8rem !important; }
    h1, h2, h3 {
        color: #0f172a;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Base de Datos SQLite
DB_NAME = "negocio_pro.db"

def ejecutar_sql(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def consultar_sql(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def inicializar_base_datos():
    ejecutar_sql('''CREATE TABLE IF NOT EXISTS productos (
        codigo TEXT PRIMARY KEY, descripcion TEXT NOT NULL, cantidad REAL, formato TEXT, costo_compra REAL, precio_venta REAL
    )''')
    ejecutar_sql('''CREATE TABLE IF NOT EXISTS gastos (
        id_gasto TEXT PRIMARY KEY, fecha TEXT, concepto TEXT, categoria TEXT, monto REAL, producto_asociado TEXT
    )''')
    ejecutar_sql('''CREATE TABLE IF NOT EXISTS empleados (
        id_empleado TEXT PRIMARY KEY, nombre TEXT, cargo TEXT, telefono TEXT, ci TEXT
    )''')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Verificar y corregir tabla ventas
    cursor.execute("PRAGMA table_info(ventas)")
    cols_v = [col[1] for col in cursor.fetchall()]
    if len(cols_v) != 10:
        cursor.execute("DROP TABLE IF EXISTS ventas")
        cursor.execute('''CREATE TABLE ventas (
            id_venta TEXT PRIMARY KEY, fecha TEXT, empleado TEXT, cliente TEXT, 
            codigo_producto TEXT, descripcion TEXT, cantidad REAL, precio_unitario REAL, total REAL, metodo_pago TEXT
        )''')
        conn.commit()
        
    # 2. Verificar y corregir tabla creditos de forma estricta
    cursor.execute("PRAGMA table_info(creditos)")
    cols_c = [col[1] for col in cursor.fetchall()]
    # Si falta la columna 'total' o la estructura no tiene 5 columnas, la reconstruimos obligatoriamente
    if "total" not in cols_c or len(cols_c) != 5:
        cursor.execute("DROP TABLE IF EXISTS creditos")
        cursor.execute('''CREATE TABLE creditos (
            id_credito TEXT PRIMARY KEY, cliente TEXT, fecha TEXT, total REAL, estado TEXT
        )''')
        conn.commit()
        
    conn.close()

inicializar_base_datos()

# Sidebar con Logo y Menú
st.sidebar.markdown("<h1 style='text-align: center; color: #38bdf8; font-size: 2rem;'>⚡ MEGA TRAM</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>Sistema de Gestión Comercial</p>", unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.warning("⚠️ Sube tu imagen como 'logo.png' en el directorio del proyecto.")

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 1.2rem; font-weight: bold; color: #f8fafc;'>Menú Principal</p>", unsafe_allow_html=True)

menu = st.sidebar.radio("", [
    "🛒 Ventas (POS)",
    "📦 Inventario",
    "👥 Empleados",
    "💸 Gastos",
    "📊 Estadísticas",
    "📒 Créditos"
], label_visibility="collapsed")

# ---------------------------------------------------------
# 1. PUNTO DE VENTA (POS)
# ---------------------------------------------------------
if menu == "🛒 Ventas (POS)":
    st.title("🛒 Punto de Venta")
    
    df_inv = consultar_sql("SELECT * FROM productos")
    df_emp = consultar_sql("SELECT * FROM empleados")
    
    if df_inv.empty:
        st.warning("⚠️ No hay productos registrados. Ve al módulo de Inventario para agregar.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Registrar Venta")
            empleados_lista = df_emp['nombre'].tolist() if not df_emp.empty else ["General"]
            emp_vende = st.selectbox("Empleado que atiende:", empleados_lista)
            cliente_nombre = st.text_input("Cliente:", value="Cliente General")
            
            dict_prods = dict(zip(
                df_inv['codigo'].astype(str) + " - " + df_inv['descripcion'] + " (Stock: " + df_inv['cantidad'].astype(str) + ")",
                df_inv['codigo']
            ))
            
            prod_sel_label = st.selectbox("Seleccionar Producto para Vender:", list(dict_prods.keys()))
            codigo_seleccionado = dict_prods[prod_sel_label]
            row_prod = df_inv[df_inv['codigo'].astype(str) == str(codigo_seleccionado)].iloc[0]
            
            with st.form("form_pos"):
                c1, c2 = st.columns(2)
                with c1: cant_vender = st.number_input("Cantidad", min_value=0.01, value=1.0, format="%.2f")
                with c2: precio_vender = st.number_input("Precio Unitario (Bs.)", value=float(row_prod['precio_venta']))
                
                metodo = st.selectbox("Método de Pago", ["Efectivo", "QR / Transferencia", "Tarjeta", "Crédito / Fiado"])
                
                subtotal = cant_vender * precio_vender
                st.markdown(f"### Total a Pagar: <span style='color: #38bdf8;'>Bs. {subtotal:,.2f}</span>", unsafe_allow_html=True)
                
                b_col1, b_col2 = st.columns(2)
                with b_col1: btn_completar = st.form_submit_button("✅ Completar Venta", use_container_width=True)
                with b_col2: btn_cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if btn_completar:
                    if row_prod['cantidad'] < cant_vender and metodo != "Crédito / Fiado":
                        st.error("❌ Stock insuficiente para completar la venta.")
                    else:
                        id_v = f"V-{int(datetime.datetime.now().timestamp())}"
                        fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        ejecutar_sql('INSERT INTO ventas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                                     (id_v, fecha_str, emp_vende, cliente_nombre, str(row_prod['codigo']), row_prod['descripcion'], cant_vender, precio_vender, subtotal, metodo))
                        
                        nuevo_stock = row_prod['cantidad'] - cant_vender
                        ejecutar_sql('UPDATE productos SET cantidad = ? WHERE codigo = ?', (nuevo_stock, str(row_prod['codigo'])))
                        
                        if metodo == "Crédito / Fiado":
                            ejecutar_sql('INSERT OR REPLACE INTO creditos VALUES (?, ?, ?, ?, ?)', 
                                         (id_v, cliente_nombre, fecha_str, subtotal, "Pendiente"))
                            
                        st.success(f"✅ Venta completada con éxito. ID: {id_v}")
                        st.rerun()
                if btn_cancelar:
                    st.info("Venta cancelada.")
                    
        with col2:
            st.subheader("Resumen Diario")
            df_hoy = consultar_sql("SELECT * FROM ventas WHERE fecha LIKE ?", (datetime.datetime.now().strftime("%Y-%m-%d") + "%",))
            st.metric("Ventas Hoy", f"Bs. {df_hoy['total'].sum() if not df_hoy.empty else 0.0:,.2f}")
            st.metric("Transacciones", f"{len(df_hoy)}")
            
            st.markdown("---")
            st.subheader("Eliminar Venta")
            df_todas_v = consultar_sql("SELECT id_venta, fecha, total, cliente FROM ventas ORDER BY fecha DESC LIMIT 20")
            if not df_todas_v.empty:
                v_sel = st.selectbox("Seleccionar Venta a Anular:", df_todas_v['id_venta'] + " - " + df_todas_v['cliente'] + " (Bs. " + df_todas_v['total'].astype(str) + ")")
                if st.button("🗑️ Eliminar Venta Seleccionada"):
                    vid = v_sel.split(" - ")[0]
                    ejecutar_sql("DELETE FROM ventas WHERE id_venta = ?", (vid,))
                    st.success("✅ Venta eliminada correctamente.")
                    st.rerun()

# ---------------------------------------------------------
# 2. INVENTARIO
# ---------------------------------------------------------
elif menu == "📦 Inventario":
    st.title("📦 Gestión de Inventario")
    
    df_inv = consultar_sql("SELECT * FROM productos")
    total_refs = len(df_inv)
    costo_inv = (df_inv['cantidad'] * df_inv['costo_compra']).sum() if not df_inv.empty else 0.0
    
    m1, m2 = st.columns(2)
    with m1: st.metric("Total Referencias", f"{total_refs}")
    with m2: st.metric("Costo Total Inventario", f"Bs. {costo_inv:,.2f}")
    
    st.markdown("---")
    
    with st.expander("➕ Crear Nuevo Producto"):
        with st.form("form_crear_prod"):
            cp1, cp2 = st.columns(2)
            with cp1:
                ncod = st.text_input("Código Único del Producto")
                ndesc = st.text_input("Descripción / Nombre")
                ncant = st.number_input("Cantidad Inicial", min_value=0.0, value=1.0)
            with cp2:
                nform = st.text_input("Unidad / Formato (Ej: Pza, Rollo, Kg, Litro)", value="Pza")
                ncost = st.number_input("Costo de Compra (Bs.)", min_value=0.0, value=10.0)
                nprec = st.number_input("Precio de Venta (Bs.)", min_value=0.0, value=15.0)
                
            bc1, bc2 = st.columns(2)
            with bc1: guardar_p = st.form_submit_button("✅ Completar Registro", use_container_width=True)
            with bc2: cancelar_p = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if guardar_p:
                if ncod and ndesc:
                    existe = consultar_sql("SELECT * FROM productos WHERE codigo = ?", (ncod,))
                    if not existe.empty:
                        st.error(f"❌ El código '{ncod}' ya existe.")
                    else:
                        ejecutar_sql('INSERT INTO productos VALUES (?, ?, ?, ?, ?, ?)', (ncod, ndesc, ncant, nform, ncost, nprec))
                        st.success("✅ Producto creado exitosamente.")
                        st.rerun()
                else:
                    st.error("Complete código y descripción.")
            if cancelar_p:
                st.info("Cancelado.")

    st.markdown("### Buscador y Edición de Productos")
    busqueda_inv = st.text_input("🔍 Buscar producto por código o nombre:")
    df_inv_filtrado = consultar_sql("SELECT * FROM productos WHERE codigo LIKE ? OR descripcion LIKE ?", (f"%{busqueda_inv}%", f"%{busqueda_inv}%")) if busqueda_inv else df_inv

    if not df_inv_filtrado.empty:
        with st.form("form_edit_inv"):
            df_editado = st.data_editor(df_inv_filtrado, use_container_width=True)
            be1, be2 = st.columns(2)
            with be1: guardar_inv = st.form_submit_button("✅ Guardar Cambios", use_container_width=True)
            with be2: cancelar_inv = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if guardar_inv:
                conn = sqlite3.connect(DB_NAME)
                for _, row in df_editado.iterrows():
                    conn.execute('INSERT OR REPLACE INTO productos VALUES (?, ?, ?, ?, ?, ?)', 
                                 (str(row['codigo']), str(row['descripcion']), float(row['cantidad']), str(row['formato']), float(row['costo_compra']), float(row['precio_venta'])))
                conn.commit()
                conn.close()
                st.success("✅ Inventario actualizado.")
                st.rerun()

# ---------------------------------------------------------
# 3. EMPLEADOS
# ---------------------------------------------------------
elif menu == "👥 Empleados":
    st.title("👥 Gestión de Empleados")
    
    with st.form("form_empleado"):
        ep1, ep2 = st.columns(2)
        with ep1:
            e_id = st.text_input("ID o Código de Empleado")
            e_nom = st.text_input("Nombre Completo")
            e_cargo = st.text_input("Cargo")
        with ep2:
            e_tel = st.text_input("Teléfono")
            e_ci = st.text_input("Cédula de Identidad (CI)")
            
        ec1, ec2 = st.columns(2)
        with ec1: save_emp = st.form_submit_button("✅ Completar Registro", use_container_width=True)
        with ec2: canc_emp = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if save_emp:
            if e_id and e_nom:
                ejecutar_sql('INSERT OR REPLACE INTO empleados VALUES (?, ?, ?, ?, ?)', (e_id, e_nom, e_cargo, e_tel, e_ci))
                st.success("✅ Empleado registrado.")
                st.rerun()
            else:
                st.error("Complete los campos requeridos.")
                
    st.markdown("---")
    st.subheader("Lista de Empleados")
    st.dataframe(consultar_sql("SELECT * FROM empleados"), use_container_width=True)

# ---------------------------------------------------------
# 4. GASTOS
# ---------------------------------------------------------
elif menu == "💸 Gastos":
    st.title("💸 Registro de Gastos")
    df_inv_g = consultar_sql("SELECT * FROM productos")
    
    with st.form("form_gasto"):
        g1, g2 = st.columns(2)
        with g1:
            g_desc = st.text_input("Concepto del Gasto")
            g_cat = st.selectbox("Categoría", ["Compras de productos", "Gastos personales", "Logística", "Otros"])
            prod_asoc = ""
            if g_cat == "Compras de productos" and not df_inv_g.empty:
                prod_asoc = st.selectbox("Seleccionar Producto:", df_inv_g['codigo'] + " - " + df_inv_g['descripcion'])
        with g2:
            g_monto = st.number_input("Monto (Bs.)", min_value=0.0, value=50.0)
            g_cant_compra = st.number_input("Cantidad a sumar al inventario", min_value=0.0, value=1.0)
            g_fecha = st.date_input("Fecha", value=datetime.date.today())
            
        gc1, gc2 = st.columns(2)
        with gc1: save_g = st.form_submit_button("✅ Completar Gasto", use_container_width=True)
        with gc2: canc_g = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if save_g:
            id_g = f"G-{int(datetime.datetime.now().timestamp())}"
            ejecutar_sql('INSERT INTO gastos VALUES (?, ?, ?, ?, ?, ?)', (id_g, g_fecha.strftime("%Y-%m-%d"), g_desc, g_cat, g_monto, prod_asoc))
            if g_cat == "Compras de productos" and prod_asoc:
                cod_prod = prod_asoc.split(" - ")[0]
                row_inv = df_inv_g[df_inv_g['codigo'].astype(str) == str(cod_prod)]
                if not row_inv.empty:
                    nuevo_stock = float(row_inv.iloc[0]['cantidad']) + g_cant_compra
                    ejecutar_sql('UPDATE productos SET cantidad = ? WHERE codigo = ?', (nuevo_stock, cod_prod))
            st.success("✅ Gasto registrado.")
            st.rerun()
            
    st.markdown("---")
    st.subheader("Historial de Gastos")
    st.dataframe(consultar_sql("SELECT * FROM gastos"), use_container_width=True)

# ---------------------------------------------------------
# 5. ESTADÍSTICAS
# ---------------------------------------------------------
elif menu == "📊 Estadísticas":
    st.title("📊 Estadísticas y Balance Financiero")
    df_v = consultar_sql("SELECT * FROM ventas")
    df_g = consultar_sql("SELECT * FROM gastos")
    
    tot_v = df_v['total'].sum() if not df_v.empty else 0.0
    tot_g = df_g['monto'].sum() if not df_g.empty else 0.0
    utilidad = tot_v - tot_g
    
    b1, b2, b3 = st.columns(3)
    with b1: st.metric("Ventas Totales", f"Bs. {tot_v:,.2f}")
    with b2: st.metric("Gastos Totales", f"Bs. {tot_g:,.2f}")
    with b3: st.metric("Utilidad Neta", f"Bs. {utilidad:,.2f}")

# ---------------------------------------------------------
# 6. CRÉDITOS
# ---------------------------------------------------------
elif menu == "📒 Créditos":
    st.title("📒 Cuentas por Cobrar (Créditos / Fiados)")
    
    df_cred = consultar_sql("SELECT * FROM creditos")
    
    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)
        
        st.markdown("### Registrar Pago de Crédito")
        pendientes = df_cred[df_cred['estado'] == 'Pendiente']
        
        if not pendientes.empty:
            with st.form("form_pagar_credito"):
                cred_sel = st.selectbox("Seleccionar Crédito a Pagar:", pendientes['id_credito'] + " - " + pendientes['cliente'] + " (Bs. " + pendientes['total'].astype(str) + ")")
                
                cp_1, cp_2 = st.columns(2)
                with cp_1: btn_pagar = st.form_submit_button("✅ Marcar como Pagado", use_container_width=True)
                with cp_2: btn_canc_c = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if btn_pagar:
                    cid = cred_sel.split(" - ")[0]
                    ejecutar_sql("UPDATE creditos SET estado = 'Pagado' WHERE id_credito = ?", (cid,))
                    st.success(f"✅ El crédito {cid} ha sido marcado como PAGADO.")
                    st.rerun()
                if btn_canc_c:
                    st.info("Cancelado.")
        else:
            st.success("🎉 ¡No hay créditos pendientes de cobro!")
    else:
        st.info("No hay registros de créditos.")