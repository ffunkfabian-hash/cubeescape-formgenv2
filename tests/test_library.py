"""Explicit prepared-Geo selection without an implicit library render."""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from formgen import build


class LibrarySelectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='formgen-library-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def test_explicit_library_id_resolves_to_existing_geo_source(self):
        source = self.path/'KC01.geo.json'
        source.write_text('{}')
        args = build.parse_args(['KC01', '--legacy-dir', str(self.path), '--stages', 'geometry'])
        self.assertEqual(args.registry['KC01'], source.resolve())
        self.assertEqual(args.ids, ['KC01'])
        self.assertEqual(args.stages, ['geometry'])
        self.assertEqual(build.REGISTRY.keys(), {'R01', 'W01', 'KG02', 'VS02'})

    def test_discovery_does_not_read_geo_or_enable_bulk_build(self):
        (self.path/'KC01.geo.json').write_text('validated only when selected')
        (self.path/'notes.json').write_text('{}')
        args = build.parse_args(['--legacy-dir', str(self.path), '--stages', 'geometry'])
        self.assertEqual(args.ids, [])
        self.assertIn('KC01', args.registry)
        self.assertNotIn('notes', args.registry)
        with patch.object(build, 'geometry_plan', return_value=[]) as plan, \
                patch.object(build, 'run_artifacts', return_value=[]), redirect_stderr(StringIO()):
            build.main(['--legacy-dir', str(self.path), '--stages', 'geometry'])
        self.assertEqual(set(plan.call_args.args[0]), {'R01', 'W01', 'KG02', 'VS02'})

    def test_explicit_geo_can_replace_bundled_legacy_fixture(self):
        source = self.path/'KG02.geo.json'
        source.write_text('{}')
        args = build.parse_args(['KG02', '--legacy-dir', str(self.path)])
        self.assertEqual(args.registry['KG02'], source.resolve())

    def test_native_collision_missing_directory_and_dummy_are_errors(self):
        (self.path/'R01.geo.json').write_text('{}')
        for argv in (['--legacy-dir', str(self.path)],
                     ['--legacy-dir', str(self.path/'absent')],
                     ['--dummy', '--legacy-dir', str(self.path)]):
            with self.subTest(argv=argv), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                build.parse_args(argv)

    def test_single_weapon_geo_export_includes_required_sight_spec_without_sight_images(self):
        from formgen import geo
        from formgen.cache import file_hash
        out, cache = self.path/'out', self.path/'cache'
        argv = ['KG02', '--stages', 'specs,geo', '--out', str(out), '--cache', str(cache)]
        for _ in range(2):
            build.main(argv)
        exported = geo.load(out/'geo/KG02.geo.json')
        self.assertEqual(exported['info']['id'], 'KG02')
        self.assertEqual(file_hash(out/'specs/VS02.spec.json'),
                         file_hash(build.ROOT/'tests/fixtures/VS02.spec.json'))
        self.assertFalse((out/'views').exists())
        self.assertFalse((out/'geo/VS02.geo.json').exists())
