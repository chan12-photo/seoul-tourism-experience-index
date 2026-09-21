"""Build public portfolio images from locally held final project outputs.

The script reads restricted/local data only to validate published aggregate results.
It writes PNG figures, never row-level data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

BACKGROUND = "#F6F8FB"
INK = "#172033"
MUTED = "#647184"
GRID = "#D8DEE8"
WHITE = "#FFFFFF"
BLUE = "#3568E8"
TEAL = "#138A7A"
ORANGE = "#D98616"
CORAL = "#D95C5C"
PURPLE = "#7657D5"

FINAL_Y = "Y_최종(중간발표이후)"
AXIS_SCORES = ["A_최종", "B_최종", "C_최종", "D_최종"]
CANDIDATES = {
    ("관악구", "중앙동"): {"A_최종": 2.75},
    ("강북구", "우이동"): {"C_최종": 3.04, "D_최종": 1.56},
    ("강동구", "상일2동"): {"B_최종": 3.58},
}


def configure_font() -> None:
    candidates = [
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/Library/Fonts/NotoSansCJKkr-Regular.otf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for path in candidates:
        if path.exists():
            family = font_manager.FontProperties(fname=path).get_name()
            plt.rcParams["font.family"] = family
            break
    plt.rcParams["axes.unicode_minus"] = False


def read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode CSV: {path}")


def numeric_column(frame: pd.DataFrame, column: str, *, minimum: float | None = None) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError(f"{column} must contain finite numeric values")
    if minimum is not None and (values < minimum).any():
        raise ValueError(f"{column} must not contain values below {minimum}")
    return values


def integer_sum(frame: pd.DataFrame, column: str) -> int:
    values = numeric_column(frame, column, minimum=0.0)
    if not np.allclose(values, np.round(values)):
        raise ValueError(f"{column} must contain whole-number counts")
    return int(values.sum())


def load_final_results(path: Path) -> tuple[pd.DataFrame, dict[str, float | int]]:
    frame = read_csv(path)
    required = {"자치구", "행정동명", FINAL_Y, *AXIS_SCORES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Final result is missing columns: {missing}")
    if len(frame) != 426:
        raise ValueError(f"Expected 426 administrative dongs, found {len(frame)}")

    result = frame.copy()
    keys = result[["자치구", "행정동명"]]
    if (
        keys.isna().any().any()
        or keys.astype("string").apply(lambda x: x.str.strip().eq("")).any().any()
    ):
        raise ValueError("Administrative-dong keys must not be missing or blank")
    if keys.duplicated().any():
        raise ValueError("Administrative-dong keys must be unique")

    for column in AXIS_SCORES:
        result[column] = numeric_column(result, column)
    result["supply"] = result[AXIS_SCORES].mean(axis=1)
    result["demand"] = numeric_column(result, FINAL_Y)
    x_median = float(result["supply"].median())
    y_median = float(result["demand"].median())
    result["quadrant"] = np.select(
        [
            (result["supply"] >= x_median) & (result["demand"] >= y_median),
            (result["supply"] < x_median) & (result["demand"] >= y_median),
            (result["supply"] < x_median) & (result["demand"] < y_median),
        ],
        ["Q1", "Q2", "Q3"],
        default="Q4",
    )
    counts = result["quadrant"].value_counts().to_dict()
    expected_counts = {"Q1": 164, "Q2": 49, "Q3": 164, "Q4": 49}
    if counts != expected_counts:
        raise ValueError(f"Unexpected quadrant counts: {counts}")

    correlation = float(result["supply"].corr(result["demand"]))
    if not np.isclose(correlation, 0.6759686489, atol=1e-9):
        raise ValueError(f"Unexpected supply-demand correlation: {correlation}")

    for (district, dong), expected_scores in CANDIDATES.items():
        candidate = result.loc[(result["자치구"] == district) & (result["행정동명"] == dong)]
        if len(candidate) != 1:
            raise ValueError(
                f"Expected one candidate row for {district} {dong}, found {len(candidate)}"
            )
        row = candidate.iloc[0]
        if row["quadrant"] != "Q4":
            raise ValueError(f"Expected {district} {dong} in Q4, found {row['quadrant']}")
        for column, expected in expected_scores.items():
            if not np.isclose(float(row[column]), expected, atol=0.005):
                raise ValueError(
                    f"Unexpected {column} for {district} {dong}: {float(row[column]):.4f}"
                )

    stats: dict[str, float | int] = {
        "rows": len(result),
        "correlation": correlation,
        "x_median": x_median,
        "y_median": y_median,
        "q4_count": counts["Q4"],
    }
    return result, stats


def load_cd_stats(archive_root: Path) -> dict[str, float | int | dict[str, int]]:
    output = archive_root / "04_output"
    culture = output / "C_axis"

    c1 = read_csv(culture / "C1_culture_space_count_by_hdong.csv")
    c2 = read_csv(culture / "C2_tourist_attraction_count_by_hdong.csv")
    c3 = read_csv(culture / "C3_content_diversity_by_hdong.csv")
    heritage = read_csv(culture / "C4_heritage_count_by_hdong_final_log.csv")
    subway = read_csv(output / "D1_subway_count_by_hdong.csv")
    distance = read_csv(output / "D3_distance_accessibility_by_hdong.csv")
    bus = read_csv(output / "D4_bus_stop_count_by_hdong.csv")

    frames = [c1, c2, c3, heritage, subway, distance, bus]
    if any(len(frame) != 426 for frame in frames):
        raise ValueError("Every C/D administrative-dong output must contain 426 rows")

    stats: dict[str, float | int | dict[str, int]] = {
        "culture_mapped": integer_sum(c1, "C1_culture_space_count"),
        "tourist_valid": integer_sum(c2, "C2_tourist_attraction_count"),
        "tourist_classified": integer_sum(c3, "C3_total_classified_count"),
        "tourist_support": integer_sum(c3, "C3_support_excluded_count"),
        "tourist_unknown": integer_sum(c3, "C3_unknown_count"),
        "heritage_counted": integer_sum(heritage, "C4_heritage_count"),
        "subway_count": integer_sum(subway, "D1_subway_count"),
        "bus_count": integer_sum(bus, "D4_bus_stop_count"),
        "distance_min": float(numeric_column(distance, "D3_min_distance_km", minimum=0.0).min()),
        "distance_max": float(numeric_column(distance, "D3_min_distance_km", minimum=0.0).max()),
        "distance_mean": float(numeric_column(distance, "D3_min_distance_km", minimum=0.0).mean()),
        "nearest_hubs": {
            str(key): int(value)
            for key, value in distance["nearest_hub_by_distance"].value_counts().items()
        },
    }
    expected = {
        "culture_mapped": 1051,
        "tourist_valid": 1009,
        "tourist_classified": 696,
        "tourist_support": 173,
        "tourist_unknown": 140,
        "heritage_counted": 271,
        "subway_count": 333,
        "bus_count": 11222,
    }
    for key, value in expected.items():
        if stats[key] != value:
            raise ValueError(f"Unexpected {key}: {stats[key]}")

    expected_distances = {
        "distance_min": 0.291316,
        "distance_mean": 6.540053,
        "distance_max": 15.412902,
    }
    for key, expected_value in expected_distances.items():
        if not np.isclose(float(stats[key]), expected_value, atol=1e-6):
            raise ValueError(f"Unexpected {key}: {stats[key]}")

    expected_hubs = {"명동역": 140, "홍대입구역": 132, "강남역": 124, "서울역": 30}
    if stats["nearest_hubs"] != expected_hubs:
        raise ValueError(f"Unexpected nearest-hub distribution: {stats['nearest_hubs']}")
    return stats


def add_round_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: str = WHITE,
    edgecolor: str = GRID,
    radius: float = 0.02,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=1,
        edgecolor=edgecolor,
        facecolor=facecolor,
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.add_patch(patch)
    return patch


def draw_overview(frame: pd.DataFrame, stats: dict[str, float | int], output: Path) -> None:
    fig = plt.figure(figsize=(12, 7.5), dpi=160, facecolor=BACKGROUND)
    fig.text(
        0.055,
        0.935,
        "서울 관광경험지수: 공급과 수요의 불균형",
        fontsize=24,
        weight="bold",
        color=INK,
    )
    fig.text(
        0.055,
        0.895,
        "426개 행정동의 관광 공급 기반(X)과 외국인 관광수요(Y)를 분리해 숨은 잠재지역을 탐색",
        fontsize=11.5,
        color=MUTED,
    )

    ax = fig.add_axes((0.07, 0.16, 0.61, 0.66), facecolor=WHITE)
    quadrant_style = {
        "Q1": (BLUE, "1사분면  이미 뜬 명소"),
        "Q2": (CORAL, "2사분면  수요 배후·확장"),
        "Q3": ("#98A2B3", "3사분면  비관광 생활권"),
        "Q4": (TEAL, "4사분면  숨은 잠재·핵심"),
    }
    for quadrant, (color, _) in quadrant_style.items():
        subset = frame[frame["quadrant"] == quadrant]
        ax.scatter(
            subset["supply"],
            subset["demand"],
            s=22,
            c=color,
            alpha=0.55 if quadrant != "Q4" else 0.72,
            edgecolors="none",
            label=quadrant,
        )

    x_median = float(stats["x_median"])
    y_median = float(stats["y_median"])
    ax.axvline(x_median, color=INK, linewidth=1.1, alpha=0.65)
    ax.axhline(y_median, color=INK, linewidth=1.1, alpha=0.65)
    x_line = np.linspace(frame["supply"].min(), frame["supply"].max(), 100)
    slope, intercept = np.polyfit(frame["supply"], frame["demand"], 1)
    ax.plot(x_line, slope * x_line + intercept, color=ORANGE, linewidth=2, alpha=0.9)

    highlights = {
        ("관악구", "중앙동"): (22, -22),
        ("강북구", "우이동"): (18, 13),
        ("강동구", "상일2동"): (-72, 14),
    }
    for (district, dong), offset in highlights.items():
        row = frame.loc[(frame["자치구"] == district) & (frame["행정동명"] == dong)].iloc[0]
        ax.scatter(
            [row["supply"]],
            [row["demand"]],
            s=74,
            c=TEAL,
            edgecolors=INK,
            linewidths=1.1,
            zorder=5,
        )
        ax.annotate(
            dong,
            (row["supply"], row["demand"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=9.5,
            color=INK,
            weight="bold",
            arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8},
        )

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    labels = {
        "Q1": (xmax - 0.05 * (xmax - xmin), ymax - 0.06 * (ymax - ymin), "right", "top"),
        "Q2": (xmin + 0.04 * (xmax - xmin), ymax - 0.06 * (ymax - ymin), "left", "top"),
        "Q3": (xmin + 0.04 * (xmax - xmin), ymin + 0.05 * (ymax - ymin), "left", "bottom"),
        "Q4": (xmax - 0.05 * (xmax - xmin), ymin + 0.05 * (ymax - ymin), "right", "bottom"),
    }
    for quadrant, (x, y, ha, va) in labels.items():
        color, label = quadrant_style[quadrant]
        ax.text(x, y, label, ha=ha, va=va, fontsize=9.5, color=color, weight="bold")

    ax.set_xlabel("관광 경험 공급지수 X  →", fontsize=11, color=INK, labelpad=9)
    ax.set_ylabel("외국인 관광수요 Y  →", fontsize=11, color=INK, labelpad=9)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.grid(color=GRID, linewidth=0.7, alpha=0.55)
    for spine in ax.spines.values():
        spine.set_color(GRID)

    panel = fig.add_axes((0.72, 0.16, 0.23, 0.66))
    panel.set_axis_off()
    add_round_box(panel, 0, 0.78, 1, 0.20, facecolor="#EEF3FF", edgecolor="#CAD7FA")
    panel.text(0.06, 0.925, "Pearson r", fontsize=10, color=MUTED, va="top")
    panel.text(
        0.06, 0.845, f"{float(stats['correlation']):.3f}", fontsize=28, weight="bold", color=BLUE
    )
    panel.text(0.52, 0.925, "4사분면", fontsize=10, color=MUTED, va="top")
    panel.text(0.52, 0.845, f"{int(stats['q4_count'])}개", fontsize=28, weight="bold", color=TEAL)

    candidates = [
        ("관악구 중앙동", "A 음식 2.75 · 전체 5위", "시장·노포 미식 다국어 코스", ORANGE),
        ("강북구 우이동", "C 3.04 · D 1.56", "등산·역사·한옥 하루 코스", TEAL),
        ("강동구 상일2동", "B 상권 3.58 · 관찰형", "생활형 쇼핑·산책 코스", PURPLE),
    ]
    for index, (name, evidence, action, color) in enumerate(candidates):
        y = 0.51 - index * 0.22
        add_round_box(panel, 0, y, 1, 0.17)
        panel.add_patch(
            FancyBboxPatch(
                (0.03, y + 0.03),
                0.018,
                0.11,
                boxstyle="round,pad=0,rounding_size=0.006",
                linewidth=0,
                facecolor=color,
                transform=panel.transAxes,
            )
        )
        panel.text(0.08, y + 0.125, name, fontsize=11, weight="bold", color=INK, va="top")
        panel.text(0.08, y + 0.082, evidence, fontsize=9, color=MUTED, va="top")
        panel.text(0.08, y + 0.040, action, fontsize=9.2, color=INK, va="top")

    fig.text(
        0.055,
        0.055,
        "해석: 4사분면은 자원 부족보다 외국인 대상 번역·연결·공식 채널 노출의 공백을 우선 점검하는 후보군이다.",
        fontsize=10.5,
        color=INK,
        weight="bold",
    )
    fig.text(
        0.055,
        0.027,
        "출처: 팀 최종보고서 및 최종 PCA 결과. 원천·행정동별 데이터는 공개하지 않고 집계 결과만 재시각화함.",
        fontsize=8.5,
        color=MUTED,
    )
    fig.savefig(output, dpi="figure", facecolor=BACKGROUND, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def draw_cd_pipeline(stats: dict[str, float | int | dict[str, int]], output: Path) -> None:
    fig = plt.figure(figsize=(12, 7.2), dpi=160, facecolor=BACKGROUND)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ax.text(
        0.055, 0.93, "담당 범위: C 문화자원 · D 교통 접근성", fontsize=24, weight="bold", color=INK
    )
    ax.text(
        0.055,
        0.885,
        "이질적인 점·공간자료를 426개 행정동 기준으로 정합화하고 PCA 입력 변수로 전달",
        fontsize=11.5,
        color=MUTED,
    )

    ax.text(0.055, 0.80, "C축  문화자원", fontsize=15, weight="bold", color=TEAL)
    culture_boxes = [
        (
            "문화공간",
            "1,052건 입력",
            f"{int(stats['culture_mapped']):,}건 공간결합",
            "좌표·경계 미매칭 1건",
        ),
        (
            "관광지",
            "5개 언어 2,358건",
            f"유효 좌표 {int(stats['tourist_valid']):,}건",
            "주소→키워드 2단계 지오코딩",
        ),
        (
            "콘텐츠 분류",
            f"분류 {int(stats['tourist_classified']):,}건",
            f"완료율 {int(stats['tourist_classified']) / int(stats['tourist_valid']):.1%}",
            f"지원시설 {int(stats['tourist_support']):,} · 미분류 {int(stats['tourist_unknown']):,}",
        ),
        (
            "장소형 문화유산",
            "2,079건 수집 → 1,992건",
            f"최종 집계 {int(stats['heritage_counted']):,}건",
            "무형유산 제외·지오코딩 검증",
        ),
    ]
    for index, (title, line1, line2, note) in enumerate(culture_boxes):
        x = 0.055 + index * 0.232
        add_round_box(ax, x, 0.56, 0.205, 0.19, facecolor=WHITE)
        ax.text(x + 0.018, 0.715, title, fontsize=12, weight="bold", color=INK, va="top")
        ax.text(x + 0.018, 0.668, line1, fontsize=10, color=MUTED, va="top")
        ax.text(x + 0.018, 0.625, line2, fontsize=12.5, weight="bold", color=TEAL, va="top")
        ax.text(x + 0.018, 0.578, note, fontsize=8.8, color=MUTED, va="top")
        if index < len(culture_boxes) - 1:
            ax.annotate(
                "",
                xy=(x + 0.225, 0.655),
                xytext=(x + 0.208, 0.655),
                xycoords=ax.transAxes,
                arrowprops={"arrowstyle": "->", "color": GRID, "linewidth": 1.5},
            )

    ax.text(0.055, 0.47, "D축  교통 접근성", fontsize=15, weight="bold", color=BLUE)
    hubs = stats["nearest_hubs"]
    if not isinstance(hubs, dict):
        raise TypeError("nearest_hubs must be a dictionary")
    transport_boxes = [
        (
            "D1 지하철",
            f"역 {int(stats['subway_count']):,}개",
            "행정동 공간결합",
            "고유 역 식별자 중복 제거",
        ),
        (
            "D2 거점거리",
            "426동 × 4거점 = 1,704쌍",
            f"평균 {float(stats['distance_mean']):.2f} km",
            "Haversine 직선거리",
        ),
        (
            "최근접 거점",
            f"명동 {hubs.get('명동역', 0)} · 홍대 {hubs.get('홍대입구역', 0)}",
            f"강남 {hubs.get('강남역', 0)} · 서울역 {hubs.get('서울역', 0)}",
            f"범위 {float(stats['distance_min']):.2f}–{float(stats['distance_max']):.2f} km",
        ),
        (
            "D3 버스",
            f"정류장 {int(stats['bus_count']):,}개",
            "행정동 공간결합",
            "고유 정류장 중복 제거",
        ),
    ]
    for index, (title, line1, line2, note) in enumerate(transport_boxes):
        x = 0.055 + index * 0.232
        add_round_box(ax, x, 0.23, 0.205, 0.19, facecolor=WHITE)
        ax.text(x + 0.018, 0.385, title, fontsize=12, weight="bold", color=INK, va="top")
        ax.text(x + 0.018, 0.338, line1, fontsize=10, color=MUTED, va="top")
        ax.text(x + 0.018, 0.295, line2, fontsize=12.2, weight="bold", color=BLUE, va="top")
        ax.text(x + 0.018, 0.248, note, fontsize=8.8, color=MUTED, va="top")
        if index < len(transport_boxes) - 1:
            ax.annotate(
                "",
                xy=(x + 0.225, 0.325),
                xytext=(x + 0.208, 0.325),
                xycoords=ax.transAxes,
                arrowprops={"arrowstyle": "->", "color": GRID, "linewidth": 1.5},
            )

    add_round_box(ax, 0.055, 0.075, 0.90, 0.095, facecolor="#EDF2FA", edgecolor="#CAD5E5")
    ax.text(0.075, 0.135, "팀 통합 분석으로 전달", fontsize=10, color=MUTED, va="center")
    ax.text(
        0.255,
        0.135,
        "C축 PC1 설명력 51.454%",
        fontsize=12.5,
        weight="bold",
        color=TEAL,
        va="center",
    )
    ax.text(
        0.49, 0.135, "D축 PC1 설명력 42.468%", fontsize=12.5, weight="bold", color=BLUE, va="center"
    )
    ax.text(
        0.73, 0.135, "426행 키·결측·범위 검증", fontsize=12.5, weight="bold", color=INK, va="center"
    )
    ax.text(
        0.075,
        0.097,
        "주의: D2는 실제 대중교통 시간이 아닌 직선거리 대리변수이며, D축 KMO 0.475로 잠재요인 해석에 한계가 있음.",
        fontsize=8.7,
        color=MUTED,
        va="center",
    )
    ax.text(
        0.055,
        0.025,
        "출처: C·D축 최종 산출물의 공개 가능한 집계 수치. API 응답·좌표·행정동별 원자료는 이미지와 저장소에 포함하지 않음.",
        fontsize=8.5,
        color=MUTED,
    )
    fig.savefig(output, dpi="figure", facecolor=BACKGROUND, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-results", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("assets"), type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_font()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    final, final_stats = load_final_results(args.final_results)
    cd_stats = load_cd_stats(args.archive_root)
    draw_overview(final, final_stats, args.output_dir / "portfolio-overview.png")
    draw_cd_pipeline(cd_stats, args.output_dir / "cd-axis-pipeline.png")
    print(f"Wrote portfolio assets to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
