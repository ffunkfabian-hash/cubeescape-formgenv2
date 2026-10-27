"""Separate content-cached geometry, views, specs, prompts and HTML layout."""
from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass, field
import hashlib
import io
import json
from pathlib import Path
from typing import Mapping, Sequence

from . import versions
from .cache import Artifact, Result, canonical, file_hash, run_artifacts

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = Path.home() / "Library/Caches/CubeEscapeFormgen/artifacts"
FONT_PATH = ROOT / "docs/fonts/bfont-contours.json"
REGISTRY = {"R01": ROOT / "formgen/models/figures/r01_basic_robot.py",
            "W01": ROOT / "formgen/models/weapons/w01_auto_rifle.py",
            "KG02": ROOT / "tests/fixtures/KG02.geo.json",
            "VS02": ROOT / "tests/fixtures/VS02.geo.json"}
VIEWS = ("side_left", "side_right", "front", "back", "top", "bottom", "iso")
ORTHOS = VIEWS[:6]
SKINS = ("standard", "nacht", "polar", "kobalt")
SPECIAL_VIEWS = ("hero", "detail_trigger", "sight_iso", "sight_side", "exploded", "idle", "ready")
STAGES = ("geometry", "views", "specs", "prompts", "sheets", "previews", "geo", "viewer")


@dataclass(frozen=True)
class Stage:
    kind: str
    builder: str
    version_names: tuple[str, ...]
    folder: str
    extension: str
    params: dict = field(default_factory=dict)


DUMMY = Stage("dummy", "formgen.build:build_dummy", ("MODEL",), "dummy", ".json")


