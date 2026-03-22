# Comandos útiles

Referencia rápida para desarrollo y uso del proyecto en la raíz del repo (`xdraco-marketer`).

## Entorno Python

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env
```

## Tests y calidad

```bash
pytest tests/ -q
pytest tests/test_rules_engine.py -v
pytest tests/ --tb=short
```

```bash
ruff check src tests
ruff check src tests --fix
```

## CLI instalada con el paquete

Tras `pip install -e .`, el entrypoint es `xdraco-marketer`:

```bash
xdraco-marketer --help
xdraco-marketer list --page 1 --class 0
xdraco-marketer scan --pages 1 --limit 3 --delay 0.3
xdraco-marketer bargains --rule examples/maga_bargain_rule.yaml --pages 2 --limit 20 --delay 0.2
```

`scan` y `bargains` muestran al final un **reporte en stderr** (recorrido del listado, errores de detalle, cohorte / gangas). `bargains` tiene `--verbose-errors` para tracebacks completos.

## Ejecutar módulo sin instalar script (alternativa)

```bash
python -m xdraco_marketer.cli --help
```

## TODOs → issues de GitHub (opcional)

Requiere [GitHub CLI](https://cli.github.com/) y `gh auth login`.

```bash
python scripts/gh_issues_from_todo.py
python scripts/gh_issues_from_todo.py --apply
```

## API MIR4 (curl de referencia)

Listado (página 1, todas las clases):

```bash
curl -sS "https://webapi.mir4global.com/nft/lists?listType=sale&class=0&levMin=0&levMax=0&powerMin=0&powerMax=0&priceMin=0&priceMax=0&sort=latest&page=1&languageCode=es" -H "Accept: application/json" | head -c 2000
```

Reemplazá `seq` y `transportID` por valores reales de una fila del listado:

```bash
curl -sS "https://webapi.mir4global.com/nft/character/summary?seq=REPLACE&languageCode=es" -H "Accept: application/json"
curl -sS "https://webapi.mir4global.com/nft/character/stats?transportID=REPLACE&languageCode=es" -H "Accept: application/json"
```

## Documentación en repo

| Archivo | Contenido |
|---------|-----------|
| [architecture.md](architecture.md) | Arquitectura de la solución |
| [commands.md](commands.md) | Este archivo |
| [agent-rules-template.md](agent-rules-template.md) | Template para asistentes al armar reglas YAML |
| [rule-identifiers.md](rule-identifiers.md) | Qué campos usar en reglas (evitar iconos/URLs) |
