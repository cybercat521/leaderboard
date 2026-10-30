import contextlib
import copy
import csv
import io
import json
import ssl
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import leaderboard_charts as charts
import update_leaderboard as updater
from table30_v2 import CAPABILITIES, OFFICIAL_TAGS, TASKS


ROOT = Path(__file__).resolve().parent.parent


def sample_rows():
    return [
        {
            "rank": i + 1,
            "display_name": f"model-{i}",
            "user_name": f"team-{i}",
            "score": 40.5,
            "success_ratio": 0.25,
            "task_results": [
                {"task_id": TASKS[0].id, "success_ratio": 0.0},
                {"task_id": TASKS[1].id, "success_ratio": 1.0},
            ],
        }
        for i in range(8)
    ]


def official_tags():
    return {entry["task_id"]: entry["task_tag"] for entry in json.loads((ROOT / "data/table30-v2-task-tags.json").read_text())}


class ChartTests(unittest.TestCase):
    def test_fixed_capability_denominator(self):
        tags = {task.id: [] for task in TASKS}
        tags[TASKS[0].id] = ["bimanual", "precise3d"]
        tags[TASKS[1].id] = ["bimanual"]
        # One evaluated 100% task plus one unreported task = 50%, not 100%.
        values = charts.capability_values({TASKS[0].id: 100}, tags | {TASKS[2].id: list(CAPABILITIES[2:])})
        self.assertEqual(values, [50, 100, 0, 0, 0, 0, 0, 0, 0])

    def test_missing_is_distinct_from_measured_zero(self):
        results = charts.model_tasks(sample_rows()[0])
        self.assertEqual(results[TASKS[0].id], 0)
        self.assertNotIn(TASKS[2].id, results)
        files = charts.generate_assets(sample_rows(), official_tags())
        records = list(csv.DictReader(io.StringIO(files["data/table30-v2-tasks.csv"])))
        self.assertEqual(len(records), 5 * 30)
        self.assertEqual(records[0]["success_rate_percent"], "0.0000")
        self.assertEqual(records[1]["success_rate_percent"], "100.0000")
        self.assertEqual(records[2]["success_rate_percent"], "")
        self.assertNotIn("model-5", files["assets/table30-v2-tasks-en.svg"])

    def test_svg_escape_and_determinism(self):
        rows = sample_rows()
        rows[0]["display_name"] = '<script>alert("x")</script>&'
        first = charts.generate_assets(rows, official_tags())
        self.assertEqual(first, charts.generate_assets(rows, official_tags()))
        for name, content in first.items():
            if name.endswith(".svg"):
                root = ET.fromstring(content)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertNotIn("<script>", content)
        self.assertIn("&lt;script&gt;", first["assets/table30-v2-capabilities-en.svg"])
        self.assertTrue(charts.csv_text([["=formula", "+formula", "@formula"]]).startswith("'=formula,'+formula,'@formula"))

    def test_invalid_task_results_fail(self):
        for results in (None, [], [{"task_id": "unknown", "success_ratio": 0}],
                        [{"task_id": TASKS[0].id, "success_ratio": 2}],
                        [{"task_id": TASKS[0].id, "success_ratio": float("nan")}],
                        [{"task_id": TASKS[0].id, "success_ratio": 0}] * 2):
            with self.subTest(results=results), self.assertRaises(ValueError):
                charts.model_tasks(dict(sample_rows()[0], task_results=results))

    def test_static_tags_cover_official_finite_set(self):
        entries = json.loads((ROOT / "data/table30-v2-task-tags.json").read_text())
        tags = charts.validate_task_tags(entries)
        self.assertEqual(tags, official_tags())
        self.assertEqual(len(OFFICIAL_TAGS), 15)
        self.assertEqual(set().union(*map(set, tags.values())), OFFICIAL_TAGS)
        counts = {tag: sum(tag in values for values in tags.values()) for tag in CAPABILITIES}
        self.assertEqual(counts, {"bimanual": 13, "precise3d": 14, "manipulation": 14,
                                 "temporal": 6, "softbody": 7, "repeated": 12,
                                 "simple-pick": 1, "classification": 2, "multiview": 1})
        invalid = [None, {}, [], entries[:-1], entries[:-1] + entries[:1]]
        for field, value in (("task_name", "wrong"), ("robot", "ARX5"),
                             ("task_tag", ["unknown"]), ("task_tag", ["softbody"]),
                             ("task_tag", entries[0]["task_tag"] * 2)):
            bad = copy.deepcopy(entries)
            bad[0][field] = value
            invalid.append(bad)
        for bad in invalid:
            with self.subTest(raw=bad), self.assertRaises(ValueError):
                charts.validate_task_tags(bad)

    def test_radar_uses_all_nine_official_tag_names(self):
        for lang in ("en", "zh"):
            root = ET.fromstring(charts.radar_svg(sample_rows(), official_tags(), lang, "light"))
            ns = {"svg": "http://www.w3.org/2000/svg"}
            labels = [node.text for node in root.findall(".//svg:text", ns)]
            for tag in CAPABILITIES:
                self.assertEqual(labels.count(tag), 5)
            self.assertEqual(len(root.findall(".//svg:circle", ns)), 45)
            for polygon in root.findall(".//svg:polygon", ns):
                self.assertEqual(len(polygon.attrib["points"].split()), 9)
        self.assertNotIn("data/table30-v2-task-tags.json", charts.generate_assets(sample_rows(), official_tags()))

    def test_heat_ramp_is_monotonic_and_text_has_contrast(self):
        def luminance(color):
            values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
            return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))
        for mode in ("light", "dark"):
            previous = None
            for value in range(101):
                fill = charts.heat_color(value, mode)
                lightness = luminance(fill)
                if previous is not None:
                    self.assertGreaterEqual(previous - lightness if mode == "light" else lightness - previous, -0.001)
                previous = lightness
                ink = luminance(charts.readable_ink(fill))
                self.assertGreaterEqual((max(lightness, ink) + .05) / (min(lightness, ink) + .05), 4.5)


