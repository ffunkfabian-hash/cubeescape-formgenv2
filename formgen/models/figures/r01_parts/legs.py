"""R01 Beine – editierbare, hohle Schalen im Autorenraum (f,u,x), mm.

Vorgabe: Entwurfshöhe 1924 mm (massfigur-v2), keine reale Bildkalibrierung.
Gemessen: vier 4096²-Orthos vom 26.10.2026. Front-Bounds y223..3876,
x-Mitte2048; k=1924/3653. Side-right Kopf-y216, Side-left Kopf-y218: gleicher Pixelmaßstab k=1924/3653,
f=(2150-pixel_x)*k rechts bzw. (pixel_x-1946)*k links.
Seiten-u=1924-(pixel_y-Kopf-y)*k, KEINE Gesamthöhen-Normierung.
Die früheren 420/420-mm-Glieder sind durch die neuen Bildanteile ersetzt.

ACHTUNG: Die Referenzen sind intern nicht gelenkgleich: Cyan-Zentren Front
Knie u704..718, Knöchel u230..239; Seiten bei gleichem Maßstab
Knie≈685, Knöchel≈205. Nutzervorgabe: Front setzt Gelenke und Fußhöhe;
Seiten geben Tiefe und Zehenprofil. Die Gelenkregionen werden geometrisch
auf die Frontlage überführt; Bilder werden nicht verformt.
Diese Fassung verwendet Frontanker (Knie710, Knöchel234); die seitliche
Silhouette ist separat abgelesen. Dies ist keine bestandene Ortho-Abnahme.
Schalenprinzip (explizite Außen-/Innenflächen, getrennte Rückschale, Fuge,
eingefasste Füße): massfigur-v2/bauteile.py:116-145. Keine Mesh-Übernahme.
"""

import math
from collections import defaultdict

