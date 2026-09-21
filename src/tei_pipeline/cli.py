import argparse
from pathlib import Path

from .io import read_csv, write_csv
from .pca import fit_first_component
from .safety import scan_public_tree
from .transport import nearest_hub_distance
from .validation import validate_administrative_dongs


def _distance_command(args: argparse.Namespace) -> int:
    origins = read_csv(args.origins)
    hubs = read_csv(args.hubs)
    result = nearest_hub_distance(
        origins,
        hubs,
        origin_id=args.origin_id,
        origin_lon=args.origin_lon,
        origin_lat=args.origin_lat,
        hub_name=args.hub_name,
        hub_lon=args.hub_lon,
        hub_lat=args.hub_lat,
        passthrough=args.passthrough,
    )
    write_csv(result, args.output)
    print(f"wrote {len(result)} rows to {args.output}")
    return 0


def _pca_command(args: argparse.Namespace) -> int:
    frame = read_csv(args.input)
    result = fit_first_component(
        frame,
        args.features,
        score_scale=args.score_scale,
        name=args.output_column,
    )
    output = frame.copy()
    output[args.output_column] = result.scores
    write_csv(output, args.output)
    print(f"explained_variance_ratio={result.explained_variance_ratio:.6f}")
    for feature, loading in result.loadings.items():
        print(f"loading[{feature}]={loading:.6f}")
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    frame = read_csv(args.input)
    errors = validate_administrative_dongs(
        frame, key_columns=args.keys, expected_rows=args.expected_rows
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(frame)} unique administrative-dong rows")
    return 0


def _safety_command(args: argparse.Namespace) -> int:
    findings = scan_public_tree(args.path)
    if findings:
        for finding in findings:
            print(f"BLOCK: {finding.path}: {finding.reason}")
        return 1
    print(f"OK: no publication blockers found under {Path(args.path).resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tei-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    distance = subparsers.add_parser("nearest-hub", help="calculate nearest-hub distance")
    distance.add_argument("--origins", required=True)
    distance.add_argument("--hubs", required=True)
    distance.add_argument("--output", required=True)
    distance.add_argument("--origin-id", default="key")
    distance.add_argument("--origin-lon", default="longitude")
    distance.add_argument("--origin-lat", default="latitude")
    distance.add_argument("--hub-name", default="hub_name")
    distance.add_argument("--hub-lon", default="longitude")
    distance.add_argument("--hub-lat", default="latitude")
    distance.add_argument("--passthrough", nargs="*", default=[])
    distance.set_defaults(handler=_distance_command)

    pca = subparsers.add_parser("pca-axis", help="fit an axis's first principal component")
    pca.add_argument("--input", required=True)
    pca.add_argument("--output", required=True)
    pca.add_argument("--features", nargs="+", required=True)
    pca.add_argument("--score-scale", choices=("none", "zscore"), default="zscore")
    pca.add_argument("--output-column", default="PC1")
    pca.set_defaults(handler=_pca_command)

    validate = subparsers.add_parser("validate-admin", help="validate 426-dong key integrity")
    validate.add_argument("--input", required=True)
    validate.add_argument("--keys", nargs="+", default=["administrative_dong_code"])
    validate.add_argument("--expected-rows", type=int, default=426)
    validate.set_defaults(handler=_validate_command)

    safety = subparsers.add_parser("check-public", help="scan for publication blockers")
    safety.add_argument("path", nargs="?", default=".")
    safety.set_defaults(handler=_safety_command)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.handler(args))

