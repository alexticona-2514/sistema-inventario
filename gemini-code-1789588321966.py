import streamlit as st
import pandas as pd
import datetime
import os

# Configuración de página optimizada para móviles y PC
st.set_page_config(
    page_title="Gestión de Inventario y Ventas", 
    page_icon="📦", 
    layout="centered"
)

INVENTARIO_FILE = "Inventario.csv"
VENTAS_FILE = "registro_ventas.csv"
COMPRAS_FILE = "registro_compras.csv"

# Inicializar archivos si no existen
@st.cache_data
def cargar_datos():
    if not os.path.exists(INVENTARIO_FILE):
        df_init = pd.DataFrame(columns=['Código', 'Descripción', 'Cantidad', 'Formato', 'Costo de Compra', 'Precio de Venta'])
        df_init.to_csv(INVENTARIO_FILE, index=False)
    
    if not os.path.exists(VENTAS_FILE):
        df_ventas = pd.DataFrame(columns=['ID_Venta', 'Fecha', 'Código', 'Descripción', 'Cantidad', 'Precio_Unitario', 'Total', 'Cliente'])
        df_ventas.to_csv(VENTAS_FILE, index=False)
        
    if not os.path.exists(COMPRAS_FILE):
        df_compras = pd.DataFrame(columns=['ID_Compra', 'Fecha', 'Código', 'Descripción', 'Cantidad', 'Costo_Unitario', 'Total'])
        df_compras.to_csv(COMPRAS_FILE, index=False)

cargar_datos()

# Categorización automática
def obtener_categoria(desc):
    desc = str(desc).upper()
    if "BAT." in desc or "BATERIA" in desc:
        return "Baterías"
    elif "ACEIT." in desc or "ACEITE" in desc:
        return "Aceites y Lubricantes"
    elif "FRENO" in desc or "PASTILLA" in desc or "DISCO" in desc or "CILINDRO" in desc:
        return "Frenos"
    elif "FILTR" in desc:
        return "Filtros"
    elif "BOMBA" in desc:
        return "Bombas"
    elif "RELAY" in desc or "VALVULA" in desc:
        return "Eléctrico / Sensores"
    else:
        return "Otros / Repuestos"

st.title("📱📦 Sistema Móvil de Ventas e Inventario")

opcion = st.selectbox("📌 SELECCIONE UNA OPCIÓN:", [
    "🛒 Registrar Venta Rápida",
    "📦 Registrar Compra / Ingreso",
    "📋 Ver Inventario y Stock",
    "📊 Balance y Ventas por Fechas",
    "🏷️ Categorías"
])

df_inv = pd.read_csv(INVENTARIO_FILE)
df_inv['Categoría'] = df_inv['Descripción'].apply(obtener_categoria)

if opcion == "🛒 Registrar Venta Rápida":
    st.subheader("🛒 Nueva Venta")
    
    busqueda_prod = st.text_input("🔍 Buscar producto por nombre o código:")
    df_filtrado = df_inv.copy()
    if busqueda_prod:
        df_filtrado = df_filtrado[
            df_filtrado['Descripción'].str.contains(busqueda_prod, case=False, na=False) |
            df_filtrado['Código'].astype(str).str.contains(busqueda_prod, case=False, na=False)
        ]
    
    if df_filtrado.empty:
        st.warning("No se encontraron productos.")
    else:
        productos_dict = dict(zip(df_filtrado['Descripción'] + " (Stock: " + df_filtrado['Cantidad'].astype(str) + " | Bs. " + df_filtrado['Precio de Venta'].astype(str) + ")", df_filtrado['Código']))
        prod_seleccionado = st.selectbox("Seleccione el producto de la lista:", list(productos_dict.keys()))
        
        codigo_prod = productos_dict[prod_seleccionado]
        fila_prod = df_inv[df_inv['Código'] == codigo_prod].iloc[0]
        
        stock_actual = fila_prod['Cantidad']
        precio_sugerido = fila_prod['Precio de Venta']
        
        st.info(f"📦 **Stock actual:** {stock_actual} | 💲 **Precio sugerido:** Bs. {precio_sugerido}")
        
        with st.form("form_venta_movil"):
            cantidad_venta = st.number_input("Cantidad a vender", min_value=1, max_value=int(stock_actual) if stock_actual > 0 else 1, value=1)
            precio_venta = st.number_input("Precio unitario final (Bs.)", value=float(precio_sugerido))
            cliente = st.text_input("Cliente / Notas", value="General")
            
            submit_venta = st.form_submit_button("✅ Confirmar y Registrar Venta")
            
            if submit_venta:
                if stock_actual < cantidad_venta:
                    st.error("❌ Stock insuficiente.")
                else:
                    df_inv.loc[df_inv['Código'] == codigo_prod, 'Cantidad'] -= cantidad_venta
                    df_inv.drop(columns=['Categoría'], errors='ignore').to_csv(INVENTARIO_FILE, index=False)
                    
                    df_ventas = pd.read_csv(VENTAS_FILE)
                    nueva_venta = {
                        'ID_Venta': f"V-{int(datetime.datetime.now().timestamp())}",
                        'Fecha': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Código': codigo_prod,
                        'Descripción': fila_prod['Descripción'],
                        'Cantidad': cantidad_venta,
                        'Precio_Unitario': precio_venta,
                        'Total': cantidad_venta * precio_venta,
                        'Cliente': cliente
                    }
                    df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
                    df_ventas.to_csv(VENTAS_FILE, index=False)
                    st.success(f"🎉 ¡Venta registrada con éxito! Total: Bs. {cantidad_venta * precio_venta:,.2f}")

