#!/usr/bin/env python3
"""Acquire audited PNPK sources; never approve evidence or change case bindings.

Python 3.11+, pypdf. Only download/discovery commands access the network.
See README.md for the distinction between the catalog, lockfile and manifest.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import email.utils
import hashlib
import http.client
import json
import os
from pathlib import Path
import random
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

ALLOWED_HOSTS = frozenset({"kemkes.go.id", "www.kemkes.go.id", "keslan.kemkes.go.id",
                          "jdih.kemkes.go.id", "repository.kemkes.go.id"})
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
USER_AGENT = "Qora-PNPK-Acquisition/1.0 (public official documents; sequential requests)"
TRANSIENT = {408, 429, 500, 502, 503, 504}


class AcquisitionError(Exception):
    pass


class TransferError(AcquisitionError):
    pass


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def checked_url(url):
    p = urllib.parse.urlsplit(url)
    if (p.scheme != "https" or p.hostname not in ALLOWED_HOSTS or
            p.username or p.password or p.port not in (None, 443) or p.fragment):
        raise AcquisitionError(f"URL not allowed: {url!r}")
    return url


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AcquisitionError(f"Cannot read JSON {path}: {exc}") from exc


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".json-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def within(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise AcquisitionError(f"Unsafe relative path: {relative}")
    result = (root / rel).resolve()
    if not result.is_relative_to(root):
        raise AcquisitionError(f"Path escapes source root: {relative}")
    return result


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_pdf(path):
    """Basic structural validation, not signature authentication or clinical QA."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise AcquisitionError("Install dependencies: python -m pip install -r requirements.txt") from exc
    path = Path(path)
    size = path.stat().st_size
    if size < 16:
        raise AcquisitionError("PDF empty or too short")
    with path.open("rb") as stream:
        if not stream.read(1024).lstrip().startswith(b"%PDF-"):
            raise AcquisitionError("Not a PDF: missing signature (possibly an HTML error page)")
        stream.seek(max(0, size - 4096))
        if b"%%EOF" not in stream.read():
            raise AcquisitionError("PDF has no trailing EOF marker")
    try:
        with path.open("rb") as stream:
            reader = PdfReader(stream, strict=False)
            if reader.is_encrypted:
                raise AcquisitionError("Encrypted PDF requires manual source review")
            pages = len(reader.pages)
            if pages < 1:
                raise AcquisitionError("PDF contains no pages")
            # Traverse page references, but do not OCR or extract full documents.
            for page in reader.pages:
                _ = page.mediabox
    except AcquisitionError:
        raise
    except Exception as exc:
        raise AcquisitionError(f"PDF structural validation failed: {exc}") from exc
    return {"method": "pypdf+signature+eof", "page_count": pages, "file_size": size}


def load_catalog(path):
    obj = load_json(path)
    if obj.get("catalog_schema_version") != 1 or not isinstance(obj.get("documents"), list):
        raise AcquisitionError("Unsupported catalog schema")
    seen = set()
    for doc in obj["documents"]:
        for key in ("edition_id", "source_id", "condition_slug"):
            if not ID_RE.fullmatch(str(doc.get(key, ""))):
                raise AcquisitionError(f"Invalid catalog {key}: {doc.get(key)!r}")
        if doc["edition_id"] in seen:
            raise AcquisitionError("Duplicate edition_id")
        seen.add(doc["edition_id"])
        if not isinstance(doc.get("year"), int) or not 1900 <= doc["year"] <= 2100:
            raise AcquisitionError("Invalid document year")
        for key in ("title", "publisher", "official_url", "landing_url", "decision_number"):
            if not doc.get(key):
                raise AcquisitionError(f"Missing {key} in {doc['edition_id']}")
        checked_url(doc["official_url"])
        checked_url(doc["landing_url"])
        if doc.get("status") not in {"active", "superseded", "archived"}:
            raise AcquisitionError("Invalid source status")
        if doc.get("supersedes") and not doc.get("supersession_evidence"):
            raise AcquisitionError("Explicit supersession requires a documentary citation")
    for url in obj.get("discovery_pages", []):
        checked_url(url)
    return obj