class UpdateTests(unittest.TestCase):
    def test_invalid_api_payload_is_rejected(self):
        for raw in (None, {}, [], [None], [{}], [dict(sample_rows()[0], score="bad")]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                updater.extract_rows(raw)

    def test_fetch_uses_verified_curl_after_tls_failures(self):
        completed = type("Result", (), {"stdout": b'[1]'})()
        with patch.object(updater, "urlopen", side_effect=URLError("TLS handshake failure")) as urlopen:
            with patch.object(updater.subprocess, "run", return_value=completed) as run:
                self.assertEqual(updater.fetch_json(updater.LEADERBOARD_URL), [1])
        self.assertEqual(urlopen.call_count, 2)
        requested_url = urlopen.call_args.args[0].full_url
        self.assertIn("?_refresh=", requested_url)
        self.assertEqual(run.call_args.args[0][-1], requested_url)
        self.assertIn("Cache-Control: no-cache", run.call_args.args[0])
        for call in urlopen.call_args_list:
            self.assertEqual(call.args[0].get_header("Cache-control"), "no-cache")
            context = call.kwargs["context"]
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "curl")
        self.assertNotIn("-k", command)
        self.assertNotIn("--insecure", command)

    def test_fetch_falls_back_to_official_www_host(self):
        response = io.BytesIO(b'[2]')
        with patch.object(updater, "urlopen", side_effect=[URLError("TLS failure"), URLError("TLS failure"), response]) as urlopen:
            with patch.object(updater.subprocess, "run", side_effect=OSError("curl unavailable")):
                self.assertEqual(updater.fetch_json(updater.LEADERBOARD_URL), [2])
        self.assertTrue(urlopen.call_args.args[0].full_url.startswith("https://www.robochallenge.cn/"))
        self.assertEqual(urlopen.call_args_list[0].args[0].full_url.split("?", 1)[1], urlopen.call_args.args[0].full_url.split("?", 1)[1])

    def test_success_rate_uses_two_decimals(self):
        row = dict(sample_rows()[0], success_ratio=0.4333)
        self.assertIn("| 43.33 |", updater.build_table([row], "en"))
        self.assertIn("SR 43.33%", charts.radar_svg([row], official_tags(), "en", "light"))

    def test_successful_sync_refreshes_time_and_failure_preserves_files(self):
        rows = sample_rows()
        tags_content = (ROOT / "data/table30-v2-task-tags.json").read_text()
        original = "# Keep intro\n" + updater.SECTION_START + "\nold\n" + updater.SECTION_END + "\n# Keep tasks\n"
        with tempfile.TemporaryDirectory() as folder, patch.object(updater, "BASE_DIR", Path(folder)), contextlib.redirect_stdout(io.StringIO()):
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/table30-v2-task-tags.json").write_text(tags_content)
            for target in updater.README_TARGETS:
                (root / target["path"]).write_text(original)
            with patch.object(updater, "fetch_json", return_value=rows) as fetch, patch.object(updater, "datetime") as clock:
                clock.now.return_value = datetime(2026, 10, 30, 10, 15, 1, tzinfo=updater.UTC_PLUS_8)
                updater.main()
                fetch.assert_called_once_with(updater.LEADERBOARD_URL)
            first = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in root.rglob("*") if path.is_file()}
            with patch.object(updater, "fetch_json", return_value=rows), patch.object(updater, "datetime") as clock:
                clock.now.return_value = datetime(2026, 10, 30, 11, 15, 2, tzinfo=updater.UTC_PLUS_8)
                updater.main()
            for path, (content, mtime) in first.items():
                if path.name in {target["path"] for target in updater.README_TARGETS}:
                    self.assertIn(b"2026-10-30 11:15:02 UTC+8", path.read_bytes())
                    self.assertEqual(content.replace(b"10:15:01", b"11:15:02"), path.read_bytes())
                else:
                    self.assertEqual((content, mtime), (path.read_bytes(), path.stat().st_mtime_ns))
            first = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in first}
            with patch.object(updater, "fetch_json", side_effect=OSError("network unavailable")), self.assertRaises(OSError):
                updater.main()
            broken = copy.deepcopy(rows)
            broken[0]["task_results"] = []
            with patch.object(updater, "fetch_json", return_value=broken), self.assertRaises(ValueError):
                updater.main()
            self.assertEqual(first, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in first})
            for target in updater.README_TARGETS:
                content = (root / target["path"]).read_text()
                self.assertTrue(content.startswith("# Keep intro\n"))
                self.assertTrue(content.endswith("\n# Keep tasks\n"))
                self.assertEqual(content.count("### RoboChallenge Table30 V2"), 1)


if __name__ == "__main__":
    unittest.main()