def source_hashes(path: Path, root: Path = ROOT) -> dict[str, str]:
    """Hash a source and its statically visible local Python imports without importing it."""
    root, path = Path(root).resolve(), Path(path).resolve()
    found = {}

    def visit(current):
        current = current.resolve()
        if str(current) in found:
            return
        found[str(current)] = file_hash(current)
        if current.name.endswith(".geo.json"):
            data = json.loads(current.read_bytes())
            for field in ("weapon_spec", "sight_spec"):
                reference = data.get("source", {}).get(field) or {}
                if reference.get("file"):
                    name = reference["file"]
                    if Path(name).name != name:
                        raise ValueError("Spec-Referenz muss ein lokaler Dateiname sein")
                    dependency = current.parent / name
                    if dependency.is_file():
                        visit(dependency)
                    else:
                        found[str(dependency)] = "missing"
        if current.suffix != ".py":
            return
        for node in ast.walk(ast.parse(current.read_bytes(), filename=str(current))):
            candidates = []
            if isinstance(node, ast.Import):
                candidates = [root.joinpath(*alias.name.split(".")) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = current.parent if node.level else root
                for _ in range(max(0, node.level - 1)):
                    base = base.parent
                module = base.joinpath(*(node.module or "").split("."))
                candidates = [module] + [module / alias.name for alias in node.names if alias.name != "*"]
            for candidate in candidates:
                for imported in (candidate.with_suffix(".py"), candidate / "__init__.py"):
                    if imported.is_file() and imported.resolve().is_relative_to(root):
                        visit(imported)

    visit(path)
    return found


def _check_sources(hashes: dict[str, str]) -> None:
    if any((Path(path).exists() if expected == "missing" else file_hash(Path(path)) != expected)
           for path, expected in hashes.items()):
        raise RuntimeError("Quelle wurde während des Baus geändert; erneut starten")


def build_geometry(artifact: Artifact) -> bytes:
    _check_sources(artifact.inputs["source_hashes"])
    path = Path(artifact.inputs["source_path"])
    if path.suffix == ".py":
        from . import geom, model
        document = geom.evaluate(model.load(path), **artifact.params)
    else:
        from . import geo
        document = geo.load(path)
    if document["info"]["id"] != artifact.model_id:
        raise ValueError(f"Modell-ID widerspricht Registry: {document['info']['id']} / {artifact.model_id}")
    _check_sources(artifact.inputs["source_hashes"])
    return canonical(document) + b"\n"


def _document(artifact: Artifact) -> dict:
    path = Path(artifact.inputs["geometry_path"])
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != artifact.source:
        raise RuntimeError("Geometrie wurde während des Baus geändert; erneut starten")
    return _attachments(json.loads(data),artifact.inputs.get("attachment_paths",{}))


def _attachments(document, paths):
    if paths:
        document["attachment_documents"]={}
    for sid,reference in paths.items():
        path=Path(reference["path"])
        if file_hash(path)!=reference["sha256"]:
            raise RuntimeError("Waffenanhang wurde während des Baus geändert")
        document["attachment_documents"][sid]=json.loads(path.read_bytes())
    return document


def _matches(part, words) -> bool:
    text = " ".join(str(part.get(key, "")) for key in ("id", "assembly", "label", "name")).lower()
    return any(word in text for word in words)


def _sight(part) -> bool:
    assembly = str(part.get("assembly", "")).lower()
    return "sight" in assembly or "visier" in assembly or str(part.get("id", "")).startswith("sight_")


def _bounds(parts):
    points = [point for part in parts for point in part["mesh"]["vertices"]]
    if not points:
        raise ValueError("Ansicht besitzt keine Geometrie")
    return [[min(point[i] for point in points) for i in range(3)],
            [max(point[i] for point in points) for i in range(3)]]


def select_document(document: dict, selection: str) -> dict:
    """Select/transform already evaluated meshes, never reconstruct or render them."""
    result = copy.deepcopy(document)
    parts = result["parts"]
    if selection == "hero" and document["info"]["kind"] == "weapon":
        parts = [part for part in parts if not _sight(part)]
    elif selection in ("sight_iso", "sight_side"):
        parts = [part for part in parts if _sight(part)]
    elif selection.startswith("assembly_"):
        assembly = selection.removeprefix("assembly_")
        parts = [part for part in parts if part.get("assembly") == assembly]
    elif selection == "detail_trigger":
        triggers = [part for part in parts if _matches(part, ("trigger", "abzug"))]
        low, high = _bounds(triggers)
        center = [(a + b) / 2 for a, b in zip(low, high)]
        parts = [part for part in parts if all(_bounds([part])[0][axis] <= center[axis] + .075
                                             and _bounds([part])[1][axis] >= center[axis] - .075
                                             for axis in range(3))]
        result["view_crop"] = {"center": center, "span_m": .15}
    elif selection == "exploded":
        vectors = {assembly["id"]: assembly.get("explode") for assembly in result["assemblies"]}
        if not any(vectors.values()):
            raise ValueError("Explosionsansicht benötigt dokumentierte assembly.explode-Vektoren")
        offsets = {}
        for part in parts:
            f, u, x = vectors.get(part.get("assembly")) or (0, 0, 0)
            offset = (x / 1000, -f / 1000, u / 1000)
            offsets[part["id"]] = offset
            part["mesh"]["vertices"] = [[value + offset[i] for i, value in enumerate(point)]
                                        for point in part["mesh"]["vertices"]]
        for anchor in result.get("anchors", {}).values():
            if anchor.get("part") in offsets and "position_m" in anchor:
                anchor["position_m"] = [value + offsets[anchor["part"]][i]
                                         for i, value in enumerate(anchor["position_m"])]
    elif selection in ("idle", "ready"):
        pose = result.get("poses", {}).get(selection)
        if not isinstance(pose, dict) or "part_transforms" not in pose:
            raise ValueError(f"Pose {selection} benötigt ausgewertete part_transforms (4×4, Meter)")
        for part in parts:
            matrix = pose["part_transforms"].get(part["id"])
            if matrix is not None:
                if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
                    raise ValueError("Posentransformation muss 4×4 sein")
                part["mesh"]["vertices"] = [[sum(matrix[i][j] * point[j] for j in range(3)) + matrix[i][3]
                                            for i in range(3)] for point in part["mesh"]["vertices"]]
        for anchor in result.get("anchors", {}).values():
            matrix = pose["part_transforms"].get(anchor.get("part"))
            if matrix is not None and "position_m" in anchor:
                point = anchor["position_m"]
                anchor["position_m"] = [sum(matrix[i][j] * point[j] for j in range(3)) + matrix[i][3]
                                         for i in range(3)]
    if selection in ("idle", "ready"):
        for attachment in document.get("poses",{}).get(selection,{}).get("attachments",[]):
            from .models.figures.r01_poses import evaluated_attachment
            sid=attachment["model"]
            if sid not in document.get("attachment_documents",{}):
                raise ValueError(f"Pose {selection}: ausgewertete Anhanggeometrie {sid} fehlt")
            placed=evaluated_attachment(document["attachment_documents"][sid],document,selection)
            for part in placed["parts"]:
                part["id"]=sid+"/"+part["id"]
                part["assembly"]="held_weapon"
            parts.extend(placed["parts"])
            result["assemblies"].append({"id":"held_weapon","de":"W01 in rechter Hand"})
            for name,anchor in placed["anchors"].items():
                anchor["part"]=sid+"/"+anchor["part"] if anchor.get("part") else None
                result["anchors"]["Socket_Held_"+sid+"_"+name.removeprefix("Socket_")]=anchor
    result["parts"] = parts
    result["bounds_m"] = _bounds(parts)
    for part in parts:
        part["bounds_m"] = _bounds([part])
    ids = {part["id"] for part in parts}
    result["anchors"] = {name: anchor for name, anchor in result.get("anchors", {}).items()
                         if anchor.get("part") is None or anchor.get("part") in ids}
    result["counts"] = {"parts": len(parts), "vertices": sum(len(p["mesh"]["vertices"]) for p in parts),
                        "faces": sum(len(p["mesh"]["faces"]) for p in parts),
                        "triangles": sum(len(face) - 2 for p in parts for face in p["mesh"]["faces"])}
    return result


def view_names(document: dict) -> list[str]:
    if document["info"]["kind"] == "figure":
        names = ["front", "side_left", "side_right", "back", "iso"]
        if any(assembly.get("explode") for assembly in document["assemblies"]):
            names.append("exploded")
        names += [pose for pose in ("idle", "ready") if pose in document.get("poses", {})]
        names += [f"assembly_{assembly['id']}" for assembly in document["assemblies"]]
        return names
    names = ["iso" if document["info"]["kind"] == "sight" else "hero", *ORTHOS]
    if any(_matches(part, ("trigger", "abzug")) for part in document["parts"]):
        names.append("detail_trigger")
    if any(_sight(part) for part in document["parts"]):
        names += ["sight_iso", "sight_side"]
    return names + [f"skin_{skin}" for skin in SKINS]


def view_parameters(document: dict, name: str, *, width=None, height=None,
                    skin="standard", bg="mid") -> dict:
    is_figure = document["info"]["kind"] == "figure"
    dimensions = (960, 960) if is_figure else (960, 480)
    camera = name if name in VIEWS else "iso"
    framing_views = list(ORTHOS) if name in ORTHOS else [camera]
    if name == "hero":
        dimensions = (1440, 960)
    elif name.startswith("skin_"):
        dimensions, skin = (960, 640), name.removeprefix("skin_")
    elif name in ("sight_side", "detail_trigger"):
        camera, framing_views = "side_left", ["side_left"]
    elif name == "iso":
        dimensions = (960, 960) if is_figure else (960, 640)
    params = {"view": camera, "selection": name, "width": width or dimensions[0],
            "height": height or dimensions[1], "skin": skin, "bg": bg,
            "skin_sha": file_hash(ROOT / "skins.toml"), "framing_views": framing_views}
    if document.get('source_geo', {}).get('format') == 'cubeescape-design/geometry-spec':
        params['legacy_catalog_sha'] = file_hash(ROOT/'docs/textures/catalog.json')
    return params


def build_view(artifact: Artifact) -> bytes:
    from . import raster
    from PIL.PngImagePlugin import PngInfo
    if file_hash(ROOT / "skins.toml") != artifact.params["skin_sha"]:
        raise RuntimeError("Skin wurde während des Baus geändert; erneut starten")
    if artifact.params.get('legacy_catalog_sha') is not None and file_hash(ROOT/'docs/textures/catalog.json') != artifact.params['legacy_catalog_sha']:
        raise RuntimeError('Legacy-Finishkatalog wurde während des Baus geändert; erneut starten')
    document = select_document(_document(artifact), artifact.params["selection"])
    options = {key: artifact.params[key] for key in ("view", "width", "height", "skin", "bg")}
    framing = raster.framing(document, views=artifact.params["framing_views"],
                             width=options["width"], height=options["height"])
    if "view_crop" in document:
        framing = {"center": document["view_crop"]["center"],
                   "scale": min(options["width"], options["height"]) * .84 / document["view_crop"]["span_m"]}
    image = raster.render(document, **options, **framing)
    buffer = io.BytesIO()
    metadata = dict(image.info, width=image.width, height=image.height)
    pnginfo = PngInfo()
    pnginfo.add_text("formgen_meta", canonical(metadata).decode("utf-8"))
    image.save(buffer, format="PNG", pnginfo=pnginfo)
    return buffer.getvalue()


def build_preview(artifact: Artifact) -> bytes:
    from . import raster
    if file_hash(ROOT / "skins.toml") != artifact.params["skin_sha"]:
        raise RuntimeError("Skin wurde während des Baus geändert; erneut starten")
    if artifact.params.get('legacy_catalog_sha') is not None and file_hash(ROOT/'docs/textures/catalog.json') != artifact.params['legacy_catalog_sha']:
        raise RuntimeError('Legacy-Finishkatalog wurde während des Baus geändert; erneut starten')
    document = select_document(_document(artifact), artifact.params["selection"])
    options = {key: artifact.params[key] for key in ("view", "width", "height", "skin", "bg")}
    image = raster.render(document, **options)
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


def build_spec(artifact: Artifact) -> bytes:
    from . import spec
    if file_hash(ROOT / "skins.toml") != artifact.params["skin_sha"]:
        raise RuntimeError("Skin wurde während des Baus geändert; erneut starten")
    document = _document(artifact)
    if document.get("source_spec"):
        field="sight_spec" if document["info"]["kind"]=="sight" else "weapon_spec"
        reference=document["source_geo"]["source"][field]
        path=Path(document["source"]["path"]).parent/reference["file"]
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=reference["sha256"] or json.loads(raw)!=document["source_spec"]:
            raise ValueError("Original-Spec wurde seit dem Geo-Import geändert")
        # Exact original bytes preserve nested sight-spec references, too.
        return raw
    return canonical(spec.build(document)) + b"\n"


def build_geo(artifact: Artifact) -> bytes:
    from . import geo
    spec_path=Path(artifact.inputs["spec_path"])
    for path,digest in artifact.inputs["spec_hashes"].items():
        if file_hash(Path(path)) != digest:
            raise RuntimeError("Spec-Quelle wurde während des Geo-Exports geändert")
    return canonical(geo.export(_document(artifact), spec_path)) + b"\n"


def build_prompts(artifact: Artifact) -> bytes:
    from . import prompts
    return canonical(prompts.build(_document(artifact))) + b"\n"


def view_metadata(paths):
    from PIL import Image
    metadata = {}
    for view, path in paths.items():
        with Image.open(path) as image:
            info = json.loads(image.info.get("formgen_meta", "{}"))
            boxes = list(info.get("boxes", {}).values())
            reference = {"horizontal": [], "vertical": []}
            if boxes:
                reference = {"horizontal": [min(box[1] for box in boxes), max(box[3] for box in boxes)],
                             "vertical": [min(box[0] for box in boxes), max(box[2] for box in boxes)]}
            metadata[view] = {"width": image.width, "height": image.height,
                              "labels": [{"label": label, "x": at[0], "y": at[1]}
                                         for label, at in info.get("anchors", {}).items()],
                              "reference_lines": reference,
                              "scale_px_m": info.get("framing", {}).get("scale")}
    return metadata


def build_sheet(artifact: Artifact) -> str:
    from . import sheet
    if file_hash(ROOT / "skins.toml") != artifact.params["skin_sha"]:
        raise RuntimeError("Skin wurde während des Baus geändert; erneut starten")
    metadata=view_metadata(artifact.inputs["view_paths"])
    if metadata != artifact.params["view_metadata"]:
        raise RuntimeError("Ansichtsmetadaten wurden während des Blattbaus geändert")
    views=dict(artifact.params["views"])
    views["_meta"]=metadata
    return sheet.build(_document(artifact),views)


def geometry_plan(sources: Mapping[str, Path]) -> list[Artifact]:
    artifacts = []
    for model_id, path in sources.items():
        path = Path(path).resolve()
        hashes = source_hashes(path)
        if path.suffix == ".py":
            hashes[str(FONT_PATH)] = file_hash(FONT_PATH)
        # Relative dependency names make relocation of the repository harmless.
        relative = {str(Path(name).relative_to(ROOT)) if Path(name).is_relative_to(ROOT)
                    else str(Path(name).name): digest for name, digest in hashes.items()}
        source = hashlib.sha256(canonical(relative)).hexdigest()
        names = ("MODEL", "GEOM") if path.suffix == ".py" else ("GEO",)
        params = {"booleans": True, "bevels": True} if path.suffix == ".py" else {}
        artifacts.append(Artifact(model_id, "geometry", source, params,
                                  {name: getattr(versions, name) for name in names},
                                  f"geometry/{model_id}.json", "formgen.build:build_geometry",
                                  {"source_path": str(path), "source_hashes": hashes}))
    return artifacts


def downstream_plan(ids: Sequence[str], out: Path, kind: str, *, views=None,
                    width=None, height=None, skin="standard", bg="mid") -> list[Artifact]:
    artifacts = []
    for model_id in ids:
        geometry_path = Path(out).resolve() / "geometry" / f"{model_id}.json"
        source = file_hash(geometry_path)
        document = json.loads(geometry_path.read_bytes())
        names = view_names(document) if views is None else list(views)
        inputs = {"geometry_path": str(geometry_path)}
        if kind == "views":
            for view in names:
                view_inputs=dict(inputs)
                references=document.get("poses",{}).get(view,{}).get("attachments",[])
                paths={ref["model"]:{"path":str(Path(out).resolve()/"geometry"/(ref["model"]+".json")),
                                     "sha256":file_hash(Path(out)/"geometry"/(ref["model"]+".json"))}
                       for ref in references}
                view_document=_attachments(copy.deepcopy(document),paths)
                params = view_parameters(view_document, view, width=width, height=height, skin=skin, bg=bg)
                if paths:
                    view_inputs["attachment_paths"]=paths
                    params["attachment_hashes"]={sid:ref["sha256"] for sid,ref in paths.items()}
                    params["pose_adapter"]=1
                artifacts.append(Artifact(model_id, kind, source, params, {"RASTER": versions.RASTER},
                                          f"views/{model_id}/{view}.png", "formgen.build:build_view", view_inputs))
        elif kind == "previews":
            params = view_parameters(document, "hero" if document["info"]["kind"] != "figure" else "iso",
                                     width=width or 720, height=height or 480, skin=skin, bg=bg)
            artifacts.append(Artifact(model_id, kind, source, params, {"RASTER": versions.RASTER},
                                      f"previews/{model_id}.webp", "formgen.build:build_preview", inputs))
        else:
            params = {}
            if kind == "sheets":
                params["skin_sha"] = file_hash(ROOT / "skins.toml")
                params["views"] = {view: f"../views/{model_id}/{view}.png" for view in names}
                inputs["view_paths"] = {view: str(Path(out).resolve() / "views" / model_id / f"{view}.png")
                                        for view in names}
                paths=inputs["view_paths"]
                params["view_metadata"]=(view_metadata(paths) if all(Path(p).is_file() for p in paths.values()) else None)
            elif kind == "geo":
                spec_path = Path(out).resolve() / "specs" / f"{model_id}.spec.json"
                spec_paths = [spec_path]
                for field in ("weapon_spec", "sight_spec"):
                    ref=(document.get("source_geo",{}).get("source",{}).get(field) or {})
                    if ref.get("file"):
                        dependency=spec_path.parent / ref["file"]
                        if dependency not in spec_paths: spec_paths.append(dependency)
                inputs["spec_path"]=str(spec_path)
                inputs["spec_hashes"]={str(p):file_hash(p) for p in spec_paths}
                params["spec_hashes"]={Path(k).name:v for k,v in inputs["spec_hashes"].items()}
            elif kind == "specs":
                params["skin_sha"] = file_hash(ROOT / "skins.toml")
            version, suffix, builder = {"specs": ("SPEC", ".spec.json", "build_spec"),
                                        "prompts": ("PROMPTS", ".prompts.json", "build_prompts"),
                                        "sheets": ("SHEET", ".dc.html", "build_sheet"),
                                        "geo": ("GEO", ".geo.json", "build_geo")}[kind]
            component_versions = {version: getattr(versions, version)}
            if kind == "prompts":
                component_versions["SPEC"] = versions.SPEC
            elif kind == "sheets":
                component_versions.update(SPEC=versions.SPEC, PROMPTS=versions.PROMPTS)
            artifacts.append(Artifact(model_id, kind, source, params, component_versions,
                                      f"{kind}/{model_id}{suffix}", f"formgen.build:{builder}", inputs))
    return artifacts


def build_asset(artifact: Artifact) -> bytes:
    data=Path(artifact.inputs["path"]).read_bytes()
    if hashlib.sha256(data).hexdigest()!=artifact.source:
        raise RuntimeError("Statische Ressource wurde während des Baus geändert")
    return data


def font_plan():
    return [Artifact("FONTS","fonts",file_hash(path),{}, {},
                     "fonts/"+path.name,"formgen.build:build_asset",{"path":str(path)})
            for path in sorted((ROOT/"formgen/assets/fonts").iterdir()) if path.is_file()]


def build_dummy(artifact: Artifact) -> bytes:
    """An actual cache proof, deliberately independent of geometry and raster imports."""
    source = Path(artifact.inputs["source_path"]).read_bytes()
    if hashlib.sha256(source).hexdigest() != artifact.source:
        raise RuntimeError("Modellquelle wurde während des Baus geändert; erneut starten")
    return canonical({"model": artifact.model_id, "source": artifact.source,
                      "kind": artifact.kind, "params": artifact.params,
                      "versions": artifact.versions, "source_bytes": len(source)}) + b"\n"


def plan(sources: Mapping[str, Path], stages: Sequence[Stage] = (DUMMY,)) -> list[Artifact]:
    artifacts = []
    for model_id, path in sources.items():
        if not model_id or Path(model_id).name != model_id or model_id in (".", ".."):
            raise ValueError(f"Ungültige Modell-ID: {model_id!r}")
        path = Path(path).resolve()
        source = file_hash(path)
        for stage in stages:
            artifacts.append(Artifact(model_id, stage.kind, source, dict(stage.params),
                                      {name: getattr(versions, name) for name in stage.version_names},
                                      f"{stage.folder}/{model_id}{stage.extension}", stage.builder,
                                      {"source_path": str(path)}))
    return artifacts


def summary(results: Sequence[Result]) -> str:
    built = sum(result.built for result in results)
    return f"{built} gebaut · {len(results) - built} aus dem Cache"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="Modell-IDs; ohne Auswahl die vier Piloten R01, W01, KG02, VS02")
    parser.add_argument("--dummy", action="store_true", help="Nur MINI-Cacheprobe ohne Geometrie/Bilder")
    parser.add_argument("--legacy-dir", type=Path, help="Vorbereitete Geo-Bibliothek für zusätzliche einzelne IDs; ohne IDs bleiben die vier Piloten")
    parser.add_argument("--out", type=Path, default=ROOT / "out")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--force-views", action="store_true")
    parser.add_argument("--force-sheets", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--stages", help="Kommagetrennt: geometry,views,specs,prompts,sheets,previews,geo,viewer")
    parser.add_argument("--views", help="Kameras/Blattansichten, kommagetrennt; Standard passend zum Modell")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--skin", default="standard")
    parser.add_argument("--bg", default="mid")
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs muss mindestens 1 sein")
    args.registry = dict(REGISTRY)
    if args.legacy_dir is not None:
        if args.dummy:
            parser.error("--legacy-dir und --dummy sind nicht kombinierbar")
        if not args.legacy_dir.is_dir():
            parser.error("--legacy-dir muss ein vorhandener Ordner sein")
        for path in sorted(args.legacy_dir.glob("*.geo.json")):
            model_id = path.name.removesuffix(".geo.json")
            if model_id in ("W01", "R01"):
                parser.error(f"Legacy-Bibliothek darf natives Modell {model_id} nicht ersetzen")
            args.registry[model_id] = path.resolve()
    available = {"MINI"} if args.dummy else set(args.registry)
    if any(model_id not in available for model_id in args.ids):
        parser.error(f"Unbekannte Modell-ID (verfügbar: {', '.join(sorted(available))})")
    if len(args.ids) != len(set(args.ids)):
        parser.error("Modell-ID mehrfach ausgewählt")
    if any(value is not None and value < 1 for value in (args.width, args.height)):
        parser.error("--width und --height müssen positiv sein")
    args.views = list(dict.fromkeys(args.views.split(","))) if args.views is not None else None
    if args.views is not None and any(view not in VIEWS + SPECIAL_VIEWS + tuple(f"skin_{skin}" for skin in SKINS)
                                     and not view.startswith("assembly_") for view in args.views):
        parser.error("Unbekannte Ansicht")
    if args.dummy and args.stages:
        parser.error("--dummy und --stages sind nicht kombinierbar")
    if args.stages:
        selected = args.stages.split(",")
        if any(stage not in STAGES for stage in selected):
            parser.error("Unbekannte Bau-Stufe")
    else:
        selected = list(STAGES)
    if "geo" in selected:
        selected.append("specs")
    if "sheets" in selected:
        selected.append("views")
    args.stages = [kind for kind in STAGES if kind in selected or kind == "geometry"]
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    force_kinds = {kind for flag, kind in ((args.force_views, "views"),
                                          (args.force_views, "previews"),
                                          (args.force_sheets, "sheets")) if flag}
    options = dict(jobs=args.jobs, force=args.force, force_kinds=force_kinds)
    if args.dummy:
        results = run_artifacts(plan({"MINI": ROOT / "formgen/models/mini.py"}),
                                args.out, args.cache, **options)
    else:
        sources = {model_id: args.registry[model_id] for model_id in (args.ids or REGISTRY)}
        geometry_sources=dict(sources)
        spec_ids = list(sources)
        if "specs" in args.stages:
            for path in sources.values():
                if path.name.endswith(".geo.json"):
                    reference = json.loads(path.read_bytes()).get("source", {}).get("sight_spec") or {}
                    if reference.get("file"):
                        dependency = reference["file"].removesuffix(".spec.json")
                        if dependency not in spec_ids:
                            if dependency not in args.registry:
                                raise ValueError(f"Visier-Spec benötigt registriertes Geo: {dependency}")
                            geometry_sources[dependency] = args.registry[dependency]
                            spec_ids.append(dependency)
        if "R01" in sources: geometry_sources.setdefault("W01",REGISTRY["W01"])
        results = run_artifacts(geometry_plan(geometry_sources), args.out, args.cache, **options)
        if "sheets" in args.stages:
            results.extend(run_artifacts(font_plan(),args.out,args.cache,**options))
        for kind in args.stages:
            if kind == "viewer":
                from . import viewer
                results.extend(viewer.build(args.out,args.cache))
            elif kind != "geometry":
                artifacts = downstream_plan(spec_ids if kind == "specs" else list(sources), args.out, kind, views=args.views,
                                            width=args.width, height=args.height, skin=args.skin, bg=args.bg)
                results.extend(run_artifacts(artifacts, args.out, args.cache, **options))
    print(summary(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
