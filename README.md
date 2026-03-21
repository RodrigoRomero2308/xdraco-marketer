# xdraco-marketer

Conjunto de herramientas para apoyar decisiones en el mercado de **NFTs** e **ítems XDraco** de **MIR4** (ecosistema WEMIX PLAY).

## Contexto: MIR4 y el mercado

**MIR4** es un MMORPG de Wemade con economía conectada a blockchain (**WEMIX**). Los activos relevantes para trading suelen ser:

| Ámbito | Qué es | Dónde opera |
|--------|--------|-------------|
| **Personajes NFT** | Cuentas/personajes convertidos a NFT (ERC-721), con atributos, rareza, poder | Mercado unificado **WEMIX PLAY**, históricamente también **XDraco** como marca/servicio |
| **XDraco (ítems / servicios)** | Plataforma de ítems coleccionables, subastas (**DSP**), mercado abierto (**EXD**), etc., ligada a políticas y operación de Wemade | **xdraco.com**, **wemixplay.com** (NFT / webshop según producto) |
| **Cadenas** | Tras la renovación del mercado (~2024), muchos flujos se unificaron en **WEMIX 3.0 mainnet**; antes existía distinción **Tornado** (juego/MIRAGE) vs **Mainnet** (mercado) — conviene validar en documentación actual al integrar datos | Conversiones y tasas de gas en **WEMIX** |

**Qué suele importar para “decisiones de mercado”:**

- **Personajes NFT:** nivel, power score, clase, rareza, skills, historial de ventas / listing vs floor del mercado.
- **Economía:** **DRACO**, **HYDRA**, **WEMIX** y cómo se usan en listing, fees y conversión cadena ↔ wallet.
- **Reglas de juego:** requisitos para mint NFT (p. ej. nivel mínimo y power), sellado/desellado (personaje no jugable mientras está “sealed” para trading, según reglas vigentes).

**Fuentes de datos para herramientas:**

- **APIs WEMIX:** documentación en [docs.wemix.com](https://docs.wemix.com) (tokens, balances, inventario NFT por dirección) — suelen requerir **API key**.
- **Front WEMIX PLAY / rankings:** hay páginas de ranking y marketplace en **wemixplay.com**; para series históricas puede hacer falta scraping o almacenar snapshots (respetar ToS y robots).
- **On-chain:** contratos ERC-721/1155 en mainnet WEMIX para verificación de propiedad y eventos `Transfer` si conoces las direcciones de colección.

## Setup local

Requisitos: **Python 3.11+**

```bash
cd xdraco-marketer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

Estructura prevista del paquete:

```
src/xdraco_marketer/   # código (clientes API, scrapers, modelos, informes)
data/                  # datos locales (gitignore en raw/ si aplica)
```

## Reglas y gangas (motor genérico)

- **Perfil:** `CharacterProfile` (clase, power, skills, ítems, pets, piedras) y `Listing` (precio + moneda).
- **Reglas:** objeto JSON/YAML con `type` y composición `and` / `or` / `not` más condiciones (`class_is`, `power_gte`, `skill_min`, `all_skills_min`, `item_any` con `item_type` / `item_type_prefix`, `items_all_slots_min`, `pets_any_of`, `pets_all_of`, `stone_min_tier`, `stones_types_min_tier`, `stat_key_gte`, `stat_key_suffix_gte`). Ver `examples/maga_bargain_rule.yaml`.
- **Stats en reglas:** `CharacterProfile.stats` es clave normalizada → valor (ver `stat_labels.normalize_stat_label`: minúsculas, sin acentos). Los datos vienen del `statName` de la API; en YAML usá nombres legibles como **Ataque Mágico**, **Evasión**, **Defensa Física** — el motor las normaliza al comparar.
- **Gangas:** `BargainDetector` compara cada listado que cumple la regla con la **mediana de precios del resto del cohorte**; si `precio <= mediana * median_ratio_max` (p. ej. 0.92), se considera ganga. Requiere `min_comparables` listados en el cohorte.

```python
from pathlib import Path
from decimal import Decimal
from xdraco_marketer import BargainDetector, BargainSettings, Listing, load_rule_from_yaml_text

rule = load_rule_from_yaml_text(Path("examples/maga_bargain_rule.yaml").read_text(encoding="utf-8"))
detector = BargainDetector(rule, BargainSettings(median_ratio_max=Decimal("0.92"), min_comparables=5))
# listings = [...]  # datos del mercado normalizados
for deal in detector.find(listings):
    print(deal.listing.listing_id, deal.ratio_to_median, deal.median_peer_price)
```

## API pública XDraco (`webapi.mir4global.com`)

Documentación informal de requests/respuestas y flujo **seq / transportID** en `example-calls/`. En código:

- `xdraco_marketer.mir4_api.Mir4Client` — pagina `/nft/lists`, pide `summary` + `stats` y arma `Listing` (`fetch_listing`, `iter_sale_rows`).
- `xdraco_marketer.mir4_api.list_row_to_profile_stub` — fila de `/nft/lists`.
- `xdraco_marketer.mir4_api.summary_data_to_profile` — `data` de `/nft/character/summary` (equipo, piedras `8_*`, pets `23_*`/`28_*`).
- `xdraco_marketer.mir4_api.stats_response_to_stat_map` — `data.lists` de `/nft/character/stats`.
- `xdraco_marketer.mir4_api.with_stats` — fusiona stats completos sobre el perfil del summary.

CLI (tras `pip install -e .`):

```bash
xdraco-marketer list --page 1 --class 0
xdraco-marketer scan --pages 1 --limit 3 --delay 0.3
xdraco-marketer bargains --rule examples/maga_bargain_rule.yaml --pages 2 --limit 20 --delay 0.2
```

**Nota:** en las muestras actuales, **skills** no vienen en `summary`; habrá que localizar otro campo o endpoint para `skill_*` en reglas.

## Documentación en el repo

| Qué | Dónde |
|-----|--------|
| Setup, motor de reglas, CLI, API | Este **README** |
| **Arquitectura** (capas, flujo, extensión) | [docs/architecture.md](docs/architecture.md) |
| **Comandos útiles** (venv, pytest, CLI, curl) | [docs/commands.md](docs/commands.md) |
| **Template de agente** para ayuda al armar reglas YAML | [docs/agent-rules-template.md](docs/agent-rules-template.md) |
| **Qué IDs usar en reglas** (stats vs itemType vs imágenes) | [docs/rule-identifiers.md](docs/rule-identifiers.md) |
| **Glosarios de habilidades por clase** (ES desde inventario; Maga con wiki opcional) | [data/glossary/README.md](data/glossary/README.md) |
| **Pendientes y roadmap** | [TODO.md](TODO.md) (opcional: [exportar a issues de GitHub](TODO.md#pasar-estos-todos-a-issues-de-github)) |
| Requests de ejemplo y notas sobre `seq` / `transportID` / `itemType` | `example-calls/**/data-infered.txt` |
| Regla YAML de ejemplo | `examples/maga_bargain_rule.yaml` |
| Tests del motor de reglas | `tests/test_rules_engine.py` (+ integración en `tests/test_rules.py`) |

## Próximos pasos (resumen)

1. Ajustar **IDs** en reglas YAML a los mismos que salgan de la API (clase slug, `item_type`, claves de stats).
2. Seguir el backlog en [TODO.md](TODO.md) (skills, alertas, persistencia, etc.).

## Aviso

Los juegos blockchain cambian reglas y URLs con frecuencia. Verifica siempre la documentación oficial de **Wemade / WEMIX PLAY** y las condiciones de uso antes de automatizar extracción de datos.