PROVENANCE = {
    'kind': 'gemessen',
    'source': 'robot-ortho-front/back/side-right/side-left.png; Pixelanteile bei Vorgabehöhe1924mm; refs/ortho-measurements.json',
    'height_mm': {'kind': 'Vorgabe', 'value': 1924, 'source': 'massfigur-v2 Entwurf'},
    'front_scale': {'kind': 'gemessen', 'mm_per_px': 1924/3653, 'center_x_px': 2048, 'ground_y_px': 3876},
    'side_scale': {'kind': 'gemessen', 'mm_per_px': 1924/3653, 'f0_px': 2150, 'head_y_px': 216, 'side_ground_u_mm': 1924-3560*1924/3653},
    'joint_conflict': 'Front Knie≈711/Knöchel≈234; Seiten bei gleichem Pixelmaßstab685/205. Nutzer: Front bestimmt Gelenke/Fußhöhe, Seite Tiefen und Zehenprofil. Lokale Profilanpassung am Gelenk ausdrücklich Entwurf, keine Bildverformung.',
    'shell_design': 'Annahme: 5mm f-Innenversatz, 3mm seitlicher Innenversatz, 10mm Teilungsfuge; Prinzip massfigur-v2 bauteile.py:116-145; Facettierung B.',
    'hidden_geometry': 'Annahme: Innenkerne, Achslängen, Hüft-f45, Profilinterpolation; verdeckte Außenkanten werden aus sichtbaren Nachbarhöhen interpoliert.',
    'core_fit': 'Annahme/Korrektur: Kerne folgen denselben Höhenreihen und Faltflächen wie die Schaleninnenhaut; 6% radialer Abstand zur Innenhaut verhindert Durchdringungen. Knie-Untersteg und Knöchel-Fuß-Link beginnen am jeweiligen oberen Schalenrand. Schalen-Außenkonturen, Wandstärken, Frontanker und Fußhöhe unverändert.',
    'foot_shell_revision': 'Gemessen: beide Seitenoriginale zeigen getrennte helle Zehen-, Spann- und Fersenschalen mit dunklem Mittelfuß/Fersenmittelfeld; Front setzt Fußhöhe und Standbreite. Annahme: vorhandene FOOT_ROWS-Außenhaut wird entlang f95/u133 (Zehe), f20..90/u127 (Spann) und f-18/u145 (Ferse) geteilt; 5mm f-Wand, 0.25mm umlaufender Montageabstand zum direkt konstruierten Kern. Spann f20 liegt vor der maximalen Seitennaht f15.36 bei u127 und lässt deren Struktursteg frei; Abweichung von gemessenen f8.43 rechts/f10.01 links somit11.57/9.99mm, ausdrücklich Montageannahme. Mittleres Fersenfenster folgt vorhandener Spannfeldbreite62..49. Kanonische Dreiecke vor Spiegelung/Innenumkehr; kein CSG-Rückimport, keine dunkle Auflage über Weißhaut. Sohle, FOOT_ROWS und Frontanker unverändert. Alle Teilungs-/Montagemaße sind Konstruktion, keine Bildabnahme.',
    'hip_housing_revision_1': {
        'kind': 'gemessen',
        'source': 'Beide4096px-Farborthos zeigen schräg/gerundet zulaufende obere dunkle Hüftgehäuse statt Rechteckblöcke. Unveränderter Frontmaßstab1924/3653 und gespiegelter Rücken: u1120(y1750) Front198.6..200.1/Back189.6..199.1; u1130(y1731)179.1..180.7/169.6..178.5; u1140(y1712)168.5..169.1/160.6..168.5; u1150(y1693)157..157/154.8..161.7mm äußere Halbbreite. Vorherige gerade Zylinder standen bisu1148 aufx212 und bis1152 aufx202.',
        'construction': {'kind': 'Annahme',
            'source': 'Bestehende Hüftteile erhalten stabile IDs und gemeinsame Achse f45/u1080. Zylindrischer Innenanschlussx82..160 mitr72, äußere45°-Gehäusefase bisx212/r20; Profilx82/r72,x160/r72,x212/r20 erhält alteGesamtausladung, f/u-Kreisprojektion undAnkerx142. Ringöffnungr45 undAußenradius68 erhalten; echte8mm-Wand normal zur konischenFacette, mittig aufx+r232 montiert. AxialerHalbversatz4*sqrt(1+sec(pi/32)^2) berücksichtigt32Facetten und ursprünglicheZylinderphase. Alle neuen Übergangsmaße sind Konstruktionsannahmen, keinePixeloptimierung. Seitenprojektion, andereGelenke, Schalen undFüße bleiben erhalten; neueBildabnahme separat erforderlich.'}},
    'profile_refinement': {
        'source': 'Gemessen 27.10.2026 an beiden unveränderten Ortho-Masken, nach Sichtung beider Farboriginale und GPUJob14579-Overlays. k=1924/3653; y_front=3876-u/k; y_right=y_front-7, y_left=y_front-5. f_right=(2150-x)*k; f_left=(x-1946)*k.',
        'knee_back_samples_mm': {'u': [620,625,643,660,680,710,750,772],
                                'right': [-52.7,-34.8,-32.1,-45.3,-51.1,-45.8,-16.9,-20.5],
                                'left': [-53.2,-34.8,-31.1,-44.8,-51.1,-45.8,-17.4,-20.5]},
        'knee_cap_front_samples_mm': {'u': [625,643], 'right': [132.2,140.1], 'left': [132.2,139.6]},
        'foot_samples_mm': {'u': [62,100,120,145,178],
                            'right_front': [185.4,174.9,148.5,91.6,66.9],
                            'left_front': [185.9,175.9,150.1,92.7,68.5],
                            'right_back': [-125.9,-117.5,-114.3,-107.4,-91.1],
                            'left_back': [-126.9,-119.6,-114.3,-108.5,-92.2]},
        'design': 'Annahme: gerundete gemeinsame f-Profile mit linearer Interpolation; echte 5mm-Knie-Rückschale, unveränderte x/u-Gliederkonturen, Gelenke und Sohle. Fuß u120 interpoliert die bisherige Frontkontur exakt. Knöchel-Fuß-Link f45 bei u178 liegt innerhalb der neuen Fußöffnung; f-2 bei u234 bleibt. Ehemaliger dunkler3mm-Spannbelag durch echten sichtbaren Kern ersetzt, siehe foot_shell_revision.',
        'limit': 'Frontboden u0 bleibt trotz Referenz-Seitenboden u49.5/50.6 bestehen; oberes Zehenvolumen kann deshalb das gesamte unterste Breitenband vergrößern. Kein bestandenes Bildkriterium behauptet.',
    },
}
PARTS = []
ANCHORS = {}


