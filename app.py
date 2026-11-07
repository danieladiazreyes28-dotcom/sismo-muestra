import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans

st.set_page_config(page_title="Pizarra sísmica", layout="wide")

ESTADOS = set(
    "Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia "
    "Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts "
    "Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada Ohio Oklahoma Oregon "
    "Pennsylvania Tennessee Texas Utah Vermont Virginia Washington Wyoming Wisconsin".split()
) | {"New Mexico", "New York", "New Jersey", "New Hampshire", "North Carolina", "South Carolina",
     "North Dakota", "South Dakota", "West Virginia", "Rhode Island", "Puerto Rico",
     "U.S. Virgin Islands", "Northern Mariana Islands", "Guam", "American Samoa",
     "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
     "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "OH", "OK",
     "OR", "PA", "TN", "TX", "UT", "VT", "VA", "WA", "WY", "NM", "NY", "NJ", "NH", "NC", "SC",
     "ND", "SD", "WV", "WI", "RI", "PR"}


@st.cache_data
def cargar(ruta="sismos.csv"):
    df = pd.read_csv(ruta, parse_dates=["time"])
    df = df[df["type"] == "earthquake"].dropna(subset=["latitude", "longitude", "depth", "mag"])
    df = df.drop_duplicates("id").copy()
    ultimo = df["place"].str.extract(r",\s*([^,]+)$")[0].fillna(df["place"])
    df["grupo"] = np.where(ultimo.isin(ESTADOS), "EE. UU. y territorios", "Resto del mundo")
    return df


def zonas(df, k):
    lat, lon = np.radians(df["latitude"]), np.radians(df["longitude"])
    # coordenadas en la esfera: evita que la línea de fecha parta una zona en dos
    X = np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat), df["depth"] / 700]
    return KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X).astype(str)


df = cargar()

st.title("Pizarra sísmica mundial")
st.caption(
    f"{len(df)} sismos del catálogo del USGS · {df['time'].min():%d %b} – {df['time'].max():%d %b %Y} (UTC)"
)

mag_min = st.sidebar.slider("Magnitud mínima", 2.5, 6.0, 2.5, 0.1)
k = st.sidebar.slider("Número de zonas (K-Means)", 2, 8, 5)
f = df[df["mag"] >= mag_min].copy()
if len(f) < k:
    st.warning("Hay muy pocos sismos con ese filtro. Baja la magnitud mínima.")
    st.stop()
f["zona"] = zonas(f, k)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sismos", f"{len(f):,}")
c2.metric("Magnitud máxima", f"{f['mag'].max():.1f}")
c3.metric("Profundidad mediana", f"{f['depth'].median():.0f} km")
c4.metric("Superficiales (<70 km)", f"{(f['depth'] < 70).mean():.0%}")

t1, t2, t3 = st.tabs(["Mapa", "Zonas (K-Means)", "¿Dónde se mide mejor?"])

with t1:
    fig = px.scatter_geo(f, lat="latitude", lon="longitude", size="mag", color="depth",
                         hover_name="place", projection="natural earth",
                         color_continuous_scale="Turbo_r", labels={"depth": "Profundidad (km)"})
    st.plotly_chart(fig, width="stretch")

with t2:
    fig = px.scatter_geo(f, lat="latitude", lon="longitude", color="zona", size="mag",
                         hover_name="place", projection="natural earth")
    st.plotly_chart(fig, width="stretch")
    resumen = (f.groupby("zona")
                 .agg(sismos=("id", "count"), mag_mediana=("mag", "median"),
                      profundidad_mediana_km=("depth", "median"),
                      lugar_frecuente=("place", lambda s: s.str.extract(r",\s*([^,]+)$")[0].mode().iloc[0]))
                 .round(1))
    st.dataframe(resumen, width="stretch")
    st.caption("Las zonas son agrupaciones por posición y profundidad. Describen el catálogo, no predicen sismos.")

with t3:
    g = f.groupby("grupo")["mag"].agg(sismos="count", mediana="median").round(2)
    pct = f.groupby("grupo")["mag"].apply(lambda s: (s < 4).mean())
    a, b = st.columns(2)
    for col, nombre in zip((a, b), ["EE. UU. y territorios", "Resto del mundo"]):
        if nombre in g.index:
            col.metric(nombre, f"{pct[nombre]:.0%} menores a M4", f"mediana M{g.loc[nombre, 'mediana']}")
    fig = px.histogram(f, x="mag", color="grupo", nbins=30, barmode="overlay", opacity=0.7,
                       labels={"mag": "Magnitud"})
    st.plotly_chart(fig, width="stretch")
    st.info(
        "Casi todos los sismos pequeños del catálogo están en EE. UU. y sus territorios. "
        "Según el USGS, dentro de EE. UU. las redes locales reportan sismos pequeños; "
        "fuera, solo se ubican bien los de ~M4.5 en adelante, y muchas redes regionales no comparten sus datos. "
        "El catálogo muestra dónde se mide, no solo dónde tiembla."
    )

st.caption("Fuente: USGS Earthquake Catalog. Análisis descriptivo; el tablero no predice sismos.")
