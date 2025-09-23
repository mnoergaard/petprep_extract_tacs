import json
from pathlib import Path

import pandas as pd

from petprep_extract_tacs.utils.utils import avgwf_to_tacs


def test_avgwf_to_tacs_generates_bids_columns(tmp_path):
    ctab_content = "0 regionA\n1 regionB\n"
    avgwf_content = "1 2\n3 4\n"
    metadata = {"FrameTimesStart": [0.0, 30.0], "FrameDuration": [30.0, 30.0]}

    ctab_file = tmp_path / "example.ctab"
    avgwf_file = tmp_path / "example.txt"
    json_file = tmp_path / "example.json"

    ctab_file.write_text(ctab_content)
    avgwf_file.write_text(avgwf_content)
    json_file.write_text(json.dumps(metadata))

    out_tsv = avgwf_to_tacs(str(avgwf_file), str(ctab_file), str(json_file))

    df = pd.read_csv(out_tsv, sep="\t")

    assert list(df.columns[:2]) == ["frame_start", "frame_end"]
    assert df["frame_start"].tolist() == metadata["FrameTimesStart"]
    expected_end = [
        start + duration
        for start, duration in zip(
            metadata["FrameTimesStart"], metadata["FrameDuration"]
        )
    ]
    assert df["frame_end"].tolist() == expected_end
    assert df["regionA"].tolist() == [1, 3]
    assert df["regionB"].tolist() == [2, 4]

    # Ensure the generated TSV lives alongside the original avgwf file
    assert Path(out_tsv).parent == avgwf_file.parent
