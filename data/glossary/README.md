# Glosarios de datos (reglas / documentación)

Archivos YAML con listas inferidas o referenciadas desde la API pública y fuentes externas.

| Archivo | Contenido |
|---------|-----------|
| [warrior_skills.yaml](warrior_skills.yaml) | Guerrero (1): nombres ES desde libros en inventario |
| [sorcerer_skills.yaml](sorcerer_skills.yaml) | Maga (2): ES + referencia EN (Fandom) cuando aplica; `skill_id_suggested` |
| [taoist_skills.yaml](taoist_skills.yaml) | Taoísta (3) |
| [arbalist_skills.yaml](arbalist_skills.yaml) | Arquero (4) |
| [lancer_skills.yaml](lancer_skills.yaml) | Lancero (5) |
| [darkist_skills.yaml](darkist_skills.yaml) | Darkist (6) |
| [lionheart_skills.yaml](lionheart_skills.yaml) | Lionheart (7) |

## Niveles de habilidades (MIR4)

En el juego, cada skill tiene nivel **de 1 a 12** (máximo). Las reglas YAML (`skill_min`, `all_skills_min`) solo aceptan umbrales en ese rango; ver `SkillMinLevel` / `AllSkillsMin` en `src/xdraco_marketer/rules/ast.py`.

## Cómo se actualiza

- **Todas las clases salvo Maga (por defecto):** `python scripts/scrape_skill_books_by_class.py --class all --out-dir data/glossary --pages 2 --max-chars 20`
- **Solo Maga:** `python scripts/scrape_skill_books_by_class.py --class 2 --out-dir data/glossary` (o el wrapper `python scripts/scrape_sorcerer_skill_books.py --out-dir data/glossary`)
- **Incluir Maga en un barrido `all`:** `--include-sorcerer` (sobrescribe `sorcerer_skills.yaml` generado; el archivo enriquecido a mano conviene respaldar antes).
- Revisar UTF-8 en consola Windows; con `--out-dir` los YAML se escriben en UTF-8.

## Límites

- El endpoint `GET /nft/character/skills` puede requerir sesión (código `60001`); los niveles de skill en `CharacterProfile.skills` siguen pendientes de integración oficial.
