# Identificadores para reglas (qué usar y qué evitar)

Referencia única para no mezclar criterios “de juego” con recursos gráficos (iconos, thumbnails) de la API.

## Resumen

| Querés filtrar por… | Usá en reglas / perfil | Fuente en la API | **No** uses para reglas |
|---------------------|-------------------------|------------------|-------------------------|
| Stat (ataque, defensa, etc.) | `stat_key_gte` / `stat_key_suffix_gte` con nombre legible; claves internas = `normalize_stat_label(statName)` | Campo **`statName`** (+ `statValue`) en `stats` y en el listado | **`iconPath`**, basename `.png`, URLs |
| Tipo de ítem (arma, accesorio, piedra…) | `item_any`: `item_type`, `item_type_prefix` | Campo **`itemType`** (ej. `2_1`, `8_5`) en `equipItem` | **`itemPath`** (URL de icono), nombres de archivo de imagen |
| Rareza / mejora | `min_rarity`, `min_enhancement` | **`grade`** (mapeado a `legendary`/`epic`/…) y **`enhance`** | Icono del ítem |
| Piedra mágica por categoría | `stones_types_min_tier`, `stone_min_tier` | **`itemType`** de piedras `8_*` como `stone_type_id` | Color/icono de la piedra en la URL |
| Mascota / orbe | `pets_*`: `pet_ids` | **`itemIdx`** (y tipo `23_*` / `28_*`) como `pet_id` | Icono en `itemPath` |
| Clase | `class_is` | Clase numérica → slug (`sorcerer`, …) en `mir4_api.constants` | Avatar o imagen |
| Power | `power_gte` / `power_lte` | `powerScore` | — |
| Skills | `skill_min`, `all_skills_min` | IDs propios cuando exista endpoint; niveles **1–12** (MIR4) en reglas | — |

## Detalle: stats

- La API incluye **`iconPath`** por stat; el código **no** lo usa para poblar `CharacterProfile.stats`.
- Las claves son el texto **`statName`** normalizado (minúsculas, sin acentos). En YAML podés escribir `"Ataque Mágico"`, `"Defensa Física"`, etc.

## Detalle: ítems equipados

- **`itemType`** es un código de juego (`"2_1"`, `"4_2"`, …), no una ruta de imagen.
- **`itemPath`** y **`itemName`** son UI/recurso; el motor actual filtra por `item_type`, `slot`, rareza y mejora, no por nombre visible ni por URL.

## Tests y mocks

En tests puede aparecer `iconPath` en JSON de ejemplo porque la API real lo envía; se ignora al construir el perfil. No implica que las reglas deban basarse en eso.
