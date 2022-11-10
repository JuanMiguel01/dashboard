import streamlit as st
from uuid import uuid4
from models import Project


st.set_page_config(
    page_title="MatCom Dashboard - Proyectos", page_icon="⚗️", layout="wide"
)


def save_project(project: Project, prefix):
    project.save()

    for key in st.session_state.keys():
        print(key, flush=True)
        if key.startswith(prefix):
            del st.session_state[key]

    del st.session_state.current_project
    print(st.session_state, flush=True)

    st.success("Proyecto guardado con éxito")


st.title("⚗️ Proyectos")

list_view, create_view, edit_view = st.tabs(["⚗️ Listado de proyectos", "⭐ Crear nuevo proyecto", "📝 Editar proyecto"])


with create_view:
    if st.session_state.get('write_access', False):
        if "current_project" in st.session_state:
            key = st.session_state.current_project
        else:
            key = str(uuid4())
            st.session_state.current_project = key

        project = Project.create(key=key)

        if project is not None:
            st.button("💾 Guardar", on_click=save_project, args=(project, key))
        else:
            st.warning("⚠️ Complete la información obligatoria, marcada con 🔹")
    else:
        st.error("Acceso de solo lectura. Vaya a la página principal para loguearse.")


projects = Project.all()
projects.sort(key=lambda p: p.title)


with list_view:
    for project in projects:
        with st.expander(f"{project.title} - {project.main_entity} - {project.project_type} ({len(project.members)} participantes)"):
            st.write(f"#### {project.title} [{project.code}]")

            left, right = st.columns(2)
            with left:
                st.write(f"**Tipo**: {project.project_type}")
                st.write(f"**Programa**: {project.program or ''}")
                st.write(f"**Coordinador**: {project.head.name} ({project.head.institution})")
                st.write(f"**Estado**: {project.status}")
                st.write(f"##### Miembros:\n" + "\n".join(f"- {person.name} ({person.institution})" for person in project.members))

            with right:
                st.write(f"##### Entidad ejecutora principal:\n" + project.main_entity)
                st.write("---")
                st.write(f"##### Entidades participantes adicionales:\n" + "\n".join(f"- {s}" for s in project.entities))
                st.write("---")
                st.write(f"##### Entidades que financian:\n" + "\n".join(f"- {s}" for s in project.funding))

            st.write("---")
            st.download_button("🔽 Descargar información", data="")