def _part(name, side_id, role, source, **shape):
    p = dict(id='legs_'+name+'_'+side_id, assembly='legs', role=role, bevel=0,
             provenance={'kind': 'Annahme', 'source': source}, **shape)
    PARTS.append(p)
    return p['id']


def _mirror_x(x, sign):
    return sign*x


def _shell(rows, sign, rear=False, wall=5, gap=10):
    """Five-point folded half-shell with explicit inner skin and closed rims.

    Rows: u, positive anatomical distance of centre, half-width, front, back.
    The f-offset is nominal wall thickness, as in the source limb_panel;
    side returns additionally inset3mm. It is genuine closed shell geometry.
    """
    outer, inner = [], []
    direction = -1 if rear else 1
    for u, xc, hw, front, back in rows:
        split = (front+back)/2
        extreme = back if rear else front
        seam = split+direction*gap/2
        cheek = extreme-direction*(abs(extreme-seam)*.24)
        fs = (seam, cheek, extreme, cheek, seam)
        xs = (-hw, -.72*hw, 0, .72*hw, hw)
        for f, dx in zip(fs,xs):
            outer.append([f,u,_mirror_x(xc+dx,sign)])
            inset = 3*(1 if dx>0 else -1 if dx<0 else 0)
            inner.append([f-direction*wall,u,_mirror_x(xc+dx-inset,sign)])
    faces = []
    n = len(outer)
    for j in range(len(rows)-1):
        for i in range(4):
            a = j*5+i
            faces.append([a,a+1,a+6,a+5])
    # Orient the complete volume in geom; inner winding is opposite outer.
    faces += [[n+i for i in reversed(face)] for face in faces[:]]
    boundary = list(range(5)) + [j*5+4 for j in range(1,len(rows))]
    boundary += list(range(n-2,n-6,-1)) + [j*5 for j in range(len(rows)-2,0,-1)]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        faces.append([b,a,n+a,n+b])
    vertices = outer+inner
    # surface deliberately preserves winding in geom; orient each mirrored
    # closed wall here. Author→world (x,-f,u) has negative determinant.
    def det(a,b,c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1])
                -a[1]*(b[0]*c[2]-b[2]*c[0])
                +a[2]*(b[0]*c[1]-b[1]*c[0]))
    author_volume = sum(det(vertices[face[0]],vertices[face[i]],vertices[face[i+1]])
                        for face in faces for i in range(1,len(face)-1))
    if author_volume > 0:
        faces = [list(reversed(face)) for face in faces]
    return dict(shape='surface', vertices=vertices, faces=faces, wall_mm=wall, seam_mm=gap)


def _core(rows, sign):
    rings=[]
    for u,xc,hw,front,back in rows:
        # Faceted octagon, reduced corners keep the folded shell returns clear.
        rings.append([[f,u,sign*(xc+dx)] for f,dx in (
            (back,-hw*.72),(back+(front-back)*.18,-hw),
            (front-(front-back)*.18,-hw),(front,-hw*.72),
            (front,hw*.72),(front-(front-back)*.18,hw),
            (back+(front-back)*.18,hw),(back,hw*.72))])
    return dict(shape='loft',rings=rings)


