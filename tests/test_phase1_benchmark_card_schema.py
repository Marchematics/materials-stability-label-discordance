from pathlib import Path
import json, jsonschema
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_benchmark_card_schema_validates():
    schema=json.loads((OUT/'benchmark_card_schema.json').read_text())
    card=json.loads((OUT/'benchmark_card_main.json').read_text())
    jsonschema.validate(card,schema)
    assert card['retained_denominator']['D2_SourceAware_Stability_36K']==36802
    assert card['retained_denominator']['D5_model_complete']==36801
    assert card['full_source_union_status']['status']=='incomplete'
