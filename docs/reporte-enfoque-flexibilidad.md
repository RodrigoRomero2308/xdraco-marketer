# Informe: enfoque del repositorio y flexibilidad para nuevas fórmulas y criterios

## Resumen ejecutivo

El proyecto **xdraco-marketer** separa bien las capas (API MIR4 → `CharacterProfile` → motor de reglas YAML/JSON → `BargainDetector`), usa **Pydantic con discriminador `type`** para un AST de reglas serializable y documenta los puntos de extensión en `docs/architecture.md`. Eso es un buen fundamento para reglas declarativas y pruebas sin red.

Para **añadir con frecuencia nuevos criterios o “fórmulas”** (predicados compuestos, comparaciones genéricas, métricas de valor distintas a la mediana, etc.), el cuello de botella principal es **la extensión manual en varios sitios**: cada condición nueva implica tocar `rules/ast.py`, un `if isinstance` largo en `rules/evaluate.py` y tests; no hay registro plug-in, validación cruzada automática AST↔evaluador ni capa de **expresiones** reutilizables (por ejemplo comparadores `<`, `between`, sumas de stats). La lógica de **ganga** está acoplada a una única fórmula (precio vs mediana del cohorte con umbral).

Las mejoras con mayor impacto serían: **(1)** un patrón de registro o *visitor* / `singledispatch` para que cada tipo de regla lleve su evaluación en un solo módulo y sea más difícil olvidar el `matches`; **(2)** abstraer comparaciones numéricas y umbrales para no multiplicar tipos `*_gte` / `*_lte`; **(3)** orden o tabla de rarezas si “mínima rareza” debe ser semántica de juego, no igualdad de string; **(4)** exponer **JSON Schema** desde Pydantic para editar YAML con autocompletado; **(5)** versionado opcional del esquema de reglas; **(6)** tests de contrato que aseguren cobertura evaluator ↔ AST; **(7)** desacoplar estrategias de “barato” en `BargainDetector` vía interfaz o cadena de estrategias.

---

## Detalle: lo observado en el código

### 1. Arquitectura general (fortalezas)

- **Flujo claro**: listado → `Listing` (personaje + precio) → `matches(Listing, rule)` en gangas (o solo `CharacterProfile` en tests de perfil) → cohorte (`bargains/detector.py`). `rules.evaluate` no depende de HTTP, lo que facilita tests unitarios (`tests/test_rules_engine.py`).
- **Reglas como datos**: `RuleExpr` es un union discriminado (`and` / `or` / `not` + hojas atómicas), cargable desde YAML (`rules/loader.py`). Los usuarios pueden versionar reglas en archivos sin recompilar.
- **Documentación de extensión**: `docs/architecture.md` ya lista el procedimiento “nueva condición” y “otra métrica de barato”.

### 2. Extensión de criterios: acoplamiento AST + evaluador

- En `rules/ast.py` cada condición es una subclase de `BaseModel` con `type: Literal[...]` y se agrega al union `_RuleLeaf` / `RuleExpr`.
- En `rules/evaluate.py`, `matches()` implementa **toda** la semántica con una cadena de `isinstance` sobre cada tipo.

**Implicación**: cada criterio nuevo obliga a **mínimo tres cambios coordinados** (modelo, evaluador, tests). No hay mecanismo que falle en compile-time si falta un brazo del evaluador; solo `TypeError` en runtime (“Tipo de regla no soportado”) cuando llega un tipo no contemplado.

**Mejora sugerida**: *registry* `{discriminator: callable}` o `functools.singledispatch` sobre una clase envoltorio, o patrón Visitor, de modo que cada tipo de regla viva en un archivo pequeño con `def eval_X(profile, node) -> bool`. Opcional: test que recorra los `Literal` esperados y compruebe que hay handler registrado.

### 3. Duplicación de patrones de comparación

- Hay tipos separados para rangos de power (`power_gte`, `power_lte`) y solo `gte` para stats por clave/sufijo (`stat_key_gte`, `stat_key_suffix_gte`).
- Cualquier nueva dimensión numérica similar obligará a duplicar el patrón o a añadir más literales al discriminador.