def _fitted_core(rows, sign):
    """Fit the dark substructure inside the actual folded shell cavity.

    An independently interpolated octagon can cut the folded cheeks even
    when its front/back extrema look smaller. Matching the shell's heights
    and inner folds keeps the complete core under both separate walls.
    The six-percent radial clearance is an authoring assumption, not an
    Ortho measurement; the seam remains open and its dark interior visible.
    """
    front = _shell(rows, sign)['vertices'][len(rows)*5:]
    back = _shell(rows, sign, rear=True)['vertices'][len(rows)*5:]
    rings = []
    for j, (u, xc, _, f, b) in enumerate(rows):
        center = [(f+b)/2, u, sign*xc]
        # The inner side-rim endpoints coincide (gap10, wall5); keep each
        # endpoint once so the closed ring contains no zero-length edges.
        ring = front[j*5:j*5+5] + list(reversed(back[j*5+1:j*5+4]))
        rings.append([[center[0]+.94*(v[0]-center[0]), u,
                       center[2]+.94*(v[2]-center[2])] for v in ring])
    return dict(shape='loft', rings=rings)


def _axle(name, side, sign, f,u,xc,half_width,r,role='graphite',r_in=None):
    a,b=sorted((sign*(xc-half_width),sign*(xc+half_width)))
    options=dict(shape='cyl',axis='x',c=[f,u],a0=a,a1=b,r=r,segs=32)
    if r_in is not None: options['r_in']=r_in
    return _part(name,side,role,'Gemessen: Front Gelenkzentren und Außenbreite; Annahme: runde Achse32 Segmente und Tiefe.',**options)


def _hip_joint(side, sign):
    """Existing bearing with a broad conical outer housing, not a flat block."""
    n = 32

    def ring(x, radius):
        return [[45+radius*math.cos(math.tau*i/n+math.pi/n),
                 1080+radius*math.sin(math.tau*i/n+math.pi/n), sign*x]
                for i in range(n)]

    source = 'Gemessen: gemeinsame Front-/Rücken-Hüftkontur; Konstruktion PROVENANCE.hip_housing_revision_1.'
    axis = _part('hip_axis', side, 'graphite', source, shape='loft',
                 rings=[ring(x, radius) for x, radius in ((82,72),(160,72),(212,20))])
    # Parallel conical faces have eight millimetres normal separation.
    # The regular32-gon facet has radial coefficient sec(pi/32), not1.
    half_axial = 4*math.sqrt(1+1/math.cos(math.pi/n)**2)
    section = ((45, half_axial), (68, half_axial),
               (68, -half_axial), (45, -half_axial))
    vertices = [point for radius, offset in section
                for point in ring(232-radius+offset, radius)]
    faces = [[j*n+i,j*n+(i+1)%n,((j+1)%4)*n+(i+1)%n,((j+1)%4)*n+i]
             for j in range(4) for i in range(n)]
    def det(a,b,c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1])
                -a[1]*(b[0]*c[2]-b[2]*c[0])
                +a[2]*(b[0]*c[1]-b[1]*c[0]))
    volume = sum(det(vertices[f[0]],vertices[f[i]],vertices[f[i+1]])
                 for f in faces for i in range(1,len(f)-1))
    if volume > 0:  # Author→world reverses orientation.
        faces = [list(reversed(face)) for face in faces]
    _part('hip_socket', side, 'dark_metal', source, shape='surface',
          vertices=vertices, faces=faces, wall_mm=8)
    return axis


# Digitized front envelope (rounded mm), side profile adjusted only where
# hands occlude the thigh. These are authoring parameters, not image masks.
THIGH_ROWS = [
    (772,180,68,137,-21),(805,178,75,145,-24),
    (900,161,94,163,-46),(970,153,102,167,-49),
    (1035,151,86,165,-51),(1072,150,69,151,-45),
]
SHIN_ROWS = [
    (275,239,62,65,-71),(305,236,65,72,-72),
    (400,220,86,91,-89),(500,207,106,114,-110),
    (542,204,108,106,-102),(585,198,92,96,-75),
    (620,193,77,130,-52),
]
FOOT_ROWS = [
    (30,259,108,184,-123),(62,258,108,185,-126),
    (100,255,102,175,-119),
    (120,255-4*20/45,102-8*20/45,149,-114),
    (145,251,94,92,-108),(178,246,78,68,-92),
]
KNEE_REAR_ROWS = [
    (620,194,50,0,-52),(625,194,50,0,-35),
    (643,194,53,0,-32),(660,194,53,0,-45),
    (680,194,53,0,-51),(710,194,50,0,-46),
    (750,192,48,0,-18),(772,180,50,0,-21),
]


