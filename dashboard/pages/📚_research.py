from typing import Dict
import streamlit as st
import pandas as pd
import altair

from models import JournalPaper, Person, Journal


st.set_page_config(
    page_title="MatCom Dashboard - Investigación", page_icon="📚", layout="wide"
)

year = st.sidebar.selectbox("Año", [2020, 2021, 2022], index=2)

people = Person.all()
people.sort(key=lambda p: p.name)

journals = Journal.all()
journals.sort(key=lambda j: j.title)

papers = [p for p in JournalPaper.all() if p.year == year]
papers.sort(key=lambda p: p.title)

st.write(f"#### Artículos en Journal - {year} ({len(papers)})")


with st.expander("⚗️ Nueva entrada / Editar"):
    if (
        st.radio("Tipo de entrada", ["⭐ Nueva entrada", "📝 Editar"], horizontal=True, label_visibility="collapsed")
        == "📝 Editar"
    ):
        paper = st.selectbox(
            "Seleccione un artículo a modificar",
            papers,
            format_func=lambda p: f"{p.title} - {p.authors[0]}",
        )
    else:
        paper = JournalPaper(title="", authors=[], journal=journals[0])

    paper.title = st.text_input("Título", key="paper_title", value=paper.title)
    paper.authors = st.multiselect("Autores", key="paper_authors", options=people, default=paper.authors)

    if paper.authors:
        paper.corresponding_author = st.selectbox("Autor por correspondencia", options=paper.authors, index=paper.authors.index(paper.corresponding_author) if paper.corresponding_author else 0)

    paper.journal = st.selectbox("Journal", options=journals + ["➕ Nueva entrada"], index=journals.index(paper.journal))

    if paper.journal == "➕ Nueva entrada":
        journal_title = st.text_input("Título del Journal", key="journal_title")
        journal_publisher = st.text_input("Editorial", key="journal_publisher")
        journal_issn = st.text_input("ISSN", key="journal_issn")

        paper.journal = Journal(title=journal_title, publisher=journal_publisher, issn=journal_issn)

    paper.issue = st.number_input("Número", key="paper_issue", min_value=1, value=paper.issue)
    paper.year = st.number_input("Número", key="paper_year", min_value=2020, value=paper.year)

    if st.button("💾 Guardar cambios"):
        paper.journal.save()
        paper.save()
        st.success("Entrada salvada con éxito.")


with st.expander("📚 Listado"):
    data = []

    for paper in papers:
        text = [f"_{paper.title}_."]

        for author in paper.authors:
            fmt = author.name

            if author.orcid:
                fmt = f"[{fmt}](https://orcid.org/{author.orcid})"

            if author.institution == "Universidad de La Habana":
                fmt = f"**{fmt}**"

            text.append(fmt.format(author.name) + ", ")

        text.append(f"En _{paper.journal.title}_, {paper.journal.publisher}. ISSN: {paper.journal.issn}.")
        text.append(f"Número {paper.issue}, {paper.year}.")
        st.write(" ".join(text))

st.stop()


@st.experimental_memo
def load_data() -> pd.DataFrame:
    return dict(
        Publicaciones=pd.read_csv(
            "/src/data/publications.csv",
        ),
        Tesis=pd.read_csv(
            "/src/data/publications.csv",
        ),
    )


data = load_data()


@st.experimental_memo
def convert_to_csv(sheet: str):
    return data[sheet].to_csv().encode("utf8")


st.markdown(f"### Publicaciones: {len(data['Publicaciones'])}")

pub_data = data["Publicaciones"]
pub_data_by_type = (
    pub_data.groupby("Tipo de publicación").agg({"Título": "count"}).to_dict()["Título"]
)

cols = st.columns(len(pub_data_by_type))

for (label, count), col in zip(pub_data_by_type.items(), cols):
    with col:
        st.metric(label=label, value=count)

sheet = "Publicaciones"

with st.expander(f"Ver datos: {sheet}", False):
    st.dataframe(data[sheet])

    st.download_button(
        "Descargar",
        data=convert_to_csv(sheet),
        file_name=f"{sheet}.csv",
        mime="text/csv",
    )

agg_method = lambda s: f"year({s})"

# with st.sidebar:
#     aggregation = st.selectbox("Modo de agregación", ["Año", "Mes/Año", "Ninguno"])

#     if aggregation == "Año":
#         agg_method = lambda s: f"year({s})"
#     if aggregation == "Mes/Año":
#         agg_method = lambda s: f"yearmonth({s})"
#     if aggregation == "Ninguno":
#         agg_method = lambda s: f"{s}"


pub_chart_dates = (
    altair.Chart(pub_data)
    .mark_bar()
    .encode(
        column=altair.Column(
            agg_method("Fecha de publicación"), type="nominal", title="Período"
        ),
        y=altair.Y("count(Título)", title="Cantidad"),
        color=altair.Color("Tipo de publicación"),
        x=altair.X("Tipo de publicación", title=None, axis=None),
        tooltip=[
            altair.Tooltip("count(Título)", title="Total"),
            altair.Tooltip("Tipo de publicación", title="Tipo"),
            altair.Tooltip(agg_method("Fecha de publicación"), title="Fecha"),
        ],
    )
)

pub_chart_types = (
    altair.Chart(pub_data, title="Publicaciones por tipo")
    .mark_arc()
    .encode(
        theta="count(Título)",
        tooltip=[
            altair.Tooltip("count(Título)", title="Total"),
            altair.Tooltip("Tipo de publicación", title="Tipo"),
        ],
        color="Tipo de publicación",
    )
)

st.altair_chart(pub_chart_dates | pub_chart_types, use_container_width=False)

venues = (
    pub_data[
        pub_data["Tipo de publicación"].isin(
            [
                "Artículo publicado en journal",
                "Artículo publicado en proceeding de congreso",
                "Presentación en congreso (sin artículo)",
            ]
        )
    ]
    .groupby(["Tipo de publicación", "Nombre de la Publicación / Evento"])
    .count()
    .reset_index()
)

st.altair_chart(
    altair.Chart(venues, width=200, title="Top de publicaciones")
    .mark_bar()
    .encode(
        x=altair.X("Título", title="Publicaciones"),
        y=altair.Y("Nombre de la Publicación / Evento"),
        column="Tipo de publicación",
        color="Tipo de publicación",
        tooltip=[
            altair.Tooltip("Nombre de la Publicación / Evento", title="Nombre"),
            altair.Tooltip("Tipo de publicación", title="Tipo"),
            altair.Tooltip("count(Título)", title="Totalr"),
        ],
    )
)
