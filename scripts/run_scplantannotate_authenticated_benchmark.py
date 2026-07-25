from __future__ import annotations

import argparse
import csv
import http.cookiejar
import json
import mimetypes
import os
import secrets
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from sklearn.metrics import accuracy_score, f1_score


BASE_URL = "https://scplantannotate.missouri.edu/"
USER_AGENT = "SnowLotus-CellFM scPlantAnnotate benchmark client/0.1"
DEFAULT_USERNAME_ENV = "SCPLANTANNOTATE_USERNAME"
DEFAULT_PASSWORD_ENV = "SCPLANTANNOTATE_PASSWORD"
SCPLANTANNOTATE_PUBLICATION = {
    "name": "scPlantAnnotate",
    "pmid": "41554477",
    "doi": "10.1016/j.jare.2026.01.035",
    "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/41554477/",
    "official_web_server": BASE_URL,
}


ENDPOINTS = {
    "login": "/api/accounts/api/login/",
    "registration": "/api/accounts/api/registration/",
    "organisms": "/api/organisms/api/organism_query/",
    "predictors_public": "/api/predictors/api/predictor_query_public/",
    "h5ad_upload": "/api/h5addatasets/api/h5ad_dataset_upload/",
    "tenx_upload": "/api/tenxfeaturebcmatrixdatasets/api/tenxfbcm_dataset_upload/",
    "annotate_and_plot_job": "/api/jobs/api/job_annotate_and_plot/",
    "annotate_and_plot_query": "/api/jobs/api/job_annotate_and_plot_query/",
    "annotate_and_plot_file_output": "/api/jobs/api/job_annotate_and_plot_file_output_query_by_id/",
}
PREDICTION_COLUMN_CANDIDATES = [
    "prediction",
    "predicted_cell_type",
    "predicted_label",
    "cell_type_pred",
    "scplantannotate_prediction",
    "annotation",
]
CELL_ID_COLUMN_CANDIDATES = ["cell_id", "cell", "barcode", "obs_name", "index"]
TRUTH_COLUMN_CANDIDATES = ["cell_type", "label", "truth", "true_label", "celltype"]


def join_url(base_url: str, endpoint: str) -> str:
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))


def build_h5ad_upload_fields(
    *,
    dataset_name: str,
    organism_id: int | str,
    public_flag: int = 0,
) -> dict[str, str]:
    return {
        "h5ad_dataset_name": dataset_name,
        "h5ad_dataset_file_extension": "h5ad",
        "h5ad_dataset_organism": str(organism_id),
        "h5ad_dataset_public_flag": str(public_flag),
    }


def build_annotate_job_payload(
    *,
    predictor_id: int | str,
    dataset_id: int | str,
    dataset_name: str,
    dataset_type: str = "h5ad",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "job_predictor": predictor_id,
        "job_name": f"{dataset_name}_annotate&plot",
        "job_script": 2,
        "job_annotate_and_plot_stdout_filename": "Stdout001",
        "job_annotate_and_plot_stderr_filename": "Stderr001",
    }
    if dataset_type == "h5ad":
        payload["job_h5ad_dataset"] = dataset_id
    elif dataset_type == "10x":
        payload["job_tenxfbcm_dataset"] = dataset_id
    else:
        raise ValueError("dataset_type must be 'h5ad' or '10x'.")
    return payload


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def read_response(response: urllib.response.addinfourl) -> dict[str, Any]:
    text = response.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"raw_text": text[:2000]}
    return {
        "status": response.status,
        "url": response.geturl(),
        "content_type": response.headers.get("content-type", ""),
        "data": data,
    }


def multipart_body(
    *,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    boundary: str,
) -> bytes:
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def first_present(row: dict[str, str], candidates: list[str]) -> str:
    lowered = {key.lower(): key for key in row}
    for candidate in candidates:
        key = lowered.get(candidate.lower())
        if key is not None and str(row.get(key, "")).strip():
            return key
    return ""