elif opcion == "📦 Registrar Compra / Ingreso":
    st.subheader("📦 Registrar Compra de Mercadería")
    
    busqueda_c = st.text_input("🔍 Buscar producto para reabastecer:")
    df_f_c = df_inv.copy()
    if busqueda_c:
        df_f_c = df_f_c[
            df_f_c['Descripción'].str.contains(busqueda_c, case=False, na=False) |
            df_f_c['Código'].astype(str).str.contains(busqueda_c, case=False, na=False)
        ]
        
    if not df_f_c.empty:
        prod_dict_c = dict(zip(df_f_c['Descripción'] + " (Stock actual: " + df_f_c['Cantidad'].astype(str) + ")", df_f_c['Código']))
        prod_sel_c = st.selectbox("Seleccione producto:", list(prod_dict_c.keys()))
        cod_c = prod_dict_c[prod_sel_c]
        row_c = df_inv[df_inv['Código'] == cod_c].iloc[0]
        
        with st.form("form_compra_movil"):
            cant_c = st.number_input("Cantidad comprada", min_value=1, value=10)
            costo_c = st.number_input("Costo unitario (Bs.)", value=float(row_c['Costo de Compra']))
            precio_v_nuevo = st.number_input("Nuevo precio de venta (Bs.)", value=float(row_c['Precio de Venta']))
            
            sub_c = st.form_submit_button("✅ Registrar Compra y Actualizar Stock")
            if sub_c:
                df_inv.loc[df_inv['Código'] == cod_c, 'Cantidad'] += cant_c
                df_inv.loc[df_inv['Código'] == cod_c, 'Costo de Compra'] = costo_c
                df_inv.loc[df_inv['Código'] == cod_c, 'Precio de Venta'] = precio_v_nuevo
                df_inv.drop(columns=['Categoría'], errors='ignore').to_csv(INVENTARIO_FILE, index=False)
                
                df_compras = pd.read_csv(COMPRAS_FILE)
                nueva_compra = {
                    'ID_Compra': f"C-{int(datetime.datetime.now().timestamp())}",
                    'Fecha': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Código': cod_c,
                    'Descripción': row_c['Descripción'],
                    'Cantidad': cant_c,
                    'Costo_Unitario': costo_c,
                    'Total': cant_c * costo_c
                }
                df_compras = pd.concat([df_compras, pd.DataFrame([nueva_compra])], ignore_index=True)
                df_compras.to_csv(COMPRAS_FILE, index=False)
                st.success("🎉 ¡Stock y compras actualizadas correctamente!")

elif opcion == "📋 Ver Inventario y Stock":
    st.subheader("📋 Inventario Actual")
    busq = st.text_input("🔍 Filtro rápido de inventario:")
    df_m = df_inv.copy()
    if busq:
        df_m = df_m[df_m['Descripción'].str.contains(busq, case=False, na=False) | df_m['Código'].astype(str).str.contains(busq, case=False, na=False)]
    st.dataframe(df_m[['Código', 'Descripción', 'Cantidad', 'Formato', 'Precio de Venta']], use_container_width=True)

elif opcion == "📊 Balance y Ventas por Fechas":
    st.subheader("📊 Balance Financiero y Reportes")
    df_ventas = pd.read_csv(VENTAS_FILE)
    df_compras = pd.read_csv(COMPRAS_FILE)
    
    total_v = df_ventas['Total'].sum() if not df_ventas.empty else 0.0
    total_c = df_compras['Total'].sum() if not df_compras.empty else 0.0
    
    st.metric("Total Ingresos por Ventas", f"Bs. {total_v:,.2f}")
    st.metric("Total Gastos en Compras", f"Bs. {total_c:,.2f}")
    st.metric("Balance Neto", f"Bs. {total_v - total_c:,.2f}")
    
    if not df_ventas.empty:
        st.markdown("---")
        st.subheader("📈 Ventas por Fecha")
        df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])
        df_ventas['Día'] = df_ventas['Fecha'].dt.date
        resumen_fechas = df_ventas.groupby('Día')['Total'].sum().reset_index()
        st.bar_chart(resumen_fechas.set_index('Día')['Total'])

elif opcion == "🏷️ Categorías":
    st.subheader("🏷️ Productos por Categoría")
    cat = st.selectbox("Seleccione categoría:", df_inv['Categoría'].unique())
    st.dataframe(df_inv[df_inv['Categoría'] == cat][['Código', 'Descripción', 'Cantidad', 'Precio de Venta']], use_container_width=True)