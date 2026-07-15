"""Minimal Drivion Publish client for Exe Runtime and DevKit integration."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import httpx


class PublishClient:
    def __init__(self, base_url: str, credential: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {credential}"},
            timeout=timeout,
        )

    def close(self) -> None:
        self.client.close()

    def deployment(self, equipment_id: str) -> dict[str, Any]:
        response = self.client.get(f"{self.base_url}/equipment/{equipment_id}/deployment")
        response.raise_for_status()
        return response.json()["data"]

    def download_autounit(
        self, equipment_id: str, destination: Path, expected_sha256: str
    ) -> Path:
        return self._download(
            f"/equipment/{equipment_id}/autounit/download",
            destination,
            expected_sha256,
        )

    def resolve_hal(self, equipment_id: str, name: str, version: str) -> dict[str, Any]:
        response = self.client.get(
            f"{self.base_url}/equipment/{equipment_id}/hal",
            params={"name": name, "version": version},
        )
        response.raise_for_status()
        return response.json()["data"]

    def download_hal(
        self,
        equipment_id: str,
        name: str,
        version: str,
        destination: Path,
        expected_sha256: str,
    ) -> Path:
        return self._download(
            f"/equipment/{equipment_id}/hal/download",
            destination,
            expected_sha256,
            params={"name": name, "version": version},
        )

    def submit_autounit(self, archive: Path) -> dict[str, Any]:
        return self._upload("POST", "/artifacts/autounit", archive)

    def update_autounit(self, artifact_id: str, archive: Path) -> dict[str, Any]:
        return self._upload("PUT", f"/artifacts/autounit/{artifact_id}", archive)

    def submit_hal(self, archive: Path) -> dict[str, Any]:
        return self._upload("POST", "/artifacts/hal", archive)

    def update_hal(self, artifact_id: str, archive: Path) -> dict[str, Any]:
        return self._upload("PUT", f"/artifacts/hal/{artifact_id}", archive)

    def _download(
        self,
        api_path: str,
        destination: Path,
        expected_sha256: str,
        params: dict[str, str] | None = None,
    ) -> Path:
        temporary = destination.with_suffix(destination.suffix + ".part")
        digest = hashlib.sha256()
        try:
            with self.client.stream("GET", f"{self.base_url}{api_path}", params=params) as response:
                response.raise_for_status()
                temporary.parent.mkdir(parents=True, exist_ok=True)
                with temporary.open("wb") as output:
                    for chunk in response.iter_bytes():
                        digest.update(chunk)
                        output.write(chunk)
            actual = digest.hexdigest()
            if actual != expected_sha256:
                raise ValueError(f"SHA-256 mismatch: expected={expected_sha256}, actual={actual}")
            temporary.replace(destination)
            return destination
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _upload(self, method: str, api_path: str, archive: Path) -> dict[str, Any]:
        with archive.open("rb") as package_file:
            response = self.client.request(
                method,
                f"{self.base_url}{api_path}",
                files={"file": (archive.name, package_file, "application/zip")},
            )
        response.raise_for_status()
        return response.json()["data"]
