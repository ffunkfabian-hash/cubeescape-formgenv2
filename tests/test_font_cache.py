"""Static font dependency in geometry keys and worker source snapshots."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from formgen import build, text
from formgen.cache import file_hash


class FontCacheTests(unittest.TestCase):
    def test_geometry_snapshot_contains_the_resource_read_by_text(self):
        artifact=build.geometry_plan({'W01':build.ROOT/'formgen/models/weapons/w01_auto_rifle.py'})[0]
        self.assertEqual(artifact.inputs['source_hashes'][str(text.FONT_PATH)],file_hash(text.FONT_PATH))

    def test_font_edit_changes_native_key_rejects_old_worker_and_keeps_legacy_key(self):
        with tempfile.TemporaryDirectory(prefix='formgen-font-key-') as directory:
            path=Path(directory)/'font.json'
            path.write_bytes(text.FONT_PATH.read_bytes())
            native={'MINI':build.ROOT/'formgen/models/mini.py'}
            legacy={'KG02':build.ROOT/'tests/fixtures/KG02.geo.json'}
            with patch.object(build,'FONT_PATH',path):
                before=build.geometry_plan(native)[0]
                imported=build.geometry_plan(legacy)[0]
                path.write_bytes(path.read_bytes()+b'\n')
                self.assertNotEqual(before.key,build.geometry_plan(native)[0].key)
                self.assertEqual(imported.key,build.geometry_plan(legacy)[0].key)
                with self.assertRaisesRegex(RuntimeError,'Quelle'):
                    build._check_sources(before.inputs['source_hashes'])

    def test_resource_reader_refreshes_when_bytes_change_in_one_process(self):
        with tempfile.TemporaryDirectory(prefix='formgen-font-reader-') as directory:
            path=Path(directory)/'font.json'
            value=deepcopy(text.font_data());path.write_text(json.dumps(value))
            before=text.font_data(path)
            value['glyphs']['65']['advance']+=1;path.write_text(json.dumps(value))
            after=text.font_data(path)
            self.assertEqual(after['glyphs']['65']['advance'],before['glyphs']['65']['advance']+1)
