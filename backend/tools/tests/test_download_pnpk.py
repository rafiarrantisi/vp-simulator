import contextlib
import copy
import email.message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import download_pnpk as d
from pypdf import PdfWriter


URL = "https://kemkes.go.id/test.pdf"


def pdf_bytes(width=72):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=72)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def document():
    return dict(edition_id="PNPK-TEST-2026", source_id="PNPK-TEST", condition_slug="test",
                title="Test PNPK", year=2026, revision="2026", official_url=URL,
                landing_url="https://kemkes.go.id/test", decision_number="TEST/2026",
                publisher="Kemenkes", status="active", selected_by_default=True,
                supersedes=[], superseded_by=[], clinical_review_status="unreviewed")


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, mime="application/pdf", etag='"v1"', length=None):
        super().__init__(data)
        self.headers = email.message.Message()
        self.headers["Content-Type"] = mime
        self.headers["Content-Length"] = str(len(data) if length is None else length)
        self.headers["ETag"] = etag

    def geturl(self):
        return URL


class Opener:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def open(self, request, timeout):
        self.calls.append(request)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.doc = document()
        self.manifest = d.read_manifest(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def client(self, responses, attempts=1, max_bytes=1000000):
        self.opener = Opener(responses)
        return d.HTTPClient(opener=self.opener, sleeper=lambda _: None, interval=0,
                            attempts=attempts, max_bytes=max_bytes)

    def first_download(self):
        client = self.client([Response(pdf_bytes())])
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client), "downloaded")
        return self.manifest["documents"][self.doc["edition_id"]]["artifacts"][0]

    def test_idempotent_without_network(self):
        artifact = self.first_download()
        client = self.client([])
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client), "unchanged")
        self.assertEqual(self.opener.calls, [])
        self.assertEqual(d.sha256_file(self.root / artifact["local_path"]), artifact["sha256"])

    def test_identical_refresh_deduplicates_bytes(self):
        self.first_download()
        client = self.client([Response(pdf_bytes())])
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client, refresh=True), "unchanged")
        self.assertEqual(len(list(self.root.rglob("*.pdf"))), 1)

    def test_changed_bytes_retained_and_never_approved(self):
        old = self.first_download()
        old_bytes = (self.root / old["local_path"]).read_bytes()
        client = self.client([Response(pdf_bytes(144))])
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client, refresh=True), "updated_new_version")
        entry = self.manifest["documents"][self.doc["edition_id"]]
        self.assertEqual(len(entry["artifacts"]), 2)
        self.assertTrue(entry["content_changed_requires_review"])
        self.assertEqual((self.root / old["local_path"]).read_bytes(), old_bytes)
        self.assertTrue(all(a["review_status"] == "unreviewed" for a in entry["artifacts"]))

    def test_failed_refresh_keeps_manifest_and_original(self):
        old = self.first_download()
        before = copy.deepcopy(self.manifest)
        client = self.client([Response(b"<html>error</html>", mime="text/html")])
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, client, refresh=True)
        self.assertEqual(before, self.manifest)
        self.assertTrue((self.root / old["local_path"]).exists())
        self.assertEqual(list((self.root / ".staging").glob("*.part")), [])

    def test_conditional_304_only_after_local_verification(self):
        self.first_download()
        headers = email.message.Message()
        client = self.client([urllib.error.HTTPError(URL, 304, "Not modified", headers, io.BytesIO())])
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client, refresh=True), "unchanged")
        self.assertEqual(self.opener.calls[0].get_header("If-none-match"), '"v1"')

    def test_corrupt_local_file_fails_without_silent_overwrite(self):
        old = self.first_download()
        target = self.root / old["local_path"]
        target.write_bytes(b"corrupt")
        client = self.client([])
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, client, refresh=True)
        self.assertEqual(target.read_bytes(), b"corrupt")
        self.assertFalse(self.opener.calls)

    def test_pinned_digest_mismatch_fails_without_accepting_version(self):
        client = self.client([Response(pdf_bytes())])
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, client,
                           pin={"sha256": "0" * 64, "official_url": URL})
        self.assertEqual(self.manifest["documents"], {})
        self.assertEqual(list(self.root.rglob("*.pdf")), [])

    def test_pinned_historical_bytes_can_be_reused(self):
        old = self.first_download()
        d.download_one(self.doc, self.root, self.manifest, self.client([Response(pdf_bytes(144))]), refresh=True)
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, self.client([]),
                         pin={"sha256": old["sha256"], "official_url": URL}), "unchanged")
        self.assertEqual(len(list(self.root.rglob("*.pdf"))), 2)

    def test_retry_transient_http_error(self):
        headers = email.message.Message()
        headers["Retry-After"] = "0"
        err = urllib.error.HTTPError(URL, 503, "unavailable", headers, io.BytesIO())
        client = self.client([err, Response(pdf_bytes())], attempts=2)
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client), "downloaded")
        self.assertEqual(len(self.opener.calls), 2)

    def test_does_not_retry_404(self):
        err = urllib.error.HTTPError(URL, 404, "missing", email.message.Message(), io.BytesIO())
        client = self.client([err], attempts=3)
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, client)
        self.assertEqual(len(self.opener.calls), 1)

    def test_retry_after_long_delay_stops_request_burst(self):
        headers = email.message.Message()
        headers["Retry-After"] = "120"
        err = urllib.error.HTTPError(URL, 429, "slow down", headers, io.BytesIO())
        client = self.client([err], attempts=3)
        with self.assertRaisesRegex(d.AcquisitionError, "retry later"):
            d.download_one(self.doc, self.root, self.manifest, client)
        self.assertEqual(len(self.opener.calls), 1)

    def test_short_response_retried_from_start(self):
        data = pdf_bytes()
        client = self.client([Response(data[:100], length=len(data)), Response(data)], attempts=2)
        self.assertEqual(d.download_one(self.doc, self.root, self.manifest, client), "downloaded")
        artifact = self.manifest["documents"][self.doc["edition_id"]]["artifacts"][0]
        self.assertEqual((self.root / artifact["local_path"]).read_bytes(), data)

    def test_oversized_response_fails(self):
        client = self.client([Response(pdf_bytes())], max_bytes=20)
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, client)

    def test_html_masquerading_as_pdf_and_truncated_pdf_rejected(self):
        for data in (b"<html>server error</html>", pdf_bytes()[:-12], b"%PDF-1.7\nBROKEN\n%%EOF"):
            with self.subTest(data=data[:20]):
                with self.assertRaises(d.AcquisitionError):
                    d.download_one(self.doc, self.root, self.manifest, self.client([Response(data)]))

    def test_official_url_and_redirect_policy(self):
        for url in ("http://kemkes.go.id/x", "https://kemkes.go.id.attacker.test/x",
                    "https://evil.test/x", "https://user:password@kemkes.go.id/x",
                    "https://kemkes.go.id:9999/x"):
            with self.assertRaises(d.AcquisitionError):
                d.checked_url(url)
        request = d.urllib.request.Request(URL)
        with self.assertRaises(d.AcquisitionError):
            d.OfficialRedirect().redirect_request(request, None, 302, "redirect", {}, "https://evil.test/x")

    def test_unsafe_paths_rejected(self):
        for relative in ("../escape.pdf", "/tmp/escape.pdf"):
            with self.assertRaises(d.AcquisitionError):
                d.within(self.root, relative)

    def test_corrupt_manifest_never_reset(self):
        path = self.root / "manifest.json"
        path.write_text("{bad json")
        with self.assertRaises(d.AcquisitionError):
            d.read_manifest(self.root)
        self.assertEqual(path.read_text(), "{bad json")

    def test_atomic_manifest_is_parseable(self):
        self.first_download()
        d.atomic_json(self.root / "manifest.json", self.manifest)
        self.assertEqual(d.read_manifest(self.root), self.manifest)

    def test_supersession_is_explicit_and_keeps_old_artifact(self):
        old = self.first_download()
        newer = copy.deepcopy(self.doc)
        newer.update(edition_id="PNPK-TEST-2027", year=2027, supersedes=[self.doc["edition_id"]],
                     supersession_evidence={"url": URL, "pdf_page_1based": 3, "section": "KETUJUH"})
        d.sync_supersession({"documents": [self.doc, newer]}, self.manifest)
        entry = self.manifest["documents"][self.doc["edition_id"]]
        self.assertEqual(entry["metadata"]["status"], "superseded")
        self.assertEqual(entry["metadata"]["superseded_by"], [newer["edition_id"]])
        self.assertTrue((self.root / old["local_path"]).exists())
        self.assertEqual(old["source_metadata_at_acquisition"]["status"], "active")

    def test_catalog_rejects_unproven_supersession(self):
        doc = copy.deepcopy(self.doc)
        doc["supersedes"] = ["PNPK-TEST-2025"]
        path = self.root / "catalog.json"
        d.atomic_json(path, {"catalog_schema_version": 1, "documents": [doc]})
        with self.assertRaises(d.AcquisitionError):
            d.load_catalog(path)

    def test_dry_run_no_network_or_root_writes(self):
        catalog = self.root / "catalog.json"
        d.atomic_json(catalog, {"catalog_schema_version": 1, "documents": [self.doc]})
        target = self.root / "absent"
        with mock.patch.object(d.HTTPClient, "fetch", side_effect=AssertionError("network forbidden")):
            with contextlib.redirect_stdout(io.StringIO()):
                result = d.main(["download", "--catalog", str(catalog), "--root", str(target), "--dry-run"])
        self.assertEqual(result, 0)
        self.assertFalse(target.exists())

    def test_discovery_is_separate_and_nonrecursive(self):
        data = b'<a href="/test.pdf">Unduh</a><a href="https://evil.test/x.pdf">bad</a><a href="/id/pnpk-new">PNPK new</a>'
        client = self.client([Response(data, mime="text/html")])
        result = d.discover({}, ["https://kemkes.go.id/index"], client)
        self.assertEqual(len(self.opener.calls), 1)
        self.assertEqual(len(result["candidates"]), 2)
        self.assertTrue(all(x["review_status"] == "unreviewed" for x in result["candidates"]))
        self.assertEqual(self.manifest["documents"], {})

    def test_unexpected_304_has_no_artifact_to_reuse(self):
        err = urllib.error.HTTPError(URL, 304, "not modified", email.message.Message(), io.BytesIO())
        with self.assertRaises(d.AcquisitionError):
            d.download_one(self.doc, self.root, self.manifest, self.client([err]))

    @unittest.skipIf(d.os.name == "nt", "POSIX lock regression; Windows code requires Windows CI")
    def test_second_writer_is_rejected(self):
        with d.manifest_lock(self.root):
            with self.assertRaisesRegex(d.AcquisitionError, "holds the root lock"):
                with d.manifest_lock(self.root):
                    self.fail("Second writer acquired the lock")

    def test_discovery_cannot_overwrite_source_catalog(self):
        catalog = self.root / "catalog.json"
        d.atomic_json(catalog, {"catalog_schema_version": 1, "documents": [self.doc]})
        before = catalog.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            result = d.main(["discover", "--catalog", str(catalog), "--output", str(catalog)])
        self.assertEqual(result, 2)
        self.assertEqual(before, catalog.read_bytes())


if __name__ == "__main__":
    unittest.main()