def prediction_metrics_from_csv(
    *,
    prediction_csv: Path,
    truth_csv: Path,
    label_key: str = "",
    prediction_key: str = "",
    cell_id_key: str = "",
) -> dict[str, Any]:
    prediction_rows = read_csv_rows(prediction_csv)
    truth_rows = read_csv_rows(truth_csv)
    if not prediction_rows:
        raise ValueError(f"prediction CSV is empty: {prediction_csv}")
    if not truth_rows:
        raise ValueError(f"truth CSV is empty: {truth_csv}")

    prediction_cell_key = cell_id_key or first_present(prediction_rows[0], CELL_ID_COLUMN_CANDIDATES)
    truth_cell_key = cell_id_key or first_present(truth_rows[0], CELL_ID_COLUMN_CANDIDATES)
    prediction_label_key = prediction_key or first_present(
        prediction_rows[0],
        PREDICTION_COLUMN_CANDIDATES,
    )
    truth_label_key = label_key or first_present(truth_rows[0], TRUTH_COLUMN_CANDIDATES)
    if not prediction_cell_key or not truth_cell_key:
        raise ValueError("cell id column was not found in prediction or truth CSV")
    if not prediction_label_key:
        raise ValueError("prediction label column was not found")
    if not truth_label_key:
        raise ValueError("truth label column was not found")

    predictions = {
        str(row[prediction_cell_key]).strip(): str(row[prediction_label_key]).strip()
        for row in prediction_rows
        if str(row.get(prediction_cell_key, "")).strip()
        and str(row.get(prediction_label_key, "")).strip()
    }
    truths = {
        str(row[truth_cell_key]).strip(): str(row[truth_label_key]).strip()
        for row in truth_rows
        if str(row.get(truth_cell_key, "")).strip() and str(row.get(truth_label_key, "")).strip()
    }
    matched_ids = sorted(set(predictions) & set(truths))
    if not matched_ids:
        raise ValueError("prediction and truth CSVs have no overlapping cell ids")
    y_true = [truths[cell_id] for cell_id in matched_ids]
    y_pred = [predictions[cell_id] for cell_id in matched_ids]
    return {
        "method": "scplantannotate_authenticated_or_exported",
        "status": "metrics_ready",
        "prediction_csv": str(prediction_csv),
        "truth_csv": str(truth_csv),
        "label_key": truth_label_key,
        "prediction_key": prediction_label_key,
        "cell_id_key": prediction_cell_key,
        "test_cells": len(matched_ids),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "classes": sorted(set(y_true) | set(y_pred)),
    }