def _foot_surface(vertices, faces, sign, wall=None):
    """Fix physical diagonals first, then reflect and orient the complete solid."""
    faces = [[face[0], face[i], face[i+1]]
             for face in faces for i in range(1, len(face)-1)]
    vertices = [[f,u,sign*x] for f,u,x in vertices]
    def det(a,b,c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1])
                -a[1]*(b[0]*c[2]-b[2]*c[0])
                +a[2]*(b[0]*c[1]-b[1]*c[0]))
    # Author -> world reverses handedness; derive rather than assume winding.
    if sum(det(vertices[a],vertices[b],vertices[c]) for a,b,c in faces) > 0:
        faces = [list(reversed(face)) for face in faces]
    result = dict(shape='surface', vertices=vertices, faces=faces)
    if wall is not None:
        result['wall_mm'] = wall
    return result


def _foot_domains():
    """Disjoint armor fields on the canonical +x skin: a*f+b*u+c*x+d >= 0."""
    lower = (251-49-(259-62))/115
    upper = (251+49-(259+62))/115
    li, ui = 259-62-lower*30, 259+62-upper*30
    return (
        [[(1,0,0,-95),(0,-1,0,133)]],
        [[(-1,0,0,-18),(0,1,0,-145)],
         [(-1,0,0,-18),(0,-1,0,145),(0,lower,-1,li)],
         [(-1,0,0,-18),(0,-1,0,145),(0,-upper,1,-ui)]],
        [[(1,0,0,-20),(-1,0,0,90),(0,1,0,-127)]],
    )


def _foot_distance(point, plane):
    return sum(a*b for a,b in zip(point,plane[:3]))+plane[3]


def _foot_clip(polygon, plane, positive=True):
    result = []
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        da, db = _foot_distance(a,plane), _foot_distance(b,plane)
        if not positive:
            da, db = -da, -db
        if da >= -1e-8:
            result.append(a)
        if (da < -1e-8) != (db < -1e-8):
            t = da/(da-db)
            result.append([x+t*(y-x) for x,y in zip(a,b)])
    clean = []
    for point in result:
        if not clean or max(abs(a-b) for a,b in zip(point,clean[-1])) > 1e-8:
            clean.append(point)
    if len(clean)>1 and max(abs(a-b) for a,b in zip(clean[0],clean[-1]))<1e-8:
        clean.pop()
    if len(clean)<3:
        return []
    normal = [sum(a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3]
                  for a,b in zip(clean,clean[1:]+clean[:1])) for i in range(3)]
    return clean if math.sqrt(sum(v*v for v in normal)) >= 1e-8 else []


def _foot_index(point, vertices, lookup):
    key = tuple(round(v,10) for v in point)
    if key not in lookup:
        lookup[key] = len(vertices)
        vertices.append(list(key))
    return lookup[key]


def _foot_skin(rear=False):
    # Only positions come from _shell: its side-specific quad winding must
    # never choose the diagonal of the nonplanar foot skin.
    vertices = _shell(FOOT_ROWS,1,rear)['vertices'][:len(FOOT_ROWS)*5]
    triangles = [[a,a+1,a+6] if k==0 else [a,a+6,a+5]
                 for j in range(len(FOOT_ROWS)-1) for i in range(4)
                 for a in [j*5+i] for k in range(2)]
    return vertices, triangles


