import argparse
import pandas as pd


def detect_cell_anomalies(
    baseline_csv: str,
    current_csv: str,
    output_csv: str,
    ratio_thresh: float = 5.0,
    min_current_density: float = 2.0,
    eps: float = 1e-3,
):
    """
    Compares baseline vs current density per grid cell and flags anomalies.

    Assumptions:
    - Baseline/current CSVs are produced by mt-ais-toolbox get_density() and have columns:
      ['gridID', 'density', 'lon_centroid', 'lat_centroid'].
    - For 'time_at_cells' density, units are hours; adjust thresholds accordingly.
    - For 'vessels_count', set min_current_density to 1 and tune ratio_thresh.
    """
    bdf = pd.read_csv(baseline_csv)
    cdf = pd.read_csv(current_csv)

    # Keep only expected columns if present
    cols = ["gridID", "density", "lon_centroid", "lat_centroid"]
    bdf = bdf[[c for c in cols if c in bdf.columns]].copy()
    cdf = cdf[[c for c in cols if c in cdf.columns]].copy()
    bdf.rename(columns={"density": "baseline"}, inplace=True)
    cdf.rename(columns={"density": "current"}, inplace=True)

    df = pd.merge(bdf, cdf, on="gridID", how="outer", suffixes=("_b", "_c"))
    # Prefer current centroids when available, else baseline
    if "lon_centroid_c" in df.columns:
        df["lon_centroid"] = df["lon_centroid_c"].fillna(df.get("lon_centroid_b"))
        df["lat_centroid"] = df["lat_centroid_c"].fillna(df.get("lat_centroid_b"))
    elif "lon_centroid_b" in df.columns:
        df["lon_centroid"] = df["lon_centroid_b"]
        df["lat_centroid"] = df["lat_centroid_b"]

    df["baseline"] = df["baseline"].fillna(0.0)
    df["current"] = df["current"].fillna(0.0)

    baseline_eps = df["baseline"].clip(lower=eps)
    df["ratio"] = df["current"] / baseline_eps
    df["diff"] = df["current"] - df["baseline"]
    df["score"] = df["ratio"] * df["diff"]
    df["is_anomaly"] = (df["ratio"] >= ratio_thresh) & (df["current"] >= min_current_density)

    out_cols = [
        "gridID",
        "lon_centroid",
        "lat_centroid",
        "baseline",
        "current",
        "ratio",
        "diff",
        "score",
        "is_anomaly",
    ]
    df[out_cols].to_csv(output_csv, index=False)

    # Show a quick summary in stdout
    top = df.sort_values("score", ascending=False).head(10)[out_cols]
    print("Saved:", output_csv)
    print("Total anomalies:", int(df["is_anomaly"].sum()))
    print("Top 10 by score:")
    print(top.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="Cell-level anomaly detection for AIS density maps")
    parser.add_argument("baseline_csv", help="Baseline density CSV (historical period)")
    parser.add_argument("current_csv", help="Current density CSV (target period)")
    parser.add_argument("output_csv", help="Output CSV with anomaly scores and flags")
    parser.add_argument("--ratio-thresh", type=float, default=5.0, help="Minimum ratio current/baseline to flag anomaly")
    parser.add_argument("--min-current-density", type=float, default=2.0, help="Minimum current density to consider (hours for time_at_cells)")
    parser.add_argument("--eps", type=float, default=1e-3, help="Small epsilon to avoid divide-by-zero when baseline is ~0")

    args = parser.parse_args()
    detect_cell_anomalies(
        args.baseline_csv,
        args.current_csv,
        args.output_csv,
        ratio_thresh=args.ratio_thresh,
        min_current_density=args.min_current_density,
        eps=args.eps,
    )


if __name__ == "__main__":
    main()