def extract_first_id(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ["id", "pk", "job_id", "dataset_id"]:
            value = payload.get(key)
            if value is not None and str(value).strip():
                return str(value)
        for value in payload.values():
            found = extract_first_id(value)
            if found:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = extract_first_id(value)
            if found:
                return found
    return ""


def job_completed(payload: Any) -> bool:
    text = json.dumps(payload, ensure_ascii=False).lower()
    return any(token in text for token in ["completed", "success", "finished", "done"])


def file_url_candidates(payload: Any, base_url: str) -> list[str]:
    urls: set[str] = set()
    if isinstance(payload, dict):
        for value in payload.values():
            urls.update(file_url_candidates(value, base_url))
    elif isinstance(payload, list):
        for value in payload:
            urls.update(file_url_candidates(value, base_url))
    elif isinstance(payload, str):
        value = payload.strip()
        if value.startswith("/"):
            urls.add(join_url(base_url, value))
        elif value.startswith("http://") or value.startswith("https://"):
            urls.add(value)
    return sorted(urls)


class ScPlantAnnotateClient:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def csrf_token(self) -> str:
        for cookie in self.cookies:
            if cookie.name == "csrftoken":
                return cookie.value
        return ""

    def request_json(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = None
        merged_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            merged_headers["Content-Type"] = "application/json"
        if headers:
            merged_headers.update(headers)
        request = urllib.request.Request(
            join_url(self.base_url, endpoint),
            data=body,
            method=method,
            headers=merged_headers,
        )
        with self.opener.open(request, timeout=60) as response:
            return read_response(response)

    def login(self, username: str, password: str) -> dict[str, Any]:
        return self.request_json(
            ENDPOINTS["login"],
            method="POST",
            payload={"username": username, "password": password},
        )

    def upload_h5ad(
        self,
        *,
        h5ad_path: Path,
        dataset_name: str,
        organism_id: int | str,
        public_flag: int = 0,
    ) -> dict[str, Any]:
        boundary = f"----snowcell{secrets.token_hex(12)}"
        body = multipart_body(
            fields=build_h5ad_upload_fields(
                dataset_name=dataset_name,
                organism_id=organism_id,
                public_flag=public_flag,
            ),
            file_field="h5ad_dataset_file",
            file_path=h5ad_path,
            boundary=boundary,
        )
        request = urllib.request.Request(
            join_url(self.base_url, ENDPOINTS["h5ad_upload"]),
            data=body,
            method="POST",
            headers={
                "User-Agent": USER_AGENT,
                "X-CSRFToken": self.csrf_token(),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        )
        with self.opener.open(request, timeout=300) as response:
            return read_response(response)

    def submit_annotate_job(
        self,
        *,
        predictor_id: int | str,
        dataset_id: int | str,
        dataset_name: str,
        dataset_type: str = "h5ad",
    ) -> dict[str, Any]:
        return self.request_json(
            ENDPOINTS["annotate_and_plot_job"],
            method="POST",
            payload=build_annotate_job_payload(
                predictor_id=predictor_id,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                dataset_type=dataset_type,
            ),
            headers={"X-CSRFToken": self.csrf_token()},
        )

    def query_annotate_jobs(self) -> dict[str, Any]:
        return self.request_json(ENDPOINTS["annotate_and_plot_query"])

    def query_annotate_job_outputs(self, job_id: str) -> dict[str, Any]:
        return self.request_json(
            ENDPOINTS["annotate_and_plot_file_output"],
            method="POST",
            payload={"id": job_id, "job_id": job_id, "job": job_id},
            headers={"X-CSRFToken": self.csrf_token()},
        )

    def download_file(self, url: str, output: Path) -> dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with self.opener.open(request, timeout=300) as response:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(response.read())
            return {
                "status": response.status,
                "url": response.geturl(),
                "content_type": response.headers.get("content-type", ""),
                "output": str(output),
                "bytes": output.stat().st_size,
            }


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input_h5ad) if args.input_h5ad else None
    prediction_csv = Path(args.prediction_csv) if getattr(args, "prediction_csv", None) else None
    truth_csv = Path(args.truth_csv) if getattr(args, "truth_csv", None) else None
    metrics_output = Path(
        getattr(
            args,
            "metrics_output",
            Path("outputs/external_benchmarks/scplantannotate_final_metrics.json"),
        )
    )
    output_path = Path(
        getattr(
            args,
            "output",
            Path("outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json"),
        )
    )
    execute_command = (
        "SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> "
        "python scripts/run_scplantannotate_authenticated_benchmark.py "
        f"--input-h5ad {input_path or '<benchmark.h5ad>'} "
        f"--dataset-name {args.dataset_name} "
        f"--organism-id {args.organism_id} "
        f"--predictor-id {args.predictor_id} "
        "--execute --wait "
        f"--output {output_path.as_posix()}"
    )
    metric_command = (
        "python scripts/run_scplantannotate_authenticated_benchmark.py "
        "--prediction-csv <scplantannotate_predictions.csv> "
        "--truth-csv <truth_labels.csv> "
        f"--metrics-output {metrics_output.as_posix()} "
        f"--output {output_path.as_posix()}"
    )
    return {
        "status": "dry_run_credentials_required",
        "method": "scplantannotate_authenticated_or_exported",
        "counts_as_completed_metric": False,
        "base_url": args.base_url,
        "publication": SCPLANTANNOTATE_PUBLICATION,
        "required_environment": {
            "username": args.username_env,
            "password": args.password_env,
            "username_present": bool(os.environ.get(args.username_env, "")),
            "password_present": bool(os.environ.get(args.password_env, "")),
        },
        "readiness_gates": {
            "authorized_account_available": bool(
                os.environ.get(args.username_env, "") and os.environ.get(args.password_env, "")
            ),
            "input_h5ad_available": bool(input_path and input_path.exists()),
            "organism_id_selected": bool(str(args.organism_id).strip()),
            "predictor_id_selected": bool(str(args.predictor_id).strip()),
            "prediction_export_available": bool(prediction_csv and prediction_csv.exists()),
            "truth_labels_available": bool(truth_csv and truth_csv.exists()),
            "metric_output_path": metrics_output.as_posix(),
        },
        "execute_requires": [
            "An authorized scPlantAnnotate account.",
            "A matching organism id from /api/organisms/api/organism_query/.",
            "A matching predictor id from /api/predictors/api/predictor_query_public/.",
            "An h5ad or 10x dataset accepted by the web server.",
        ],
        "post_submit_automation": [
            "Poll /api/jobs/api/job_annotate_and_plot_query/ for completion.",
            "Query /api/jobs/api/job_annotate_and_plot_file_output_query_by_id/ for downloadable outputs.",
            "Convert prediction CSV plus truth CSV into a metric JSON counted by benchmark audits.",
        ],
        "reproducible_commands": {
            "authorized_submit_and_wait": execute_command,
            "author_or_web_export_to_metric": metric_command,
        },
        "metric_acceptance_rule": (
            "Only outputs/external_benchmarks/scplantannotate_final_metrics.json "
            "or another scplantannotate JSON containing accuracy/macro_f1 metrics "
            "is counted as a completed external benchmark. This dry-run plan is "
            "excluded by benchmark-gap and status-summary audits."
        ),
        "endpoints": ENDPOINTS,
        "input_h5ad": {
            "path": str(input_path) if input_path else "",
            "exists": bool(input_path and input_path.exists()),
            "bytes": input_path.stat().st_size if input_path and input_path.exists() else 0,
        },
        "request_templates": {
            "login": {"username": "<env>", "password": "<env>"},
            "h5ad_upload_fields": build_h5ad_upload_fields(
                dataset_name=args.dataset_name,
                organism_id=args.organism_id,
                public_flag=args.public_flag,
            ),
            "annotate_job": build_annotate_job_payload(
                predictor_id=args.predictor_id,
                dataset_id="<uploaded_dataset_id>",
                dataset_name=args.dataset_name,
                dataset_type="h5ad",
            ),
            "job_output_query": {"id": "<job_id>", "job_id": "<job_id>", "job": "<job_id>"},
        },
        "source_basis": [
            "https://scplantannotate.missouri.edu/src/pages/SignIn.jsx",
            "https://scplantannotate.missouri.edu/src/components/Upload.jsx",
            "https://scplantannotate.missouri.edu/src/utils/predictionJobs.js",
        ],
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    username = os.environ.get(args.username_env, "")
    password = os.environ.get(args.password_env, "")
    if not username or not password:
        return {**dry_run_payload(args), "status": "missing_credentials"}
    if not args.input_h5ad:
        return {**dry_run_payload(args), "status": "missing_input_h5ad"}
    h5ad_path = Path(args.input_h5ad)
    if not h5ad_path.exists():
        return {**dry_run_payload(args), "status": "input_h5ad_not_found"}

    client = ScPlantAnnotateClient(args.base_url)
    login = client.login(username, password)
    if not login["data"].get("isLogin"):
        return {"status": "login_failed", "login": login}
    organisms = client.request_json(ENDPOINTS["organisms"])
    predictors = client.request_json(ENDPOINTS["predictors_public"])
    upload = client.upload_h5ad(
        h5ad_path=h5ad_path,
        dataset_name=args.dataset_name,
        organism_id=args.organism_id,
        public_flag=args.public_flag,
    )
    uploaded = upload["data"].get("H5adDatasetUpload") or upload["data"].get("h5ad_dataset") or {}
    dataset_id = uploaded.get("id") or args.dataset_id
    if not dataset_id:
        return {
            "status": "upload_completed_dataset_id_missing",
            "login": login,
            "organisms": organisms,
            "predictors": predictors,
            "upload": upload,
        }
    job = client.submit_annotate_job(
        predictor_id=args.predictor_id,
        dataset_id=dataset_id,
        dataset_name=args.dataset_name,
    )
    job_id = args.job_id or extract_first_id(job.get("data"))
    polls: list[dict[str, Any]] = []
    outputs: dict[str, Any] = {}
    downloads: list[dict[str, Any]] = []
    if args.wait and job_id:
        for _ in range(args.max_polls):
            poll = client.query_annotate_jobs()
            polls.append(poll)
            if job_completed(poll.get("data")):
                break
            time.sleep(args.poll_seconds)
        outputs = client.query_annotate_job_outputs(job_id)
        for index, url in enumerate(file_url_candidates(outputs.get("data"), client.base_url), start=1):
            suffix = Path(urllib.parse.urlparse(url).path).suffix or ".download"
            output_path = args.download_dir / f"scplantannotate_job_{job_id}_{index}{suffix}"
            downloads.append(client.download_file(url, output_path))
    return {
        "status": "submitted",
        "login": {"status": login["status"], "isLogin": login["data"].get("isLogin")},
        "organisms": organisms,
        "predictors": predictors,
        "upload": upload,
        "submitted_dataset_id": dataset_id,
        "submitted_job_id": job_id,
        "job": job,
        "polls": polls,
        "outputs": outputs,
        "downloads": downloads,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare or execute an authenticated scPlantAnnotate benchmark job."
    )
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--input-h5ad", default="")
    parser.add_argument("--dataset-name", default="snowcell_scplantannotate_probe")
    parser.add_argument("--organism-id", default="1")
    parser.add_argument("--predictor-id", default="1")
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--public-flag", default=0, type=int)
    parser.add_argument("--username-env", default=DEFAULT_USERNAME_ENV)
    parser.add_argument("--password-env", default=DEFAULT_PASSWORD_ENV)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--max-polls", default=120, type=int)
    parser.add_argument("--poll-seconds", default=30.0, type=float)
    parser.add_argument("--download-dir", default=Path("outputs/external_benchmarks/scplantannotate_downloads"), type=Path)
    parser.add_argument("--prediction-csv", default=None, type=Path)
    parser.add_argument("--truth-csv", default=None, type=Path)
    parser.add_argument("--label-key", default="")
    parser.add_argument("--prediction-key", default="")
    parser.add_argument("--cell-id-key", default="")
    parser.add_argument(
        "--metrics-output",
        default=Path("outputs/external_benchmarks/scplantannotate_final_metrics.json"),
        type=Path,
    )
    parser.add_argument(
        "--output",
        default="outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json",
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = execute(args) if args.execute else dry_run_payload(args)
    if args.prediction_csv is not None and args.truth_csv is not None:
        metrics = prediction_metrics_from_csv(
            prediction_csv=args.prediction_csv,
            truth_csv=args.truth_csv,
            label_key=args.label_key,
            prediction_key=args.prediction_key,
            cell_id_key=args.cell_id_key,
        )
        write_json(metrics, args.metrics_output)
        payload = {**payload, "metrics_output": str(args.metrics_output), "metrics": metrics}
    write_json(payload, args.output)
    print(args.output)
    if payload.get("metrics_output"):
        print(payload["metrics_output"])


if __name__ == "__main__":
    main()
