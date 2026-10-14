import os
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- CONFIGURACIÓN DE LA BASE DE DATOS SQL ---
DB_URL = "sqlite:///inmobiliaria.db"
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Directorio para guardar las fotos de los inmuebles físicamente
UPLOAD_DIR = "fotos_inmuebles"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- DEFINICIÓN DE TABLAS (MODELOS) ---
class Inmueble(Base):
    __tablename__ = "inmuebles"
    id  =   Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50))              # Urbano o Rural
    modalidad = Column(String(50))         # Arriendo, Venta, Proyectos
    tipo_propiedad = Column(String(50))    # Casa, Apartamento, etc.
    titulo = Column(String(150))
    ubicacion = Column(String(200))
    precio = Column(Float)
    habitaciones = Column(Integer, default=0)
    banos = Column(Integer, default=0)
    estrato = Column(String(20), default="3")       # 1, 2, 3, 4, 5, 6, Campestre, Comercial
    parqueadero = Column(Integer, default=0)        # Cantidad de parqueaderos
    antiguedad = Column(String(50), default="Menor a 1 año") # Menor a 1 año, 1 a 8 años, etc.
    foto_path = Column(String(300))

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150))
    telefono = Column(String(50))
    email = Column(String(100))

class Asesor(Base):
    __tablename__ = "asesores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150))
    codigo = Column(String(50))

class Cita(Base):
    __tablename__ = "citas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inmueble_id = Column(Integer, ForeignKey("inmuebles.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    asesor_id = Column(Integer, ForeignKey("asesores.id"))
    fecha_hora = Column(DateTime)
    estado = Column(String(50), default="Programada")  # Programada, Finalizada
    incumplimiento = Column(String(100), default="N/A") # Ninguno, Cliente, Inmobiliaria

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# Función auxiliar para abrir una sesión de base de datos
def get_db():
    return SessionLocal()

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="Inmobiliaria - Control de Citas e Inmuebles", layout="wide")
import base64

import base64

