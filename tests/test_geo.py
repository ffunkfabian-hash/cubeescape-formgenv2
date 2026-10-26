import copy,json,tempfile,unittest
from jsonschema import ValidationError
from pathlib import Path
from formgen import geo

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures'
class GeoTests(unittest.TestCase):
    def test_real_v1_pilots(self):
        for sid,n in [('KG02',33),('VS02',8)]:
            d=geo.load(FIX/(sid+'.geo.json'))
            self.assertEqual(d['counts']['parts'],n)
            self.assertEqual(d['source_spec']['format_version'],2)
            self.assertEqual(d['info']['id'],sid)
    def test_unknown_fields_ignored(self):
        d=json.loads((FIX/'KG02.geo.json').read_text());d['future_field']={'enabled':True}
        self.assertEqual(geo.normalize(d)['info']['id'],'KG02')
    def test_invalid_version_indices_counts_nan(self):
        base=json.loads((FIX/'KG02.geo.json').read_text())
        edits=[lambda d:d.update(format_version=2),lambda d:d['parts'][0]['mesh']['faces'][0].append(999999),
               lambda d:d['counts'].update(vertices=1),lambda d:d['parts'][0]['mesh']['vertices'][0].__setitem__(0,float('nan'))]
        for edit in edits:
            d=copy.deepcopy(base);edit(d)
            with self.assertRaises((ValueError,ValidationError)):geo.normalize(d)
    def test_spec_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'KG02.geo.json').write_bytes((FIX/'KG02.geo.json').read_bytes());(p/'KG02.spec.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'SHA'):geo.load(p/'KG02.geo.json')
