import httpx

from xdraco_marketer.mir4_api.client import Mir4Client


def test_client_list_summary_stats_listing() -> None:
    list_payload = {
        "code": 200,
        "data": {
            "firstID": 1,
            "totalCount": 1,
            "more": 0,
            "lists": [
                {
                    "rowID": 1,
                    "seq": 999,
                    "transportID": 111,
                    "nftID": "1",
                    "powerScore": 100000,
                    "class": 2,
                    "price": 500,
                }
            ],
        },
    }
    summary_payload = {
        "code": 200,
        "data": {
            "blockChain": "WEMIX",
            "character": {"class": "2", "powerScore": "100000"},
            "equipItem": {
                "1": {
                    "itemIdx": "1",
                    "enhance": "10",
                    "grade": "5",
                    "tier": "4",
                    "itemType": "2_1",
                    "itemName": "W",
                }
            },
        },
    }
    stats_payload = {
        "code": 200,
        "data": {
            "lists": [
                {
                    "statName": "Ataque Mágico",
                    "statValue": "100",
                    "iconPath": "https://h/x.png",  # opcional en API real; ignorado al mapear stats
                }
            ]
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if "/nft/lists" in u:
            return httpx.Response(200, json=list_payload)
        if "/nft/character/summary" in u and "seq=999" in u:
            return httpx.Response(200, json=summary_payload)
        if "/nft/character/stats" in u and "transportID=111" in u:
            return httpx.Response(200, json=stats_payload)
        return httpx.Response(404, json={})

    tr = httpx.MockTransport(handler)
    with Mir4Client(base_url="https://webapi.mir4global.com", delay_s=0, transport=tr) as client:
        rows = list(client.iter_sale_rows(max_pages=1))
        assert len(rows) == 1
        listing = client.fetch_listing(rows[0])
        assert listing.listing_id == "999"
        assert listing.price == 500
        assert listing.character.power == 100000
        assert listing.character.stats.get("ataque magico") == 100.0