**Mejora sugerida**: un nodo genérico del estilo `numeric_compare { target: power | stat_key | …, op: gte|lte|eq, value }` validado con Pydantic, o al menos convención de un solo tipo `Threshold` parametrizado por “ruta” en el perfil (con cuidado de no perder tipado ni legibilidad del YAML).

### 4. Semántica de rareza y filtros de ítems

- `_rarity_ok` compara **igualdad** normalizada de strings, no un orden (p. ej. legendary > epic). Si el juego o los datos usan varias convenciones, “min_rarity” puede ser ambiguo o exigir valores exactos.

**Mejora sugerida**: mapa ordinal configurable (config o tabla en código), o rareza como entero/enum externo al cargar el perfil.

- `ItemAny` combina varios filtros opcionales en un solo nodo; es potente pero **menos composable** que encadenar `and` de subcondiciones más pequeñas por ítem (si existieran).

### 5. Ausencia de “fórmulas” sobre stats o campos derivados

- Las reglas actuales son **predicados fijos** sobre campos del modelo. No hay expresiones tipo `stat.A + stat.B >= N`, ni variables intermedias, ni acceso indexado genérico.
- `CharacterProfile` no expone propiedades calculadas reutilizables por el motor; todo va directo a `matches`.

**Mejora sugerida**: capa opcional de **features** (funciones puras `Profile -> float | bool`) registradas por nombre y referenciables desde reglas; o un mini-DSL acotado (solo operaciones seguras) si el riesgo de evaluar expresiones arbitrarias es aceptable con sandboxing.

### 6. Carga y ergonomía de YAML

- `load_rule_from_yaml_text` usa `yaml.safe_load` + validación Pydantic: correcto y seguro.
- No se observa generación de **JSON Schema** para editores/CI que validen reglas sin ejecutar Python.

**Mejora sugerida**: `TypeAdapter(RuleExpr).json_schema()` exportado a `docs/schemas/rule-expr.schema.json` o similar, más ejemplos en `examples/` referenciados desde el esquema.

### 7. Versionado del lenguaje de reglas

- No hay campo `version` en la raíz de la regla. Si en el futuro se renombra un `type` o se cambia el significado de un campo, los YAML antiguos pueden romperse sin migración explícita.

**Mejora sugerida**: `schema_version: 1` en la raíz y migradores ligeros en el loader, o reglas bajo namespaces por versión.

### 8. Motor de gangas y “fórmulas” de precio

- `BargainDetector._find_in_group` implementa una única lógica: mediana de precios de pares, umbral `median_ratio_max`, tamaño mínimo de cohorte.
- Extender a percentiles, z-score, o comparación contra un precio “justo” externo implica **modificar la clase** o bifurcar métodos.

**Mejora sugerida**: interfaz `PricingStrategy` / `BargainScorer` inyectable con implementaciones por defecto (mediana, p90, etc.) y tests por estrategia.

### 9. Calidad y mantenimiento de tests

- `tests/test_rules_engine.py` cubre ramas principales del evaluador y el loader YAML; incluye test de tipo no soportado.
- Falta un test **parametrizado por tipo de nodo** que garantice que cada miembro publicado del union tiene al menos un caso (o el registro del punto 2).

### 10. Resumen de prioridades sugeridas

| Prioridad | Mejora | Motivo |
|-----------|--------|--------|
| Alta | Registro / dispatch por tipo de regla | Reduce errores al añadir criterios; escala mejor |
| Alta | Comparadores y umbrales genéricos donde aplique | Menos tipos duplicados en el AST |
| Media | JSON Schema + más ejemplos | Facilita a usuarios y CI |
| Media | Rareza ordinal configurable | Alinea “min_rarity” con el juego |
| Media | Estrategias plug-in para gangas | Nuevas “fórmulas” de barato sin tocar el núcleo |
| Baja | Versionado de esquema de reglas | Evolución sin romper YAML legacy |
| Baja | Capa de features / mini-DSL para stats | Máxima flexibilidad; mayor coste de diseño y seguridad |

---

*Documento generado como revisión de código del enfoque actual (`src/xdraco_marketer/rules/`, `bargains/`, `models/`, `docs/architecture.md`).*