def _foot_panel(sign, rear, domains):
    source, triangles = _foot_skin(rear)
    vertices, faces, lookup = [], [], {}
    for triangle in triangles:
        if len(domains)>1:
            # Adjacent heel fields form one plate. Split every source triangle
            # by every union plane first, so the u145 join and window corners
            # share identical edge subdivisions on both sides of the join.
            polygons = [[source[i] for i in triangle]]
            for plane in dict.fromkeys(p for domain in domains for p in domain):
                divided = []
                for polygon in polygons:
                    distances = [_foot_distance(v,plane) for v in polygon]
                    if min(distances)<-1e-8 and max(distances)>1e-8:
                        divided += [piece for positive in (True,False)
                                    if (piece:=_foot_clip(polygon,plane,positive))]
                    else:
                        divided.append(polygon)
                polygons = divided
            selected = []
            for polygon in polygons:
                center = [sum(v[i] for v in polygon)/len(polygon) for i in range(3)]
                if any(all(_foot_distance(center,p)>=-1e-7 for p in domain)
                       for domain in domains):
                    selected.append(polygon)
        else:
            polygon = [source[i] for i in triangle]
            for plane in domains[0]:
                polygon = _foot_clip(polygon,plane) if polygon else []
            selected = [polygon]
        for polygon in selected:
            ids = [_foot_index(p,vertices,lookup) for p in polygon]
            faces += [[ids[0],ids[i],ids[i+1]] for i in range(1,len(ids)-1)]
    n = len(vertices)
    vertices += [[f+(5 if rear else -5),u,x] for f,u,x in vertices[:]]
    outer = faces[:]
    faces += [[n+i for i in reversed(face)] for face in outer]
    edges = defaultdict(list)
    for face in outer:
        for a,b in zip(face,face[1:]+face[:1]):
            edges[tuple(sorted((a,b)))].append((a,b))
    for uses in edges.values():
        if len(uses)==1:
            a,b = uses[0]
            faces.append([b,a,n+a,n+b])
    return _foot_surface(vertices,faces,sign,wall=5)


def _foot_armor(sign):
    toe, heel, instep = _foot_domains()
    return (_foot_panel(sign,False,toe), _foot_panel(sign,True,heel),
            _foot_panel(sign,False,instep))


def _foot_cap(vertices, face):
    """Ear-clip a horizontal cap, retaining all shared boundary vertices."""
    points = [(vertices[i][0],vertices[i][2]) for i in face]
    area = sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))
    orientation = 1 if area>0 else -1
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def tolerance(a,b):
        # Rounded shared vertices can perturb a straight cap edge by ~1e-10mm.
        # Use the same linear precision as clipping, rather than treating that
        # perturbation as a physical ear and emitting a collapsed triangle.
        return 1e-8*max(1,math.hypot(b[0]-a[0],b[1]-a[1]))
    remaining, triangles = list(range(len(face))), []
    while len(remaining)>3:
        for at,i in enumerate(remaining):
            j,k = remaining[at-1],remaining[(at+1)%len(remaining)]
            if orientation*cross(points[j],points[i],points[k]) <= tolerance(points[j],points[k]):
                continue
            if any(all(orientation*cross(points[a],points[b],points[t])>=-tolerance(points[a],points[b])
                       for a,b in ((j,i),(i,k),(k,j)))
                   for t in remaining if t not in (j,i,k)):
                continue
            triangles.append([face[j],face[i],face[k]])
            remaining.pop(at)
            break
        else:
            raise ValueError('Fußkappe ist degeneriert oder selbstüberschneidend')
    return triangles+[[face[t] for t in remaining]]


