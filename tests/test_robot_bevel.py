"""Fasen der Roboterteile: Netzbau, Überlappungsschutz, Vorgaben aus BALLON, Normalen; ohne Referenzdatei aus der Sicherung."""
import collections
import math
from pathlib import Path
import tempfile
import tomllib
import unittest

import numpy as np
from PIL import Image

from formgen import geom
from formgen.models.robot import kit, roboterbasic_01 as basic
from formgen.robot import bevel, glb
from tools import robot_cycles

ROOT = Path(__file__).resolve().parents[1]

SQUARE = [(0, 0), (.1, 0), (.1, .1), (0, .1)]


def closed(faces):
    edges = collections.Counter((a, b) for f in np.asarray(faces).tolist() for a, b in zip(f, f[1:] + f[:1]))
    return all(n == 1 and edges.get((b, a)) == 1 for (a, b), n in edges.items())


def volume(vertices, faces):
    v, f = np.asarray(vertices), np.asarray(faces)
    return float(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6)


def prism(outline, height):
    """Gerades Prisma über einem gegen den Uhrzeigersinn laufenden Umriss."""
    n = len(outline)
    v = [(*q, 0.) for q in outline] + [(*q, height) for q in outline]
    faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return np.array(v), np.array(geom._triangulate(v, faces))


class CubeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = prism(SQUARE, .1)
        cls.done = bevel.apply(*cls.source, .01)

    def test_all_twelve_edges_and_the_diagonals_stay(self):
        self.assertEqual(self.done.edges, 12)
        self.assertAlmostEqual(self.done.width, .01)
        self.assertTrue(closed(self.done.faces))

    def test_bounds_stay_and_faces_step_back_by_the_width(self):
        v = self.done.vertices
        np.testing.assert_allclose([v.min(axis=0), v.max(axis=0)], [[0] * 3, [.1] * 3], atol=1e-12)
        on_face = v[np.abs(v[:, 2]) < 1e-12]
        np.testing.assert_allclose([on_face[:, :2].min(), on_face[:, :2].max()], [.01, .09], atol=1e-12)

    def test_volume_matches_rounded_edges(self):
        w, a = .01, .1
        strip = (1 - math.sqrt(.5)) * w * w                         # zwei Segmente: Querschnitt wegfallend (1 − √½) w², weniger als die ebene Fase w²/2
        expected = a ** 3 - 12 * (a - 2 * w) * strip
        self.assertAlmostEqual(volume(self.done.vertices, self.done.faces), expected, delta=8 * w ** 3)     # Rest: acht Ecken

    def test_profile_point_lies_on_the_arc(self):
        v = self.done.vertices
        w = .01
        mids = v[(np.abs(v[:, 0] - w * (1 - math.sqrt(.5))) < 1e-9) & (np.abs(v[:, 1] - w * (1 - math.sqrt(.5))) < 1e-9)]
        self.assertGreaterEqual(len(mids), 2)

    def test_bevel_normals_are_smooth_across_the_middle_of_the_strip(self):
        hard = glb.split_normals(self.done.vertices, self.done.faces)[1]
        soft = glb.split_normals(self.done.vertices, self.done.faces, soft=self.done.soft)[1]
        self.assertLess(len(soft), len(hard))                       # Gegenprobe: ohne soft bricht die 45°-Kante, Punkte werden getrennt
        self.assertTrue(((soft @ [0, 0, 1]) > .999).any())          # große Fläche behält ihre Normale