def add_watermark(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        css = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("data:image/png;base64,{encoded}") !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-size: 450px !important;
            background-attachment: fixed !important;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    else:
        st.warning(f"No se encontró la imagen de marca de agua en: {image_file}")

# Llama a la función usando una cadena cruda (r"...") para evitar problemas con las rutas de Windows
add_watermark(r"C:\inetpub\wwwroot\app_inmobiliaria\fotos_inmuebles\house-logo.png")
##add_watermark(r"C:\inetpub\wwwroot\app_inmobiliaria\fotos_inmuebles\casa-logo1.png")

st.sidebar.title("Menú Principal")
menu = st.sidebar.selectbox("Navegación", [
    "Gestión de Inmuebles", 
    "Gestión de Clientes", 
    "Gestión de Asesores", 
    "Control de Citas"
])

db = get_db()

# --- 1. GESTIÓN DE INMUEBLES ---
if menu == "Gestión de Inmuebles":
    st.header("🏠 Control y Filtrado Avanzado de Inmuebles")
    
    sub_menu_inm = st.radio("Acción:", ["Ver y Filtrar Inmuebles", "➕ Registrar Nuevo Inmueble", "✏️ Editar / 🗑️ Eliminar Inmueble"], key="sub_inm", horizontal=True)
    
    # --- REGISTRAR NUEVO INMUEBLE ---
    if sub_menu_inm == "➕ Registrar Nuevo Inmueble":
        st.subheader("Registrar Inmueble con Filtros Detallados")
        with st.form("form_inmueble_avanzado", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Zona", ["Urbano", "Rural"])
                modalidad = st.selectbox("Tipo de oferta / Modalidad", ["Arriendo", "Venta", "Proyectos"])
                tipo_propiedad = st.selectbox("Tipo de Inmueble", [
                    "Casa", "Apartamento", "Apartaestudio", "Cabaña", 
                    "Casa Campestre", "Casa Lote", "Finca", "Habitación", "Lote"
                ])
                titulo = st.text_input("Título / Descripción")
                ubicacion = st.text_input("Ubicación (Ciudad, Barrio o Vereda)")
                precio = st.number_input("Precio ($)", min_value=0.0, step=100000.0)
            with col2:
                habitaciones = st.number_input("Habitaciones", min_value=0, step=1)
                banos = st.number_input("Baños", min_value=0, step=1)
                estrato = st.selectbox("Estrato", ["1", "2", "3", "4", "5", "6", "Campestre", "Comercial"])
                parqueadero = st.number_input("Parqueaderos", min_value=0, step=1)
                antiguedad = st.selectbox("Antigüedad", ["Menor a 1 año", "De 1 a 8 años", "De 9 a 15 años", "Más de 15 años"])
                foto_subida = st.file_uploader("Cargar Foto", type=["jpg", "jpeg", "png"])
                
            submitted = st.form_submit_button("Guardar Inmueble")
            
            if submitted and titulo:
                foto_path = ""
                if foto_subida is not None:
                    foto_path = os.path.join(UPLOAD_DIR, foto_subida.name)
                    with open(foto_path, "wb") as f:
                        f.write(foto_subida.getbuffer())
                
                nuevo = Inmueble(
                    tipo=tipo, modalidad=modalidad, tipo_propiedad=tipo_propiedad,
                    titulo=titulo, ubicacion=ubicacion, precio=precio,
                    habitaciones=habitaciones, banos=banos, estrato=estrato,
                    parqueadero=parqueadero, antiguedad=antiguedad, foto_path=foto_path
                )
                db.add(nuevo)
                db.commit()
                st.success(f"Inmueble '{titulo}' registrado con éxito.")

    # --- VER Y FILTRAR INMUEBLES ---
    elif sub_menu_inm == "Ver y Filtrar Inmuebles":
        st.subheader("🔍 Filtros de Búsqueda Estilo Portal Inmobiliario")
        
        with st.expander("🛠️ Panel de Filtros Avanzados", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                f_modalidad = st.selectbox("Tipo de Oferta", ["Todos", "Arriendo", "Venta", "Proyectos"])
                f_tipo_prop = st.selectbox("Tipo de Inmueble", ["Todos", "Casa", "Apartamento", "Apartaestudio", "Cabaña", "Casa Campestre", "Finca", "Habitación"])
                f_estrato = st.selectbox("Estrato", ["Todos", "1", "2", "3", "4", "5", "6", "Campestre", "Comercial"])
            with col_f2:
                f_precio_min = st.number_input("Precio Mínimo ($)", min_value=0.0, value=0.0, step=100000.0)
                f_precio_max = st.number_input("Precio Máximo ($)", min_value=0.0, value=1000000000.0, step=1000000.0)
                f_antiguedad = st.selectbox("Antigüedad", ["Todos", "Menor a 1 año", "De 1 a 8 años", "De 9 a 15 años", "Más de 15 años"])
            with col_f3:
                f_hab = st.selectbox("Habitaciones (mínimo)", ["Todos", "1+", "2+", "3+", "4+"])
                f_banos = st.selectbox("Baños (mínimo)", ["Todos", "1+", "2+", "3+"])
                f_parq = st.selectbox("Parqueadero (mínimo)", ["Todos", "1", "2", "3", "4+"])
                
            busqueda_texto = st.text_input("Ubicación o palabra clave (Ej. Bogotá)", "")

        # Consultar y aplicar filtros SQL
        query = db.query(Inmueble)
        
        if f_modalidad != "Todos":
            query = query.filter(Inmueble.modalidad == f_modalidad)
        if f_tipo_prop != "Todos":
            query = query.filter(Inmueble.tipo_propiedad == f_tipo_prop)
        if f_estrato != "Todos":
            query = query.filter(Inmueble.estrato == f_estrato)
        if f_antiguedad != "Todos":
            query = query.filter(Inmueble.antiguedad == f_antiguedad)
            
        query = query.filter(Inmueble.precio >= f_precio_min, Inmueble.precio <= f_precio_max)
        
        if f_hab != "Todos":
            num_h = int(f_hab.replace("+", ""))
            query = query.filter(Inmueble.habitaciones >= num_h)
        if f_banos != "Todos":
            num_b = int(f_banos.replace("+", ""))
            query = query.filter(Inmueble.banos >= num_b)
        if f_parq != "Todos":
            if "+" in f_parq:
                query = query.filter(Inmueble.parqueadero >= 4)
            else:
                query = query.filter(Inmueble.parqueadero >= int(f_parq))
                
        if busqueda_texto:
            query = query.filter(Inmueble.ubicacion.ilike(f"%{busqueda_texto}%") | Inmueble.titulo.ilike(f"%{busqueda_texto}%"))
            
        resultados = query.all()
        st.markdown(f"### Resultados encontrados: {len(resultados)}")
        
        if resultados:
            for inm in resultados:
                with st.expander(f"[{inm.modalidad}] {inm.titulo} - ${inm.precio:,.0f} ({inm.tipo_propiedad})"):
                    c_det1, c_det2 = st.columns([2, 1])
                    with c_det1:
                        st.write(f"**Ubicación:** {inm.ubicacion}")
                        st.write(f"**Estrato:** {inm.estrato} | **Habitaciones:** {inm.habitaciones} | **Baños:** {inm.banos}")
                        st.write(f"**Parqueaderos:** {inm.parqueadero} | **Antigüedad:** {inm.antiguedad}")
                    with c_det2:
                        if inm.foto_path and os.path.exists(inm.foto_path):
                            st.image(Image.open(inm.foto_path), width=250)
        else:
            st.info("No hay inmuebles que coincidan con estos filtros.")

    # --- EDITAR / ELIMINAR INMUEBLE ---
    elif sub_menu_inm == "✏️ Editar / 🗑️ Eliminar Inmueble":
        st.subheader("Modificar o Borrar Inmuebles")
        inmuebles_totales = db.query(Inmueble).all()
        if inmuebles_totales:
            inm_dict = {f"ID #{i.id} - {i.titulo}": i.id for i in inmuebles_totales}
            sel_key = st.selectbox("Seleccione el Inmueble", list(inm_dict.keys()))
            inm_obj = db.query(Inmueble).get(inm_dict[sel_key])
            
            accion_ges = st.radio("Acción", ["Editar", "Eliminar"], horizontal=True)
            if accion_ges == "Editar":
                with st.form("form_edit_inm"):
                    n_tit = st.text_input("Título", value=inm_obj.titulo)
                    n_ubi = st.text_input("Ubicación", value=inm_obj.ubicacion)
                    n_pre = st.number_input("Precio", value=float(inm_obj.precio), step=100000.0)
                    n_est = st.selectbox("Estrato", ["1", "2", "3", "4", "5", "6", "Campestre", "Comercial"], index=["1", "2", "3", "4", "5", "6", "Campestre", "Comercial"].index(inm_obj.estrato) if inm_obj.estrato in ["1", "2", "3", "4", "5", "6", "Campestre", "Comercial"] else 2)
                    n_parq = st.number_input("Parqueaderos", value=int(inm_obj.parqueadero))
                    
                    if st.form_submit_button("Actualizar Cambios"):
                        inm_obj.titulo = n_tit
                        inm_obj.ubicacion = n_ubi
                        inm_obj.precio = n_pre
                        inm_obj.estrato = n_est
                        inm_obj.parqueadero = n_parq
                        db.commit()
                        st.success("¡Inmueble actualizado con éxito!")
                        st.rerun()
            else:
                with st.form("form_del_inm"):
                    st.warning("⚠️ ¿Estás seguro de eliminar este inmueble?")
                    if st.form_submit_button("Sí, Eliminar"):
                        db.delete(inm_obj)
                        db.commit()
                        st.success("Inmueble eliminado.")
                        st.rerun()
        else:
            st.info("No hay inmuebles registrados.")

# --- 2. GESTIÓN DE CLIENTES ---
# --- 2. GESTIÓN DE CLIENTES ---
elif menu == "Gestión de Clientes":
    st.header("👥 Control y Gestión de Clientes")
    
    accion_cliente = st.radio("Seleccione una acción:", ["Ver Clientes", "➕ Nuevo Cliente", "✏️ Editar Cliente", "🗑️ Eliminar Cliente"], key="radio_cliente", horizontal=True)
    
    # --- NUEVO CLIENTE ---
    if accion_cliente == "➕ Nuevo Cliente":
        st.subheader("Registrar Nuevo Cliente")
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre Completo")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Correo Electrónico")
            
            submitted = st.form_submit_button("Guardar Cliente")
            if submitted and nombre:
                db.add(Cliente(nombre=nombre, telefono=telefono, email=email))
                db.commit()
                st.success(f"¡Cliente {nombre} registrado con éxito!")

    # --- VER CLIENTES ---
    elif accion_cliente == "Ver Clientes":
        st.subheader("Listado de Clientes Registrados")
        clientes = db.query(Cliente).all()
        if clientes:
            df_cli = pd.DataFrame([{"ID": c.id, "Nombre": c.nombre, "Teléfono": c.telefono, "Email": c.email} for c in clientes])
            st.dataframe(df_cli, use_container_width=True)
        else:
            st.info("No hay clientes registrados.")

    # --- EDITAR CLIENTE ---
    elif accion_cliente == "✏️ Editar Cliente":
        st.subheader("Modificar Datos de Cliente")
        clientes = db.query(Cliente).all()
        if clientes:
            cli_dict = {f"{c.id} - {c.nombre}": c.id for c in clientes}
            sel_cli_edit = st.selectbox("Seleccione el Cliente a Editar", list(cli_dict.keys()))
            cli_id_sel = cli_dict[sel_cli_edit]
            cli_obj = db.query(Cliente).get(cli_id_sel)
            
            with st.form("form_editar_cliente"):
                nuevo_nombre = st.text_input("Nombre Completo", value=cli_obj.nombre)
                nuevo_tel = st.text_input("Teléfono", value=cli_obj.telefono)
                nuevo_email = st.text_input("Correo Electrónico", value=cli_obj.email)
                
                guardar_cambios = st.form_submit_button("Actualizar Cliente")
                if guardar_cambios:
                    cli_obj.nombre = nuevo_nombre
                    cli_obj.telefono = nuevo_tel
                    cli_obj.email = nuevo_email
                    db.commit()
                    st.success(f"¡Cliente #{cli_obj.id} actualizado correctamente!")
                    st.rerun()
        else:
            st.info("No hay clientes disponibles para editar.")

    # --- ELIMINAR CLIENTE ---
    elif accion_cliente == "🗑️ Eliminar Cliente":
        st.subheader("Eliminar Registro de Cliente")
        clientes = db.query(Cliente).all()
        if clientes:
            cli_dict_del = {f"{c.id} - {c.nombre}": c.id for c in clientes}
            sel_cli_del = st.selectbox("Seleccione el Cliente a Borrar", list(cli_dict_del.keys()))
            cli_id_del = cli_dict_del[sel_cli_del]
            
            with st.form("form_eliminar_cliente"):
                st.warning("⚠️ Precaución: Si este cliente tiene citas asociadas, podría generar conflictos en la base de datos.")
                confirmar_eliminar = st.form_submit_button("Sí, Eliminar Cliente")
                
                if confirmar_eliminar:
                    cli_a_borrar = db.query(Cliente).get(cli_id_del)
                    db.delete(cli_a_borrar)
                    db.commit()
                    st.success(f"Cliente eliminado con éxito.")
                    st.rerun()
        else:
            st.info("No hay clientes registrados para eliminar.")


# --- 3. GESTIÓN DE ASESORES ---
elif menu == "Gestión de Asesores":
    st.header("👔 Control y Gestión de Asesores")
    
    accion_asesor = st.radio("Seleccione una acción:", ["Ver Asesores", "➕ Nuevo Asesor", "✏️ Editar Asesor", "🗑️ Eliminar Asesor"], key="radio_asesor", horizontal=True)
    
    # --- NUEVO ASESOR ---
    if accion_asesor == "➕ Nuevo Asesor":
        st.subheader("Registrar Nuevo Asesor")
        with st.form("form_nuevo_asesor", clear_on_submit=True):
            nombre = st.text_input("Nombre del Asesor")
            codigo = st.text_input("Código de Empleado")
            
            submitted = st.form_submit_button("Guardar Asesor")
            if submitted and nombre:
                db.add(Asesor(nombre=nombre, codigo=codigo))
                db.commit()
                st.success(f"¡Asesor {nombre} registrado correctamente!")

    # --- VER ASESORES ---
    elif accion_asesor == "Ver Asesores":
        st.subheader("Listado de Asesores Registrados")
        asesores = db.query(Asesor).all()
        if asesores:
            df_ase = pd.DataFrame([{"ID": a.id, "Nombre": a.nombre, "Código": a.codigo} for a in asesores])
            st.dataframe(df_ase, use_container_width=True)
        else:
            st.info("No hay asesores registrados.")

    # --- EDITAR ASESOR ---
    elif accion_asesor == "✏️ Editar Asesor":
        st.subheader("Modificar Datos de Asesor")
        asesores = db.query(Asesor).all()
        if asesores:
            ase_dict = {f"{a.id} - {a.nombre}": a.id for a in asesores}
            sel_ase_edit = st.selectbox("Seleccione el Asesor a Editar", list(ase_dict.keys()))
            ase_id_sel = ase_dict[sel_ase_edit]
            ase_obj = db.query(Asesor).get(ase_id_sel)
            
            with st.form("form_editar_asesor"):
                nuevo_nombre = st.text_input("Nombre del Asesor", value=ase_obj.nombre)
                nuevo_codigo = st.text_input("Código de Empleado", value=ase_obj.codigo)
                
                guardar_cambios = st.form_submit_button("Actualizar Asesor")
                if guardar_cambios:
                    ase_obj.nombre = nuevo_nombre
                    ase_obj.codigo = nuevo_codigo
                    db.commit()
                    st.success(f"¡Asesor #{ase_obj.id} actualizado correctamente!")
                    st.rerun()
        else:
            st.info("No hay asesores disponibles para editar.")

    # --- ELIMINAR ASESOR ---
    elif accion_asesor == "🗑️ Eliminar Asesor":
        st.subheader("Eliminar Registro de Asesor")
        asesores = db.query(Asesor).all()
        if asesores:
            ase_dict_del = {f"{a.id} - {a.nombre}": a.id for a in asesores}
            sel_ase_del = st.selectbox("Seleccione el Asesor a Borrar", list(ase_dict_del.keys()))
            ase_id_del = ase_dict_del[sel_ase_del]
            
            with st.form("form_eliminar_asesor"):
                st.warning("⚠️ Precaución: Si este asesor tiene citas asociadas, ten en cuenta que podría afectar el historial.")
                confirmar_eliminar = st.form_submit_button("Sí, Eliminar Asesor")
                
                if confirmar_eliminar:
                    ase_a_borrar = db.query(Asesor).get(ase_id_del)
                    db.delete(ase_a_borrar)
                    db.commit()
                    st.success(f"Asesor eliminado con éxito.")
                    st.rerun()
        else:
            st.info("No hay asesores registrados para eliminar.")

# --- 3. GESTIÓN DE ASESORES ---
elif menu == "Gestión de Asesores":
    st.header("👔 Control de Asesores")
    with st.form("form_asesor", clear_on_submit=True):
        nombre = st.text_input("Nombre del Asesor")
        codigo = st.text_input("Código de Empleado")
        submitted = st.form_submit_button("Registrar Asesor")
        
        if submitted and nombre:
            db.add(Asesor(nombre=nombre, codigo=codigo))
            db.commit()
            st.success(f"Asesor {nombre} guardado correctamente.")
            
    asesores = db.query(Asesor).all()
    if asesores:
        df_ase = pd.DataFrame([{"ID": a.id, "Nombre": a.nombre, "Código": a.codigo} for a in asesores])
        st.dataframe(df_ase, use_container_width=True)

# --- 4. CONTROL Y VALIDACIÓN DE CITAS ---
elif menu == "Control de Citas":
    st.header("📅 Control de Citas y Validación de Cumplimiento")
    
    inmuebles = db.query(Inmueble).all()
    clientes = db.query(Cliente).all()
    asesores = db.query(Asesor).all()
    
    if not inmuebles or not clientes or not asesores:
        st.warning("⚠️ Debes tener al menos un Inmueble, un Cliente y un Asesor registrados para poder gestionar citas.")
    else:
        # Pestañas o botones de acción superior para organizar la interfaz
        accion_cita = st.radio("Seleccione una acción:", ["Ver / Validar Citas", "➕ Nueva Cita", "✏️ Editar Cita", "🗑️ Eliminar Cita"], horizontal=True)
        
        # --- NUEVA CITA ---
        if accion_cita == "➕ Nueva Cita":
            st.subheader("Agendar Nueva Cita")
            with st.form("form_nueva_cita", clear_on_submit=True):
                inm_dict = {f"{i.titulo} ({i.tipo})": i.id for i in inmuebles}
                cli_dict = {c.nombre: c.id for c in clientes}
                ase_dict = {a.nombre: a.id for a in asesores}
                
                sel_inm = st.selectbox("Seleccionar Inmueble", list(inm_dict.keys()))
                sel_cli = st.selectbox("Seleccionar Cliente", list(cli_dict.keys()))
                sel_ase = st.selectbox("Seleccionar Asesor", list(ase_dict.keys()))
                
                f_cita = st.date_input("Fecha de la Cita")
                h_cita = st.time_input("Hora de la Cita")
                
                agendar = st.form_submit_button("Guardar Nueva Cita")
                if agendar:
                    fecha_hora_combinada = datetime.combine(f_cita, h_cita)
                    nueva_cita = Cita(
                        inmueble_id=inm_dict[sel_inm],
                        cliente_id=cli_dict[sel_cli],
                        asesor_id=ase_dict[sel_ase],
                        fecha_hora=fecha_hora_combinada,
                        estado="Programada",
                        incumplimiento="N/A"
                    )
                    db.add(nueva_cita)
                    db.commit()
                    st.success("¡Cita agendada con éxito!")

        # --- VER / VALIDAR CITAS ---
        elif accion_cita == "Ver / Validar Citas":
            st.subheader("Listado y Validación de Cumplimiento")
            citas = db.query(Cita).all()
            if citas:
                for c in citas:
                    inm_obj = db.query(Inmueble).get(c.inmueble_id)
                    cli_obj = db.query(Cliente).get(c.cliente_id)
                    ase_obj = db.query(Asesor).get(c.asesor_id)
                    
                    with st.expander(f"Cita #{c.id} - Cliente: {cli_obj.nombre if cli_obj else 'N/A'} con Asesor: {ase_obj.nombre if ase_obj else 'N/A'}"):
                        st.write(f"**Inmueble:** {inm_obj.titulo if inm_obj else 'N/A'} ({inm_obj.tipo if inm_obj else ''})")
                        st.write(f"**Fecha y Hora:** {c.fecha_hora}")
                        st.write(f"**Estado actual:** {c.estado}")
                        st.write(f"**Incumplimiento:** {c.incumplimiento}")
                        
                        # Formulario de validación rápida
                        with st.form(f"val_cita_{c.id}"):
                            nuevo_estado = st.selectbox("Estado de la Cita", ["Programada", "Finalizada"], index=0 if c.estado=="Programada" else 1)
                            
                            opciones_incumplimiento = ["Ninguno / Cumplida", "Cliente", "Inmobiliaria (Asesor)"]
                            try:
                                idx_inc = opciones_incumplimiento.index(c.incumplimiento)
                            except ValueError:
                                idx_inc = 0
                                
                            responsable = st.selectbox("¿Quién incumplió (si aplica)?", opciones_incumplimiento, index=idx_inc)
                            
                            btn_actualizar = st.form_submit_button("Actualizar Validación")
                            if btn_actualizar:
                                c.estado = nuevo_estado
                                c.incumplimiento = responsable
                                db.commit()
                                st.success("¡Validación de cita actualizada!")
                                st.rerun()
            else:
                st.info("No hay citas registradas.")

        # --- EDITAR CITA ---
        elif accion_cita == "✏️ Editar Cita":
            st.subheader("Modificar Datos de una Cita Existente")
            citas = db.query(Cita).all()
            if citas:
                cita_dict = {f"Cita #{c.id} - Fecha: {c.fecha_hora}": c.id for c in citas}
                sel_cita_edit = st.selectbox("Seleccione la Cita a Editar", list(cita_dict.keys()))
                cita_id_sel = cita_dict[sel_cita_edit]
                cita_obj = db.query(Cita).get(cita_id_sel)
                
                with st.form("form_editar_cita"):
                    inm_dict = {f"{i.titulo} ({i.tipo})": i.id for i in inmuebles}
                    cli_dict = {c.nombre: c.id for c in clientes}
                    asesor_dict = {a.nombre: a.id for a in asesores}
                    
                    # Pre-seleccionar valores actuales de forma segura
                    inm_actual_key = next((k for k, v in inm_dict.items() if v == cita_obj.inmueble_id), list(inm_dict.keys())[0])
                    cli_actual_key = next((k for k, v in cli_dict.items() if v == cita_obj.cliente_id), list(cli_dict.keys())[0])
                    ase_actual_key = next((k for k, v in asesor_dict.items() if v == cita_obj.asesor_id), list(asesor_dict.keys())[0])
                    
                    nuevo_inm = st.selectbox("Inmueble", list(inm_dict.keys()), index=list(inm_dict.keys()).index(inm_actual_key))
                    nuevo_cli = st.selectbox("Cliente", list(cli_dict.keys()), index=list(cli_dict.keys()).index(cli_actual_key))
                    nuevo_ase = st.selectbox("Asesor", list(asesor_dict.keys()), index=list(asesor_dict.keys()).index(ase_actual_key))
                    
                    f_edit = st.date_input("Nueva Fecha", value=cita_obj.fecha_hora.date())
                    h_edit = st.time_input("Nueva Hora", value=cita_obj.fecha_hora.time())
                    
                    guardar_cambios = st.form_submit_button("Guardar Cambios")
                    if guardar_cambios:
                        cita_obj.inmueble_id = inm_dict[nuevo_inm]
                        cita_obj.cliente_id = cli_dict[nuevo_cli]
                        cita_obj.asesor_id = asesor_dict[nuevo_ase]
                        cita_obj.fecha_hora = datetime.combine(f_edit, h_edit)
                        db.commit()
                        st.success(f"¡Cita #{cita_obj.id} modificada correctamente!")
                        st.rerun()
            else:
                st.info("No hay citas disponibles para editar.")

        # --- ELIMINAR CITA ---
        elif accion_cita == "🗑️ Eliminar Cita":
            st.subheader("Eliminar Registro de Cita")
            citas = db.query(Cita).all()
            if citas:
                cita_dict_del = {f"Cita #{c.id} - Fecha: {c.fecha_hora}": c.id for c in citas}
                sel_cita_del = st.selectbox("Seleccione la Cita a Borrar", list(cita_dict_del.keys()))
                cita_id_del = cita_dict_del[sel_cita_del]
                
                with st.form("form_eliminar_cita"):
                    st.warning("⚠️ Esta acción eliminará permanentemente la cita de la base de datos.")
                    confirmar_eliminar = st.form_submit_button("Sí, Eliminar Cita")
                    
                    if confirmar_eliminar:
                        cita_a_borrar = db.query(Cita).get(cita_id_del)
                        db.delete(cita_a_borrar)
                        db.commit()
                        st.success(f"Cita #{cita_id_del} eliminada con éxito.")
                        st.rerun()
            else:
                st.info("No hay citas registradas para eliminar.")

db.close()