def select_documents(catalog, ids, all_documents):
    if ids and all_documents:
        raise AcquisitionError("Use --id or --all, not both")
    docs = catalog["documents"]
    if ids:
        unknown = set(ids) - {d["edition_id"] for d in docs}
        if unknown:
            raise AcquisitionError(f"Unknown edition IDs: {sorted(unknown)}")
        return [d for d in docs if d["edition_id"] in ids]
    return docs if all_documents else [d for d in docs if d.get("selected_by_default")]


@contextlib.contextmanager
def manifest_lock(root):
    """OS lock is released on crash. The harmless lock file may remain."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".acquisition.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise AcquisitionError("Another acquisition process holds the root lock") from exc
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise AcquisitionError("Another acquisition process holds the root lock") from exc
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


class HTTPClient:
    def __init__(self, timeout=25, attempts=3, interval=1.0, max_bytes=80 * 1024 * 1024,
                 opener=None, sleeper=time.sleep):
        self.timeout, self.attempts, self.interval = timeout, attempts, interval
        self.max_bytes = max_bytes
        self.opener = opener or urllib.request.build_opener(OfficialRedirect())
        self.sleeper = sleeper
        self.last_request = None

    def _pace(self):
        if self.last_request is not None:
            self.sleeper(max(0, self.interval - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()

    def _retry_delay(self, attempt, exc):
        delay = min(2 ** attempt + random.uniform(0, 0.5), 10)
        value = exc.headers.get("Retry-After") if isinstance(exc, urllib.error.HTTPError) else None
        if value:
            try:
                server_delay = float(value)
            except ValueError:
                try:
                    parsed = email.utils.parsedate_to_datetime(value)
                    server_delay = (parsed - dt.datetime.now(dt.timezone.utc)).total_seconds()
                except (TypeError, ValueError):
                    server_delay = 0
            # Do not hammer a server asking for a long pause. Let the operator rerun later.
            if server_delay > 60:
                raise AcquisitionError(f"Server requests Retry-After={value}; retry later") from exc
            delay = max(delay, server_delay)
        return delay

    def fetch(self, url, target, headers=None, expect_pdf=True):
        checked_url(url)
        target = Path(target)
        limit = self.max_bytes if expect_pdf else min(self.max_bytes, 2 * 1024 * 1024)
        for attempt in range(self.attempts):
            self._pace()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                "Accept": "application/pdf" if expect_pdf else "text/html",
                "Accept-Encoding": "identity", **(headers or {})})
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    checked_url(response.geturl())
                    if response.status != 200:
                        raise AcquisitionError(f"Unexpected HTTP {response.status}")
                    mime = response.headers.get_content_type().lower()
                    if expect_pdf and mime not in {"application/pdf", "application/octet-stream", "binary/octet-stream"}:
                        raise AcquisitionError(f"Unexpected content type: {mime}")
                    if not expect_pdf and mime not in {"text/html", "application/xhtml+xml"}:
                        raise AcquisitionError(f"Discovery page is not HTML: {mime}")
                    length = response.headers.get("Content-Length")
                    expected = int(length) if length and length.isdigit() else None
                    if expected is not None and expected > limit:
                        raise AcquisitionError(f"Response exceeds {limit} byte limit")
                    total = 0
                    started = time.monotonic()
                    with target.open("wb") as stream:
                        while block := response.read(64 * 1024):
                            total += len(block)
                            if total > limit:
                                raise AcquisitionError("Response exceeds configured byte limit")
                            if time.monotonic() - started > 180:
                                raise TransferError("Transfer exceeded 180 second budget")
                            stream.write(block)
                        stream.flush()
                        os.fsync(stream.fileno())
                    if expected is not None and total != expected:
                        raise TransferError("Truncated response: Content-Length mismatch")
                    if total == 0:
                        raise TransferError("Empty response")
                    return {"not_modified": False, "resolved_url": response.geturl(),
                            "content_type": mime, "etag": response.headers.get("ETag"),
                            "last_modified": response.headers.get("Last-Modified")}
            except urllib.error.HTTPError as exc:
                if exc.code == 304 and headers and (headers.get("If-None-Match") or headers.get("If-Modified-Since")):
                    exc.close()
                    return {"not_modified": True}
                if exc.code not in TRANSIENT or attempt + 1 == self.attempts:
                    exc.close()
                    raise AcquisitionError(f"HTTP {exc.code} for {url}") from exc
                try:
                    delay = self._retry_delay(attempt, exc)
                finally:
                    exc.close()
            except (urllib.error.URLError, socket.timeout, ConnectionError,
                    http.client.HTTPException, TransferError) as exc:
                if attempt + 1 == self.attempts:
                    raise AcquisitionError(f"Transfer failed after {self.attempts} attempts: {exc}") from exc
                delay = self._retry_delay(attempt, exc)
            self.sleeper(delay)
        raise AcquisitionError("Transfer attempts exhausted")


def read_manifest(root):
    path = Path(root) / "manifest.json"
    if not path.exists():
        return {"manifest_schema_version": 1, "documents": {}, "created_at": utcnow()}
    obj = load_json(path)
    if obj.get("manifest_schema_version") != 1 or not isinstance(obj.get("documents"), dict):
        raise AcquisitionError("Unsupported manifest; refusing to overwrite")
    return obj


def verify_artifact(root, artifact):
    path = within(root, artifact["local_path"])
    if not SHA_RE.fullmatch(artifact.get("sha256", "")):
        raise AcquisitionError("Invalid manifest digest")
    if not path.is_file() or sha256_file(path) != artifact["sha256"]:
        raise AcquisitionError(f"Missing or checksum mismatch: {artifact['local_path']}")
    validation = validate_pdf(path)
    if validation["file_size"] != artifact["file_size"]:
        raise AcquisitionError("Manifest file_size mismatch")
    return validation


def download_one(doc, root, manifest, client, refresh=False, pin=None):
    edition = doc["edition_id"]
    old_entry = manifest["documents"].get(edition)
    entry = copy.deepcopy(old_entry or {"artifacts": [], "latest_observed_sha256": None})
    artifacts = entry["artifacts"]
    if pin and (not SHA_RE.fullmatch(pin.get("sha256", "")) or pin.get("official_url") != doc["official_url"]):
        raise AcquisitionError("Lockfile URL or SHA does not match the audited catalog")
    wanted = pin["sha256"] if pin else entry.get("latest_observed_sha256")
    current = next((a for a in artifacts if a["sha256"] == wanted), None)
    if current:
        # Corrupt local state is never silently overwritten. Preserve it for investigation.
        verify_artifact(root, current)
    if current and (pin or (not refresh and current["official_url"] == doc["official_url"])):
        entry.update({"metadata": copy.deepcopy(doc), "last_local_verified_at": utcnow()})
        manifest["documents"][edition] = entry
        return "unchanged"

    conditional = {}
    if current and not pin and current["official_url"] == doc["official_url"]:
        for response_key, request_key in (("etag", "If-None-Match"), ("last_modified", "If-Modified-Since")):
            if current.get(response_key):
                conditional[request_key] = current[response_key]
    staging = within(root, ".staging")
    staging.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=edition + "-", suffix=".part", dir=staging)
    os.close(fd)
    tmp = Path(tmp)
    try:
        response = client.fetch(doc["official_url"], tmp, conditional)
        if response["not_modified"]:
            if not current:
                raise AcquisitionError("304 without a verified local artifact")
            entry.update({"metadata": copy.deepcopy(doc), "last_remote_checked_at": utcnow()})
            manifest["documents"][edition] = entry
            return "unchanged"
        validation = validate_pdf(tmp)
        digest = sha256_file(tmp)
        if pin and digest != pin["sha256"]:
            raise AcquisitionError(f"Pinned checksum differs: expected {pin['sha256']}, received {digest}; catalog/library review required")
        same = next((a for a in artifacts if a["sha256"] == digest), None)
        if same:
            verify_artifact(root, same)
            same.update({k: v for k, v in response.items() if k != "not_modified"})
            same["last_remote_checked_at"] = utcnow()
            same["official_url"] = doc["official_url"]
            outcome = "unchanged"
        else:
            rel = f"{doc['condition_slug']}/{doc['year']}/{edition}/{digest}.pdf"
            destination = within(root, rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Recover a valid orphan after a crash between artifact publication and manifest write.
            if destination.exists():
                if sha256_file(destination) != digest:
                    raise AcquisitionError("Content-addressed destination exists with different bytes")
                validate_pdf(destination)
            else:
                os.replace(tmp, destination)
            artifact = {"artifact_id": f"{edition}@sha256:{digest}", "sha256": digest,
                        "local_path": rel, "file_size": validation["file_size"],
                        "downloaded_at": utcnow(), "official_url": doc["official_url"],
                        "source_metadata_at_acquisition": copy.deepcopy(doc),
                        "validation": validation, "review_status": "unreviewed",
                        **{k: v for k, v in response.items() if k != "not_modified"}}
            artifacts.append(artifact)
            previously_known_family = any(e.get("metadata", {}).get("source_id") == doc["source_id"]
                                          for e in manifest["documents"].values())
            outcome = "updated_new_version" if old_entry or previously_known_family else "downloaded"
            if old_entry:
                entry["content_changed_requires_review"] = True
        entry.update({"metadata": copy.deepcopy(doc), "latest_observed_sha256": digest,
                      "last_remote_checked_at": utcnow()})
        manifest["documents"][edition] = entry
        return outcome
    finally:
        tmp.unlink(missing_ok=True)


def sync_supersession(catalog, manifest):
    """Only explicit researched relations. Changed bytes alone never supersede anything."""
    by_id = {d["edition_id"]: d for d in catalog["documents"]}
    for edition, entry in manifest["documents"].items():
        if edition in by_id:
            entry["metadata"] = copy.deepcopy(by_id[edition])
    for doc in catalog["documents"]:
        for previous in doc.get("supersedes", []):
            if previous in manifest["documents"]:
                prior = manifest["documents"][previous]["metadata"]
                prior["status"] = "superseded"
                prior["superseded_by"] = sorted(set(prior.get("superseded_by", [])) | {doc["edition_id"]})
                prior["supersession_evidence"] = doc["supersession_evidence"]


class DiscoveryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.href, self.text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href, self.text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self.href:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(" ".join(self.text).split())))
            self.href, self.text = None, []


def discover(catalog, pages, client):
    results, failures = [], []
    for url in dict.fromkeys(pages or catalog.get("discovery_pages", [])):
        checked_url(url)
        with tempfile.TemporaryDirectory(prefix="qora-pnpk-discovery-") as folder:
            try:
                target = Path(folder) / "page.html"
                client.fetch(url, target, expect_pdf=False)
                parser = DiscoveryParser()
                parser.feed(target.read_text(encoding="utf-8", errors="replace"))
                for href, label in parser.links:
                    absolute = urllib.parse.urljoin(url, href)
                    p = urllib.parse.urlsplit(absolute)
                    if not (p.path.lower().endswith(".pdf") or "pnpk" in (p.path + label).lower()
                            or "pedoman-nasional" in p.path.lower()):
                        continue
                    try:
                        checked_url(absolute)
                    except (AcquisitionError, ValueError):
                        continue
                    results.append({"discovered_on": url, "url": absolute, "label": label,
                                    "kind": "pdf_candidate" if p.path.lower().endswith(".pdf") else "landing_candidate",
                                    "review_status": "unreviewed"})
            except (AcquisitionError, OSError) as exc:
                failures.append({"url": url, "error": str(exc)})
    unique = {(x["discovered_on"], x["url"]): x for x in results}
    return {"discovery_schema_version": 1, "observed_at": utcnow(),
            "note": "Candidates only; no recursive crawl, downloads, or catalog promotion.",
            "candidates": list(unique.values()), "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["download", "verify", "discover", "lock"], default="download")
    parser.add_argument("--catalog", type=Path, default=Path(__file__).with_name("pnpk_sources.json"))
    parser.add_argument("--root", type=Path, default=Path("clinical_sources/pnpk"))
    parser.add_argument("--id", action="append", default=[], help="Repeat to select exact edition IDs")
    parser.add_argument("--all", action="store_true", help="Explicitly select every catalog edition, including archives/holds")
    parser.add_argument("--dry-run", action="store_true", help="No network or filesystem writes")
    parser.add_argument("--refresh", action="store_true", help="Recheck remote bytes, preserving old versions")
    parser.add_argument("--lockfile", type=Path, help="Require exact bytes in an audited lockfile; never auto-accept changed content")
    parser.add_argument("--output", type=Path, help="Required output for discover/lock")
    parser.add_argument("--page", action="append", default=[], help="Explicit official landing/index URL for discover")
    parser.add_argument("--timeout", type=float, default=25)
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.attempts <= 5 or not 1 <= args.timeout <= 60:
            raise AcquisitionError("Use 1..5 attempts and 1..60 second socket timeout")
        if args.refresh and args.lockfile:
            raise AcquisitionError("--refresh discovers changes; --lockfile reproduces bytes. Run them separately.")
        if args.command in {"discover", "lock"} and not args.output:
            raise AcquisitionError("--output is required for discover/lock")
        if args.output and args.output.resolve() in {args.catalog.resolve(), (args.root / "manifest.json").resolve()}:
            raise AcquisitionError("Discovery/lock output must not overwrite the catalog or acquisition manifest")
        catalog = load_catalog(args.catalog)
        documents = select_documents(catalog, args.id, args.all)
        if not documents and args.command != "discover":
            raise AcquisitionError("No documents selected")
        if args.dry_run:
            print(json.dumps({"dry_run": True, "command": args.command,
                "selected": [d["edition_id"] for d in documents],
                "urls": (args.page or catalog.get("discovery_pages", [])) if args.command == "discover"
                        else [d["official_url"] for d in documents],
                "network_requests": 0, "writes": 0}, indent=2))
            return 0
        client = HTTPClient(timeout=args.timeout, attempts=args.attempts)
        if args.command == "discover":
            data = discover(catalog, args.page, client)
            atomic_json(args.output, data)
            print(json.dumps({"candidates": len(data["candidates"]), "failed": len(data["failures"])}))
            return int(bool(data["failures"]))
        if args.command in {"verify", "lock"}:
            manifest = read_manifest(args.root)
            errors, pins, verified = [], {}, 0
            for doc in documents:
                entry = manifest["documents"].get(doc["edition_id"])
                if not entry or not entry["artifacts"]:
                    errors.append(f"Not downloaded: {doc['edition_id']}")
                    continue
                for artifact in entry["artifacts"]:
                    try:
                        verify_artifact(args.root, artifact)
                        verified += 1
                        if artifact["sha256"] == entry["latest_observed_sha256"]:
                            pins[doc["edition_id"]] = {"sha256": artifact["sha256"],
                                                      "official_url": artifact["official_url"]}
                    except (AcquisitionError, OSError, KeyError) as exc:
                        errors.append(f"{doc['edition_id']}: {exc}")
            if args.command == "lock" and not errors:
                atomic_json(args.output, {"lock_schema_version": 1, "created_at": utcnow(),
                                          "clinical_approval": False, "documents": pins})
            print(json.dumps({"verified": verified, "failed": len(errors), "errors": errors}, indent=2))
            return int(bool(errors))
        pins = None
        if args.lockfile:
            lock = load_json(args.lockfile)
            if lock.get("lock_schema_version") != 1:
                raise AcquisitionError("Unsupported lockfile schema")
            pins = lock["documents"]
            if any(d["edition_id"] not in pins for d in documents):
                raise AcquisitionError("Lockfile must cover every selected edition")
        counts = {"downloaded": 0, "unchanged": 0, "updated_new_version": 0, "failed": 0}
        with manifest_lock(args.root):
            manifest = read_manifest(args.root)
            for doc in documents:
                try:
                    outcome = download_one(doc, args.root, manifest, client, args.refresh,
                                           pins.get(doc["edition_id"]) if pins is not None else None)
                    counts[outcome] += 1
                    print(f"{outcome}: {doc['edition_id']}", flush=True)
                except (AcquisitionError, OSError, ValueError, KeyError) as exc:
                    counts["failed"] += 1
                    print(f"failed: {doc['edition_id']}: {exc}", file=sys.stderr, flush=True)
                    # Operational failure remains separate from a document's clinical/source status.
                    manifest.setdefault("last_failures", {})[doc["edition_id"]] = {
                        "at": utcnow(), "error": str(exc), "official_url": doc["official_url"]}
                else:
                    manifest.get("last_failures", {}).pop(doc["edition_id"], None)
                sync_supersession(catalog, manifest)
                manifest["updated_at"] = utcnow()
                atomic_json(args.root / "manifest.json", manifest)
        print(json.dumps({"summary": counts}, indent=2))
        return int(counts["failed"] > 0)
    except (AcquisitionError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
