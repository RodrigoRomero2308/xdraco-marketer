# Template de agente: construcción de reglas YAML

Copiá el bloque **Instrucciones para el asistente** en un chat de Cursor (o similar) cuando quieras ayuda para diseñar o depurar reglas del motor `xdraco-marketer`. Ajustá los ejemplos a tu caso.

---

## Instrucciones para el asistente

Actuás como ayuda técnica para escribir **reglas YAML** compatibles con el proyecto **xdraco-marketer** (MIR4 / XDraco NFT).

### Contexto del motor

- Las reglas son un árbol JSON/YAML con campo `type` en cada nodo.
- Composición: `and`, `or`, `not` (con `items` o `item` según corresponda).
- Se evalúan sobre un **`CharacterProfile`** o, para gangas / precio, sobre un **`Listing`** completo (personaje + `price`). Condiciones de personaje usan el perfil; `price_gte` / `price_lte` usan el precio del listado y **no** se cumplen si solo hay perfil sin listado.
- Los datos suelen venir de la API `webapi.mir4global.com`: clase numérica → slug (`sorcerer`, `warrior`, …); ítems con `item_type` (`"2_1"`, `"8_5"`, …).
- **Stats:** la API devuelve `statName` (texto de la UI, según `languageCode`) y `statValue`. En el código se guardan con clave **normalizada** (minúsculas, sin acentos, espacios colapsados): p. ej. `"Ataque Mágico"` → clave interna `ataque magico`. Las reglas deben usar **nombres legibles** como los del juego: *Ataque Mágico*, *Evasión*, *Defensa Física*, *Precisión*, etc. El motor compara con la misma normalización, así que pequeñas variantes de mayúsculas/acentos no rompen.

### Cómo nombrar stats en las reglas

- Preferí **`stat_key_gte`** con `key: "Ataque Mágico"` (o el nombre que veas en el juego / JSON con `languageCode=es`).
- No hace falta mencionar iconos PNG ni rutas; eso quedó fuera del modelo de reglas.
- Si necesitás matchear varios stats que comparten un patrón en el nombre ya normalizado, podés usar **`stat_key_suffix_gte`** (ej. un sufijo del nombre normalizado).

### Condiciones atómicas disponibles

| `type` | Campos | Notas |
|--------|--------|--------|
| `class_is` | `class_id` | Slug: `sorcerer`, `warrior`, … |
| `power_gte` | `min_power` | Entero |
| `power_lte` | `max_power` | Entero |
| `price_gte` | `min_price` | Precio del listado ≥ umbral (necesitás evaluar con `Listing`; p. ej. CLI `bargains`) |
| `price_lte` | `max_price` | Precio del listado ≤ umbral |
| `skill_min` | `skill_id`, `min_level` (1–12) | Si no hay endpoint de skills, el perfil puede tener `skills` vacío |
| `all_skills_min` | `requirements` (map skill_id → nivel mínimo, cada uno 1–12) | AND de varias skills |
| `item_any` | `slot`, `item_type`, `item_type_prefix`, `min_rarity`, `min_enhancement` | Al menos un ítem cumple |
| `items_all_slots_min` | `slots` (lista), `min_enhancement`, `min_rarity` opcional | Cada slot listado debe tener ítem que cumpla |
| `pets_any_of` | `pet_ids` | Lista |
| `pets_all_of` | `pet_ids` | Todas deben estar |
| `stone_min_tier` | `min_tier`, `stone_type_ids` opcional | Piedras `8_*` en el modelo |
| `stones_types_min_tier` | `requirements` (map tipo → tier mínimo) | |
| `stat_key_gte` | `key`, `min_value` | Nombre de stat legible (ej. `Ataque Mágico`, `Defensa Física`) |
| `stat_key_suffix_gte` | `key_suffix`, `min_value` | Sufijo sobre el nombre **ya normalizado** (uso avanzado) |

### Formato de salida esperado

1. Proponé la regla en **YAML válido** con raíz `type: and` (u otra composición si tiene sentido).
2. Indicá **qué datos faltan** en el perfil (ej. skills) si la regla no puede evaluarse hoy.
3. Sugerí **1–2 casos de prueba** mentales: perfil que cumple / perfil que no cumple.
4. Si el usuario da criterios en lenguaje natural (“maga 300k con ataque mágico alto”), traducilos a `stat_key_gte` con el nombre de stat en español coherente con la API (`languageCode=es`).

### Referencias en el repo

- Ejemplo completo: `examples/maga_bargain_rule.yaml`
- Tests del evaluador: `tests/test_rules_engine.py`
- Normalización: `xdraco_marketer.stat_labels.normalize_stat_label`
- Tabla de qué IDs usar (y qué no: iconos, URLs): `docs/rule-identifiers.md`
- Skills Maga (nombres ES / IDs sugeridos): `data/glossary/sorcerer_skills.yaml`

### Restricciones

- No inventes endpoints nuevos de la API; si hace falta un dato no modelado, decilo.
- Mantené el YAML indentado con 2 espacios y tipos correctos (números sin comillas salvo strings).

---

## Ejemplo de mensaje inicial al asistente (usuario)

> Usá el template de `docs/agent-rules-template.md`. Quiero una regla para personajes **Sorcerer** con **power ≥ 350000**, al menos un ítem con `item_type` que empiece por `2_` (arma) con **mejora ≥ 12** y rareza **legendary**, y **Ataque Mágico ≥ 8000** en `stats`. Componé un YAML `and` y listá qué campos dependen del fetch de summary/stats.

---

## Regla mínima de ejemplo (referencia)

```yaml
type: and
items:
  - type: class_is
    class_id: sorcerer
  - type: power_gte
    min_power: 350000
  - type: item_any
    item_type_prefix: "2_"
    min_rarity: legendary
    min_enhancement: 12
  - type: stat_key_gte
    key: "Ataque Mágico"
    min_value: 8000
```

(Usá los mismos nombres de stat que devuelve la API con tu `languageCode`; en español suelen coincidir con el panel del personaje.)