class ShapesTest(unittest.TestCase):
    def test_concave_edge_gets_a_fillet_and_stays_closed(self):
        v, f = prism([(0, 0), (.1, 0), (.1, .05), (.05, .05), (.05, .1), (0, .1)], .02)
        done = bevel.apply(v, f, .002)
        self.assertTrue(closed(done.faces))
        self.assertAlmostEqual(done.width, .002)
        arc = .05 + .002 * (1 - math.sqrt(.5))                      # Hohlkehle: Profilpunkt liegt außerhalb des Körpers, auf dem Kreis um (0,052; 0,052)
        self.assertLess(np.abs(done.vertices[:, :2] - arc).sum(axis=1).min(), 1e-9)
        self.assertGreater(volume(done.vertices, done.faces), .0)

    def test_smooth_surface_below_the_angle_stays_untouched(self):
        ring = [(math.cos(t), math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
        v, f = prism(ring, 1.)
        done = bevel.apply(v, f, .05)
        self.assertEqual(done.edges, 48)                            # nur die beiden Ränder, nicht die 15°-Mantelkanten
        self.assertTrue(closed(done.faces))

    def test_edge_ending_in_a_smooth_surface_tapers_out(self):
        v = np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (.4, .5, .6), (.6, .5, .6)])
        f = np.array([(0, 2, 1), (0, 3, 2), (0, 1, 5), (0, 5, 4), (2, 3, 4), (2, 4, 5), (1, 2, 5), (3, 0, 4)])
        done = bevel.apply(v, f, .01, angle_deg=90)                 # nur First und Grundkanten, die Grate liegen unter der Grenze
        self.assertEqual(done.edges, 5)
        self.assertTrue(closed(done.faces))
        for tip in v[4:]:
            self.assertLess(np.linalg.norm(done.vertices - tip, axis=1).min(), 1e-12)       # Firstenden bleiben stehen, das Profil läuft spitz aus

    def test_open_or_broken_meshes_are_refused(self):
        v, f = prism(SQUARE, .1)
        with self.assertRaises(bevel.BevelError):
            bevel.apply(v, np.asarray(f)[:-1], .01)


class ClampTest(unittest.TestCase):
    def test_thin_plate_clamps_the_whole_part_and_nothing_flips(self):
        v, f = prism(SQUARE, .002)
        done = bevel.apply(v, f, .01)
        self.assertLess(done.width, .001)
        self.assertGreater(done.width, .0005)
        self.assertGreater(volume(done.vertices, done.faces), 0)
        self.assertTrue(closed(done.faces))

    def notched(self):
        """Prisma mit einer 0,5-mm-Kante im Umriss: Kleinstkante wie sie der Boolean an einer Fuge hinterlässt."""
        return prism([(0, 0), (.0995, 0), (.1, .0005), (.1, .1), (0, .1)], .05)

    def test_common_clamp_lets_a_tiny_edge_shrink_everything(self):
        self.assertLess(bevel.apply(*self.notched(), .002).width, .001)

    def test_local_clamp_keeps_the_width_away_from_the_tiny_edge(self):
        done = bevel.apply(*self.notched(), .002, local=True)
        self.assertAlmostEqual(done.width, .002)
        self.assertTrue(closed(done.faces))
        self.assertGreater(volume(done.vertices, done.faces), 0)


    def test_sharp_sector_steps_back_at_most_by_the_miter_limit(self):
        v, f = prism([(0, 0), (1, .02), (0, .04)], .5)              # spitzer Keil: volle Gehrung wäre das 25-Fache der Breite
        done = bevel.apply(v, f, .001)
        tip = done.vertices[done.vertices[:, 0].argmax()]
        self.assertLess(1 - tip[0], 2 * bevel.MITER * .001)
        self.assertTrue(closed(done.faces))

    def test_short_run_of_a_grazing_groove_is_left_out(self):
        v = np.array([(0, 0, 0), (.001, 0, 0), (.002, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)], float)
        kept = bevel._without_short_runs(v, {(0, 1), (1, 2), (3, 4), (4, 5)}, .5)
        self.assertEqual(kept, {(3, 4), (4, 5)})


