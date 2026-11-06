"""HTML contract checks; these tests never render or open a browser."""
import copy
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

from formgen import sheet, sheet_figure


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def document(kind='weapon'):
    return {'info': {'id': 'TEST', 'kind': kind, 'name_de': 'Studie <&>',
                     'provenance': {'kind': 'Annahme', 'source': 'Test'}},
            'parts': [{'id': 'body', 'label': 'Gehäuse', 'assembly': 'body', 'role': 'shell',
                       'mesh': {'vertices': [[0, 0, 0], [.1, -.2, .3], [.1, 0, 0]], 'faces': [[0, 1, 2]]}}],
            'assemblies': [{'id': 'body', 'de': 'Körper'}], 'anchors': {}, 'poses': {}, 'warnings': []}


def views():
    keys = ['hero', 'iso', 'detail_trigger'] + [key for key, _ in sheet.ORTHOS] + ['skin_' + name for name in sheet.SKINS]
    result = {key: f'../views/TEST/{key}.png' for key in keys}
    result['_meta'] = {key: {'width': 960, 'height': 480, 'scale_px_m': 1200,
                            'reference_lines': {'horizontal': [40, 440], 'vertical': [480]}}
                       for key, _ in sheet.ORTHOS}
    result['_meta']['hero'] = {'width': 1440, 'height': 960,
                              'labels': [{'label': 'Gehäuse', 'x': 500, 'y': 480}]}
    return result


def line_document(skin):
    return {**document(), 'generator': {'variant': {'skin': skin}}}


class SheetTests(unittest.TestCase):
    def test_main_skin_of_the_line_comes_first_and_is_marked(self):
        self.assertEqual(sheet.sheet_skins(line_document('wueste')), ('wueste', *sheet.SKINS))
        images = {**views(), 'skin_wueste': '../views/TEST/skin_wueste.png'}
        result = sheet.build(line_document('wueste'), images)
        self.assertIn('Wüste · Haupt-Skin', result)
        self.assertIn('--skins:5', result)
        self.assertNotIn('Ansichten ausstehend', result)
        self.assertLess(result.index('skin_wueste.png'), result.index('skin_standard.png'))

    def test_main_skin_among_the_fixed_four_is_not_doubled(self):
        self.assertEqual(sheet.sheet_skins(line_document('polar')), ('polar', 'standard', 'nacht', 'kobalt'))
        result = sheet.build(line_document('polar'), views())
        self.assertIn('Polar · Haupt-Skin', result)
        self.assertEqual(result.count('skin_polar.png'), 1)

    def test_sheet_without_line_keeps_the_fixed_four(self):
        self.assertEqual(sheet.sheet_skins(document()), sheet.SKINS)
        self.assertEqual(sheet.sheet_skins({**document(), 'generator': None}), sheet.SKINS)
        result = sheet.build(document(), views())
        self.assertIn('Vier Skins', result)
        self.assertNotIn('Haupt-Skin', result)

    def test_complete_weapon_uses_external_images_and_bilingual_prompts(self):
        doc, images = document(), views()
        before = copy.deepcopy((doc, images))
        result = sheet.build(doc, images)
        parsed = Markup(result)
        imgs = [attrs for tag, attrs in parsed.tags if tag == 'img']
        self.assertEqual(len(imgs), 12)
        self.assertTrue(all(img['src'].startswith('../views/TEST/') for img in imgs))
        self.assertNotIn('data:image', result)
        self.assertIn('Studie &lt;&amp;&gt;', result)
        self.assertIn('Prompt · Deutsch', result)
        self.assertIn('Prompt · English', result)
        self.assertIn('ohne Wechselvisier', result)
        self.assertIn('gleicher Maßstab', result)
        self.assertIn('../fonts/Barlow-Regular.ttf', result)
        self.assertEqual(before, (doc, images))

    def test_unavailable_views_and_scale_remain_visible(self):
        result = sheet.build(document(), {})
        self.assertEqual(result.count('Ansicht ausstehend</div>'), 12)
        self.assertIn('Ansichten ausstehend:', result)
        self.assertIn('Maßstab offen', result)
        self.assertNotIn('<img ', result)

    def test_max_eight_labels_and_all_other_parts_remain_documented(self):
        images = views()
        images['_meta']['hero']['labels'] = [{'label': f'Teil {i}', 'x': 50*i, 'y': 300} for i in range(12)]
        result = sheet.build(document(), images)
        self.assertEqual(result.count('<g class="callout">'), 8)
        self.assertIn('Weitere Bauteile: Gehäuse', result)

    def test_scale_disagreement_is_not_claimed_as_shared_scale(self):
        images = views()
        images['_meta']['front']['scale_px_m'] = 900
        result = sheet.build(document(), images)
        self.assertIn('Maßstab offen', result)
        self.assertIn('noch nicht belegt', result)

    def test_warnings_escape_content_and_deduplicate(self):
        doc = document()
        doc['warnings'] = ['<script>bad()</script>', '<script>bad()</script>']
        result = sheet.build(doc, views())
        self.assertNotIn('<script>', result)
        self.assertIn('1 offene Hinweise', result)
        self.assertIn('&lt;script&gt;', result)

    def test_embedded_and_remote_images_are_rejected(self):
        for path in ('data:image/png;base64,AAAA', 'https://example.org/test.png', '//example.org/test.png', 'javascript:alert(1)'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                sheet.build(document(), {'hero': path})

    def test_separate_sight_does_not_disappear(self):
        doc = document()
        doc['parts'].append(dict(doc['parts'][0], id='optic', label='Optik', assembly='sight', sight=True))
        result = sheet.build(doc, views())
        self.assertIn('data-view="sight_iso"', result)
        self.assertIn('data-view="sight_side"', result)
        self.assertNotIn('Kein Wechselvisier im Modell', result)

    def test_no_renderer_dependency(self):
        import builtins
        real_import = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name == 'raster' or name.endswith('.raster'):
                raise AssertionError('sheet attempted to import raster')
            return real_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=guarded):
            self.assertIn('<html', sheet.build(document(), views()))

    def test_figure_assemblies_parts_anchors_and_poses(self):
        doc = document('figure')
        doc['anchors'] = {'Socket_Hand': {'part': 'body', 'at': [0, 30, 10], 'source': 'Annahme'}}
        doc['poses'] = {'idle': {}, 'ready': {}}
        images = {key: f'../views/TEST/{key}.png' for key in
                  ['front', 'side_left', 'back', 'iso', 'exploded', 'idle', 'ready', 'assembly_body']}
        result = sheet_figure.build(doc, images)
        self.assertEqual(result.count('<img '), 8)
        self.assertIn('data-assembly="body"', result)
        self.assertIn('<td>Gehäuse</td>', result)
        self.assertIn('Socket_Hand', result)
        self.assertIn('f/u/x: 0 / 30 / 10 mm', result)
        self.assertEqual(sheet.build(doc, images), result)

    def test_figure_keeps_undeclared_parts_and_missing_pose_warnings(self):
        doc = document('figure')
        doc['assemblies'] = []
        result = sheet_figure.build(doc, {})
        self.assertIn('data-assembly="body"', result)
        self.assertIn('Nicht deklarierte Baugruppen', result)
        self.assertIn('Pose ready ist', result)
        self.assertIn('Socket_Hand fehlt', result)


if __name__ == '__main__':
    unittest.main()
