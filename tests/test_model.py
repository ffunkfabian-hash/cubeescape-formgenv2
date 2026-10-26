import copy
import json
import tempfile
import unittest
from pathlib import Path

from formgen import model


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.doc = model.load('formgen/models/mini.py')

    def test_aliases_preserve_source_and_do_not_mutate(self):
        d = copy.deepcopy(self.doc)
        d['META'] = d.pop('info')
        p = d['parts'][0]
        for a,b in (('assembly','asm'),('role','mat'),('label','de')):
            p[b] = p.pop(a)
        result = model.normalize(d)
        self.assertEqual(result['parts'][0], self.doc['parts'][0])
        self.assertIn('META',d)
        json.dumps(result,allow_nan=False)

    def test_conflicting_alias_is_error(self):
        self.doc['parts'][0]['asm'] = 'other'
        with self.assertRaisesRegex(model.ModelError,'Widersprüchliche'):
            model.normalize(self.doc)

    def test_references_and_ids(self):
        for mutate in (
            lambda d: d['parts'][1].update(id='shell'),
            lambda d: d['parts'][0].update(assembly='missing'),
            lambda d: d['parts'][0].update(parent_part='missing'),
            lambda d: d['anchors']['Socket_Hand'].update(part='missing'),
            lambda d: d['assemblies'].append({'id':'empty'}),
            lambda d: d['parts'][0].update(parent_part='grip') or d['parts'][1].update(parent_part='shell'),
        ):
            with self.subTest(mutate=mutate):
                d = copy.deepcopy(self.doc)
                mutate(d)
                with self.assertRaises(model.ModelError):
                    model.normalize(d)

    def test_provenance_and_finite_dimensions(self):
        for mutate in (
            lambda d: d['info'].pop('provenance'),
            lambda d: d['parts'][0].update(w=-1),
            lambda d: d['parts'][0].update(w=float('nan')),
            lambda d: d['parts'][0].update(color='red'),
        ):
            d=copy.deepcopy(self.doc); mutate(d)
            with self.assertRaises(model.ModelError):
                model.normalize(d)

    def test_rapid_file_edits_do_not_reuse_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'model.py'
            source=Path('formgen/models/mini.py').read_text()
            p.write_text(source)
            a=model.load(p)
            p.write_text(source.replace('"f1": 100','"f1": 200'))
            b=model.load(p)
            self.assertNotEqual(a['source']['sha256'],b['source']['sha256'])
            self.assertEqual(b['parts'][0]['f1'],200)

    def test_pilot_accepts_all_kit_fields(self):
        doc=model.load('formgen/models/weapons/w01_auto_rifle.py')
        self.assertEqual(len(doc['parts']),72)
        self.assertEqual(len({p['id'] for p in doc['parts']}),72)
