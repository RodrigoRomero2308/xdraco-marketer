# Pendientes y roadmap

Lista viva de trabajo futuro; prioriza según lo que uses día a día.

## Datos y API

- [ ] **Skills en perfil:** localizar endpoint o campo con skills + nivel para rellenar `CharacterProfile.skills` y que las reglas `skill_*` evalúen datos reales del listado. (`GET /nft/character/skills` → 60001 sin sesión.) **Glosario de nombres (ES) por clase:** YAML en `data/glossary/` + generación con `scripts/scrape_skill_books_by_class.py` (inferido desde libros en inventario; no sustituye niveles en API).
- [ ] **Inventario (`/nft/character/inven`):** opcional — normalizar a modelo si querés filtros por recursos (oro, materiales, etc.).
- [ ] **Concurrencia:** `async` + límite de paralelismo para `fetch_listing` en lotes (sin martillar la API).
- [ ] **Reintentos:** backoff ante 429/5xx y cabeceras configurables si el servidor exige algo más que el flujo actual.

## Producto (alertas y persistencia)

- [ ] **Estado incremental:** guardar último `seq` / timestamp visto y solo procesar listados nuevos.
- [ ] **Histórico de precios:** snapshots locales (SQLite/JSON) para comparar en el tiempo, no solo cohorte actual.
- [ ] **Notificaciones:** Discord, Telegram o email cuando `BargainDetector` encuentre candidatos nuevos.
- [ ] **Otras métricas de “barato”:** percentil, ratio vs mínimo reciente, precio por punto de power, etc.

## Reglas y DX

- [ ] **Mapeo de `item_type`:** catálogo de códigos API (`2_1`, `8_5`, `23_*`, …) a categoría legible (arma, sub-arma, piedra, orbe, …) para docs, autocompletado o alias en reglas YAML.
- [ ] **Documentar todas las condiciones** del motor en un solo sitio (hoy hay tabla en [docs/rule-identifiers.md](docs/rule-identifiers.md) + [docs/agent-rules-template.md](docs/agent-rules-template.md); unificar o enlazar sin duplicar).
- [ ] **Validar reglas YAML** con mensajes más explícitos por campo (además de la validación Pydantic ya aplicada al cargar, p. ej. `skill_min` / `all_skills_min` con niveles 1–12).
- [ ] **Ejemplos YAML adicionales:** por clase, solo stats, solo equipo (ya hay `examples/skill_rules_*.yaml` con AND/OR/NOT + skills y `maga_bargain_rule.yaml`).

## Calidad

- [ ] **Tests de integración** opcionales contra la API real (marcados `slow` o desactivados por defecto).
- [ ] **CI:** GitHub Actions con `pytest` + `ruff` en push/PR.

## Documentación

- [ ] Mantener `README.md` al día cuando cambien comandos o flujos.
- [ ] Volcar capturas nuevas de la API en `example-calls/` si cambian contratos.

---

Si cerrás un ítem, marcá el checkbox o borrá la línea para no acumular ruido.

### Pasar estos TODOs a issues de GitHub

GitHub **no** lee `TODO.md` solo. Podés crear un issue por cada ítem con la CLI oficial:

1. Instalá [GitHub CLI](https://cli.github.com/) y ejecutá `gh auth login` en el repo.
2. Simulación (solo imprime): `python scripts/gh_issues_from_todo.py`
3. Crear issues: `python scripts/gh_issues_from_todo.py --apply`

Eso no sincroniza en dos direcciones: cerrar un issue en GitHub no tilda el checkbox en el archivo (y al revés).