def _foot_structure(sign):
    """Construct the recessed core boundary directly, without Boolean cuts.

    All skin triangles are partitioned by the same planes. Armor cells move
    5.25mm inward, adjacent dark cells stay on the original outside skin;
    explicit step walls connect their shared edges. Expanded armor domains
    leave a real .25mm assembly gap at the panel boundaries as well.
    """
    front, ft = _foot_skin()
    back, bt = _foot_skin(True)
    n = len(front)
    source = front+back
    faces = ft+[[n+i for i in reversed(t)] for t in bt]
    skin_count = len(ft)
    for j in range(len(FOOT_ROWS)-1):
        a,b = j*5,(j+1)*5
        faces += [[a,b,b+n],[a,b+n,a+n],
                  [a+4,a+n+4,b+n+4],[a+4,b+n+4,b+4]]
    toe, heel, instep = _foot_domains()
    domains = toe+instep+heel
    domains = [[(a,b,c,d+.25*math.sqrt(a*a+b*b+c*c)) for a,b,c,d in domain]
               for domain in domains]
    planes = list(dict.fromkeys(p for domain in domains for p in domain))
    vertices, lookup, original, original_lookup, cells = [], {}, [], {}, []
    for at, triangle in enumerate(faces):
        polygons = [[source[i] for i in triangle]]
        for plane in planes:
            divided = []
            for polygon in polygons:
                distances = [_foot_distance(v,plane) for v in polygon]
                if min(distances)<-1e-8 and max(distances)>1e-8:
                    divided += [piece for positive in (True,False)
                                if (piece:=_foot_clip(polygon,plane,positive))]
                else:
                    divided.append(polygon)
            polygons = divided
        for polygon in polygons:
            center = [sum(v[i] for v in polygon)/len(polygon) for i in range(3)]
            active = (domains[:2] if at<skin_count else
                      domains[2:] if at<2*skin_count else [])
            armored = any(all(_foot_distance(center,p)>=-1e-7 for p in domain)
                          for domain in active)
            offset = (-5.25 if at<skin_count else 5.25) if armored else 0
            oi = [_foot_index(v,original,original_lookup) for v in polygon]
            pi = [_foot_index([f+offset,u,x],vertices,lookup) for f,u,x in polygon]
            cells.append((oi,pi))
    edges, faces = defaultdict(list), []
    for original_ids, physical_ids in cells:
        faces += [[physical_ids[0],physical_ids[i],physical_ids[i+1]]
                  for i in range(1,len(physical_ids)-1)]
        for i in range(len(physical_ids)):
            j = (i+1)%len(physical_ids)
            edges[tuple(sorted((original_ids[i],original_ids[j])))].append(
                (physical_ids[i],physical_ids[j]))
    for uses in edges.values():
        if len(uses)==2:
            (a,b),(c,d) = uses
            if a!=d or b!=c:
                faces += [[b,a,d],[b,d,c]]
        elif len(uses)!=1:
            raise ValueError('Fußkern hat eine nichtmannigfaltige Teilungskante')
    physical_edges = defaultdict(list)
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):
            physical_edges[tuple(sorted((a,b)))].append((a,b))
    boundary = {a:b for uses in physical_edges.values() if len(uses)==1 for a,b in uses}
    while boundary:
        a = next(iter(boundary))
        loop, b = [a], boundary.pop(a)
        while b!=a:
            loop.append(b)
            b = boundary.pop(b)
        faces += _foot_cap(vertices,list(reversed(loop)))
    return _foot_surface(vertices,faces,sign)

