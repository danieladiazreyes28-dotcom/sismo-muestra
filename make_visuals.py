"""Genera la portada (PNG) y la animación (GIF + MP4) para el post de LinkedIn."""
import subprocess
import sys

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile  # pyshp

sys.path.insert(0, ".")
BG, TXT, SUB = "#0b1d26", "#f3ead7", "#9db4bd"
TEAL, GOLD, GRID = "#3fb8af", "#f2b134", "#1c3744"

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

# contornos de países: Natural Earth (dominio público)
PAISES = [shapefile.Reader("mapa/naturalearth_lowres").shapes()[i] for i in range(len(shapefile.Reader("mapa/naturalearth_lowres")))]


def contornos(ax):
    for shp in PAISES:
        partes = list(shp.parts) + [len(shp.points)]
        for a, b in zip(partes[:-1], partes[1:]):
            xs, ys = zip(*shp.points[a:b])
            ax.fill(xs, ys, facecolor="#11303d", edgecolor="#244a5a", lw=0.5, zorder=1)


df = pd.read_csv("sismos.csv", parse_dates=["time"])
df = df[df["type"] == "earthquake"].drop_duplicates("id").sort_values("time").copy()
ultimo = df["place"].str.extract(r",\s*([^,]+)$")[0].fillna(df["place"])
df["eeuu"] = ultimo.isin(ESTADOS)

# cifras que se citan en el post (todas salen de aquí)
n = len(df)
peq = df[df["mag"] < 4]
stats = {
    "n": n,
    "n_menor4": len(peq),
    "n_menor4_eeuu": int(peq["eeuu"].sum()),
    "pct_menor4_en_eeuu": peq["eeuu"].mean(),
    "pct_eeuu_menor4": (df[df["eeuu"]]["mag"] < 4).mean(),
    "pct_resto_menor4": (df[~df["eeuu"]]["mag"] < 4).mean(),
    "mediana_eeuu": df[df["eeuu"]]["mag"].median(),
    "mediana_resto": df[~df["eeuu"]]["mag"].median(),
}
print(stats)


def dibujar_mapa(ax, datos, destacar=None):
    ax.set_facecolor(BG)
    contornos(ax)
    for grupo, color in ((False, TEAL), (True, GOLD)):
        d = datos[datos["eeuu"] == grupo]
        ax.scatter(d["longitude"], d["latitude"], s=(d["mag"] - 1.5) ** 2 * 7, c=color,
                   alpha=0.75, edgecolors="none", zorder=2)
    if destacar is not None and len(destacar):
        ax.scatter(destacar["longitude"], destacar["latitude"], s=(destacar["mag"] - 1.5) ** 2 * 18,
                   facecolors="none", edgecolors=TXT, lw=1.2, zorder=3)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-65, 85)
    ax.set_aspect("equal")
    ax.axis("off")


# ---------- portada ----------
fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BG)
ax = fig.add_axes([0.03, 0.12, 0.64, 0.72])
dibujar_mapa(ax, df)
fig.text(0.04, 0.92, "Una semana de sismos en el mundo", color=TXT, fontsize=30, fontweight="bold",
         va="center")
fig.text(0.04, 0.865, f"{n} sismos del catálogo del USGS · 31 oct – 7 nov 2026 (UTC) · tamaño = magnitud",
         color=SUB, fontsize=13, va="center")
fig.text(0.72, 0.70, f"{stats['pct_menor4_en_eeuu']:.0%}", color=GOLD, fontsize=88, fontweight="bold",
         va="center")
fig.text(0.72, 0.56, f"de los sismos menores a magnitud 4\nestán en EE. UU. y sus territorios\n"
         f"({stats['n_menor4_eeuu']} de {stats['n_menor4']})", color=TXT, fontsize=17, va="top",
         linespacing=1.5)
fig.text(0.72, 0.36, "¿Allá tiembla más? No necesariamente.\nDentro de EE. UU. las redes locales reportan\n"
         "sismos pequeños; fuera, el USGS solo ubica\nbien los de ~M4.5 en adelante.", color=SUB, fontsize=14,
         va="top", linespacing=1.6)
fig.text(0.72, 0.12, "●", color=GOLD, fontsize=14, va="center")
fig.text(0.74, 0.12, "EE. UU. y territorios", color=TXT, fontsize=13, va="center")
fig.text(0.72, 0.085, "●", color=TEAL, fontsize=14, va="center")
fig.text(0.74, 0.085, "Resto del mundo", color=TXT, fontsize=13, va="center")
fig.text(0.04, 0.04, "Fuente: USGS Earthquake Catalog · Análisis y visualización: Dani · Python (pandas, scikit-learn)",
         color=SUB, fontsize=11, va="center")
fig.savefig("portada.png", facecolor=BG)
plt.close(fig)

# ---------- animación ----------
inicio, fin = df["time"].min(), df["time"].max()
cortes = pd.date_range(inicio.floor("6h"), fin.ceil("6h"), freq="6h")
cuadros = []
for i, t in enumerate(cortes[1:], start=1):
    previo = cortes[i - 1]
    visto = df[df["time"] <= t]
    nuevo = df[(df["time"] > previo) & (df["time"] <= t)]
    fig = plt.figure(figsize=(10, 5.625), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.02, 0.06, 0.96, 0.74])
    dibujar_mapa(ax, visto, destacar=nuevo)
    fig.text(0.03, 0.92, "Una semana de sismos", color=TXT, fontsize=22, fontweight="bold", va="center")
    fig.text(0.03, 0.85, f"{t:%d %b %H:%M} UTC", color=SUB, fontsize=12, va="center")
    fig.text(0.97, 0.92, f"{len(visto)}", color=GOLD, fontsize=30, fontweight="bold", ha="right", va="center")
    fig.text(0.97, 0.85, "sismos acumulados", color=SUB, fontsize=11, ha="right", va="center")
    fig.canvas.draw()
    cuadros.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
    plt.close(fig)

# cuadros finales con el hallazgo
fig = plt.figure(figsize=(10, 5.625), dpi=100, facecolor=BG)
ax = fig.add_axes([0.02, 0.06, 0.96, 0.74])
dibujar_mapa(ax, df)
fig.text(0.03, 0.92, "Una semana de sismos", color=TXT, fontsize=22, fontweight="bold", va="center")
fig.text(0.03, 0.85, f"{stats['pct_menor4_en_eeuu']:.0%} de los sismos < M4 están en EE. UU.  ·  ¿más temblores o mejor medición?",
         color=GOLD, fontsize=13, va="center")
fig.text(0.97, 0.92, f"{n}", color=GOLD, fontsize=30, fontweight="bold", ha="right", va="center")
fig.text(0.97, 0.85, "sismos", color=SUB, fontsize=11, ha="right", va="center")
fig.canvas.draw()
final = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
plt.close(fig)
cuadros += [final] * 14

imageio.mimsave("sismos.gif", cuadros, duration=0.12, loop=0)
imageio.mimsave("sismos.mp4", cuadros, fps=8, codec="libx264", macro_block_size=2,
                ffmpeg_params=["-pix_fmt", "yuv420p"])
print("cuadros:", len(cuadros))
