# Pizarra sísmica mundial

Tablero interactivo con el catálogo sísmico del USGS (321 sismos, 31 oct – 7 nov 2026).
Tres vistas: mapa por magnitud y profundidad, zonas con K-Means y un análisis del sesgo de detección.

**Hallazgo:** de los sismos menores a magnitud 4, la gran mayoría está en EE. UU. y sus territorios.
No significa que tiemble más ahí. Según el USGS, dentro de EE. UU. las redes locales reportan sismos pequeños; fuera, solo se ubican bien los de ~M4.5 en adelante. El catálogo muestra dónde se mide, no solo dónde tiembla.

## Cómo correrlo
```
pip install -r requirements.txt
pip install pyshp   # solo para make_visuals.py
streamlit run app.py
```

## Archivos
- `app.py`: la app (Streamlit + Plotly + scikit-learn)
- `sismos.csv`: datos descargados del catálogo del USGS
- `make_visuals.py`: genera la portada y la animación para el post

## Método
1. Se filtran solo los eventos tipo `earthquake` (se descarta 1 explosión de cantera) y duplicados.
2. Se clasifica cada sismo como "EE. UU. y territorios" o "Resto del mundo" según el texto del campo `place`.
3. K-Means agrupa por posición en la esfera y profundidad (así la línea de fecha no parte una zona en dos).

## Límites
- Solo una semana de datos: es una muestra, no una conclusión sobre el comportamiento sísmico a largo plazo.
- La clasificación por país sale de texto, no de un mapa de fronteras; puede tener errores en bordes (por ejemplo, Baja California).
- Análisis descriptivo: no predice sismos.

Fuente de datos: USGS Earthquake Catalog (earthquake.usgs.gov). Contornos de países: Natural Earth (dominio público), en `mapa/`.
Explicación de umbrales: USGS FAQ sobre qué sismos aparecen en la lista de últimos sismos.