for side, sign in (('r',-1),('l',1)):
    hip = _hip_joint(side,sign)
    _part('thigh_core',side,'graphite',PROVENANCE['core_fit'],
          **_fitted_core(THIGH_ROWS,sign))
    for rear in (False,True):
        _part('thigh_'+('rear' if rear else 'front')+'_shell',side,'shell',
              'Gemessen: Front x-Kontur y1840..2410, Seite im gemeinsamen Pixelmaßstab. Annahme: halbe Facettenschale, verdeckte obere Innenkante; '+PROVENANCE['shell_design'],
              **_shell(THIGH_ROWS,sign,rear))
    knee = _axle('knee_axis',side,sign,35,710,194,72,65)
    for edge in (-1,1):
        _axle('knee_ring_'+str(edge),side,sign,35,710,194+edge*77,6,58,'dark_metal',43)
        _axle('knee_disc_'+str(edge),side,sign,35,710,194+edge*84,3,41,'anodized')
    _part('knee_cap',side,'shell','Gemessen: Front Knieschild u625..770, Breite≈130mm; beide Seiten unterer Schildrand f132 bei u625 und f140 bei u643, PROVENANCE.profile_refinement. Annahme: Facetten und interpolierter oberer Übergang unverändert.',
          **_core([(625,194,45,132,72),(643,194,56,140,68),
                   (705,194,66,145,67),(766,190,53,129,69)],sign))
    _part('knee_lower_link',side,'graphite','Annahme: innerer Verbindungssteg oberhalb der Schienbeinschale u620..695; verdeckte Fortsetzung übernimmt der eingepasste Schienbeinkern. '+PROVENANCE['core_fit'],
          **_core([(620,194,53,105,-10),(640,194,53,105,-10),(695,194,49,93,-8)],sign))
    _part('knee_rear_shell',side,'graphite',
          'Gemessen: hintere Kniekontur beider registrierter Seiten; PROVENANCE.profile_refinement. Annahme: 5mm-Rückschale mit gerundeten Messwerten, innerhalb bestehender Frontkontur, unveränderte Gelenkachse.',
          **_shell(KNEE_REAR_ROWS,sign,rear=True))
    _part('shin_core',side,'graphite',PROVENANCE['core_fit'],
          **_fitted_core(SHIN_ROWS,sign))
    for rear in (False,True):
        _part('shin_'+('rear' if rear else 'front')+'_shell',side,'shell' if not rear else 'graphite',
              'Gemessen: Front Schienbeinkontur u275..620; Seite u275..620; '+PROVENANCE['shell_design'],
              **_shell(SHIN_ROWS,sign,rear))
    # Thin, folded black inset follows the forward panel; no emissive accents.
    _part('shin_inset',side,'graphite','Gemessen: schmaler dunkler Front-Einsatz u300..460; Annahme 3mm Auflage.',
          **_core([(299,239,27,74,71),(430,216,32,101,98),
                   (457,213,22,107,104)],sign))
    ankle = _axle('ankle_axis',side,sign,-30,234,240,65,47)
    for edge in (-1,1):
        _axle('ankle_ring_'+str(edge),side,sign,-30,234,240+edge*71,6,43,'dark_metal',30)
        _axle('ankle_disc_'+str(edge),side,sign,-30,234,240+edge*78,3,29,'anodized')
    _part('ankle_link',side,'graphite','Annahme: Knöchel-Fuß-Link oberhalb des Fußschalenrandes u178..234; unterhalb übernimmt der eingepasste Fußkern. '+PROVENANCE['core_fit'],
          **_core([(178,244,53,45,-66),(234,240,48,-2,-59)],sign))
    # Broad sole with independent front and side silhouettes, not a cuboid.
    _part('foot_sole',side,'graphite','Gemessen: Front Standbreite x≈147..370 je Fuß; Seite Ferse-129, Spitze191mm. Annahme: Sohlenkante.',
          shape='prism2',side=[[-123,0],[180,0],[188,18],[186,48],[167,66],[-113,66],[-129,39]],
          front=[[sign*x,u] for x,u in [(177,0),(339,0),(368,19),(370,49),(361,68),(155,68),(148,42),(151,18)]])
    _part('foot_core',side,'graphite',PROVENANCE['foot_shell_revision'],
          **_foot_structure(sign))
    for name, panel in zip(('toe','heel','instep'),_foot_armor(sign)):
        _part('foot_'+name+'_shell',side,'shell',PROVENANCE['foot_shell_revision'],**panel)
    for joint, at, part in [('Hip',[45,1080,sign*142],hip),('Knee',[35,710,sign*194],knee),('Ankle',[-30,234,sign*240],ankle)]:
        ANCHORS['Socket_'+joint+'_'+side.upper()] = {
            'at':at,'part':part,
            'source':'Gemessen: Front bei k1924/3653; Annahme f aus Seite; Konflikt Seiten-Gelenkhöhen siehe PROVENANCE.joint_conflict.'}