class CyclesToolTest(unittest.TestCase):
    def test_measure_reads_the_inside_of_each_role_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            image, mask = Path(tmp) / 'i.png', Path(tmp) / 'm.png'
            rgb = np.full((60, 60, 3), 200, np.uint8)
            rgb[:, 30:] = 40
            rgb[:, 29:31] = 255                                     # Randpixel dürfen den Wert nicht ziehen
            levels = robot_cycles.srgb(np.array([1 / 3, 2 / 3])) * 255
            m = np.zeros((60, 60, 4), np.uint8)
            m[..., 3] = 255
            m[:, :30, :3], m[:, 30:, :3] = int(levels[0]), int(levels[1])
            Image.fromarray(rgb).save(image)
            Image.fromarray(m).save(mask)
            report = robot_cycles.measure(image, mask, ['graphite', 'shell'], dict(roles=dict(shell='#D6D7D5')))
        self.assertEqual((report['graphite']['bild'], report['shell']['bild']), ('#C8C8C8', '#282828'))
        self.assertEqual(report['shell']['soll'], '#D6D7D5')
        self.assertEqual(report['graphite']['clip'], 0)

    def test_too_small_roles_are_reported_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            image, mask = Path(tmp) / 'i.png', Path(tmp) / 'm.png'
            Image.fromarray(np.full((20, 20, 3), 90, np.uint8)).save(image)
            m = np.zeros((20, 20, 4), np.uint8)
            m[..., 3] = 255
            m[..., :3] = int(robot_cycles.srgb(1 / 3) * 255)
            m[10, 10, :3] = int(robot_cycles.srgb(2 / 3) * 255)
            Image.fromarray(m).save(mask)
            report = robot_cycles.measure(image, mask, ['graphite', 'shell'], dict(roles={}))
        self.assertIsNone(report['shell']['bild'])
        self.assertEqual(report['graphite']['bild'], '#5A5A5A')

    def test_cycles_colours_stay_out_of_glb_and_sheet(self):
        skins = tomllib.loads((ROOT / 'skins.toml').read_text())['skins']['weiss_graphit']
        self.assertLessEqual(set(skins['aaa']), set(skins['roles']))
        shell = glb.materials('weiss_graphit', ['shell'])[0]['pbrMetallicRoughness']['baseColorFactor'][:3]
        self.assertEqual(shell, glb.linear(skins['roles']['shell']))
        self.assertNotEqual(shell, glb.linear(skins['aaa']['shell']))


class ModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {p['id']: p for p in basic.parts(basic.PARAMS)}
        cls.doc = bevel.evaluate(basic.document())
        cls.parts = {p['id']: p for p in cls.doc['parts']}

    def test_widths_follow_ballon(self):
        self.assertEqual(kit.BEVEL, {'cyl': .8, 'hull': 2.0, 'plate': 1.0, 'box': 1.0, 'loft': 1.6, 'wrap': 1.2, 'tube': 0.0})
        for p in self.source.values():
            if p['form'] in kit.BEVEL and p['id'] not in ('buckle', 'buckle_inset') and 'bridge' not in p['id'] and not p['id'].startswith('arm_'):
                self.assertEqual(p['bevel'], kit.BEVEL[p['form']], p['id'])
        self.assertEqual(self.source['buckle']['bevel'], 2)         # eigene Fase des Teils geht vor, wie in BALLON

    def test_helmet_and_tubes_stay_unchanged(self):
        helmet = [p for p in self.parts.values() if p['id'].startswith('helmet_')]
        self.assertEqual(len(helmet), 58)
        for p in helmet:
            self.assertEqual(p['bevel'], 0)
            self.assertNotIn('bevel_status', p)
            self.assertNotIn('soft', p['mesh'])
        self.assertTrue(all('bevel_status' not in p for p in self.parts.values() if p.get('form') == 'tube'))

    # Zählwerte: 424 Bauteile − 58 Helm − 20 Leitungen = 346; sieben Teile mit Fugen. Ändert sich das Modell, gehören sie mit Grund geändert.
    def test_every_other_part_is_bevelled_closed_and_without_warning(self):
        done = [p for p in self.parts.values() if p['bevel'] > 0]
        self.assertEqual(len(done), 346)
        self.assertEqual(self.doc['warnings'], [])
        for p in done:
            self.assertEqual(p['bevel_status'], 'mesh_bevel', p['id'])
            self.assertTrue(closed(p['mesh']['faces']), p['id'])
            self.assertGreater(volume(p['mesh']['vertices'], p['mesh']['faces']), 0, p['id'])

    def test_parts_with_grooves_keep_their_full_width(self):
        cut = [p for p in self.parts.values() if p.get('cuts')]
        self.assertEqual(len(cut), 7)
        for p in cut:
            self.assertAlmostEqual(p['bevel_effective_mm'], p['bevel'], places=3, msg=p['id'])

    def test_counts_and_bounds_describe_the_bevelled_meshes(self):
        self.assertEqual(self.doc['counts']['triangles'], sum(len(p['mesh']['faces']) for p in self.parts.values()))
        every = np.concatenate([np.asarray(p['mesh']['vertices']) for p in self.parts.values()])
        np.testing.assert_allclose(self.doc['bounds_m'], [every.min(axis=0), every.max(axis=0)])


if __name__ == '__main__':
    unittest.main()
