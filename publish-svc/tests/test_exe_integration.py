import io
import json
import tempfile
import unittest
import zipfile

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.exe import (
    get_equipment_deployment,
    replace_autounit_artifact,
    submit_autounit_artifact,
    submit_hal_artifact,
)
from app.core.config import settings
from app.core.database import Base
from app.core.integration_auth import IntegrationPrincipal, require_integration_permission
from app.models.facility import Equipment, Factory, Line, Station
from app.models.package import AutoUnitPackage, DriverPackage
from app.models.publish import EquipmentAutoUnitBinding


def _zip(files: dict[str, str]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return stream.getvalue()


class ExeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.storage_dir = tempfile.TemporaryDirectory()
        self.original_storage_dir = settings.LOCAL_STORAGE_DIR
        settings.LOCAL_STORAGE_DIR = self.storage_dir.name
        self.local_principal = IntegrationPrincipal(
            subject="integration:test", username="integration-test"
        )

    async def asyncTearDown(self) -> None:
        settings.LOCAL_STORAGE_DIR = self.original_storage_dir
        self.storage_dir.cleanup()
        await self.engine.dispose()

    def test_scope_matches_equipment_ancestor_and_rejects_other_line(self) -> None:
        principal = IntegrationPrincipal(
            subject="client:execution",
            username="execution",
            auth_source="sso",
            permissions={"platform.equipment.read"},
            permission_grants=[{
                "permission": "platform.equipment.read",
                "scopeType": "line",
                "scopeId": "line-a",
            }],
        )
        resources = [("equipment", "eq-a"), ("station", "station-a"), ("line", "line-a")]
        require_integration_permission(principal, "platform.equipment.read", resources)
        with self.assertRaises(HTTPException) as context:
            require_integration_permission(
                principal,
                "platform.equipment.read",
                [("equipment", "eq-b"), ("line", "line-b")],
            )
        self.assertEqual(403, context.exception.status_code)

    async def test_deployment_returns_exact_bound_unpublished_version(self) -> None:
        async with self.sessions() as db:
            db.add_all([
                Factory(id="site-a", name="一厂", code="SITE-A", status="active", is_deleted=0, create_user_id="u"),
                Line(id="line-a", factory_id="site-a", name="A 线", code="LINE-A", status="active", is_deleted=0, create_user_id="u"),
                Station(id="station-a", line_id="line-a", name="上料工位", code="ST-A", status="active", is_deleted=0, create_user_id="u"),
                Equipment(id="eq-a", station_id="station-a", name="上料机", code="EQ-A", status="active", is_deleted=0, create_user_id="u"),
                AutoUnitPackage(
                    id="au-a", name="long-autounit-name", package_id="demo.logic", version="1.2.3",
                    module="demo_logic", file_name="demo.zip", size=10, file_path="autounit/au-a/package.zip",
                    status="testing", deleted=0, locked=True, storage_provider="local", md5="a" * 32,
                    sha256="b" * 64, upload_user_id="u",
                ),
            ])
            await db.flush()
            db.add(EquipmentAutoUnitBinding(
                id="binding-a", equipment_id="eq-a", package_id="au-a", bind_user_id="u"
            ))
            await db.flush()

            response = await get_equipment_deployment("eq-a", db, self.local_principal)
            self.assertEqual("demo.logic", response.data.autoUnit.packageId)
            self.assertEqual("1.2.3", response.data.autoUnit.version)
            self.assertFalse(response.data.autoUnit.published)
            self.assertIn("testing", response.data.autoUnit.releaseWarning)
            self.assertEqual("line-a", response.data.equipment.line["id"])

    async def test_devkit_submission_parses_metadata_and_creates_pending_versions(self) -> None:
        auto_content = _zip({
            "project/drivion.project.json": json.dumps({
                "name": "Demo AutoUnit",
                "package_id": "demo.autounit",
                "version": "0.2.0",
                "module": "demo_autounit",
                "dependencies": [{"name": "demo-hal", "version": "1.0.0"}],
            })
        })
        hal_content = _zip({
            "driver/pyproject.toml": """
[project]
name = "demo-hal"
version = "1.0.0"

[project.entry-points."drivion.hal_drivers"]
main = "demo_hal.driver:register"
""".strip()
        })
        async with self.sessions() as db:
            auto_response = await submit_autounit_artifact(
                UploadFile(filename="demo-autounit.zip", file=io.BytesIO(auto_content)),
                db,
                self.local_principal,
            )
            hal_response = await submit_hal_artifact(
                UploadFile(filename="demo-hal.zip", file=io.BytesIO(hal_content)),
                db,
                self.local_principal,
            )
            await db.commit()

            auto = await db.get(AutoUnitPackage, auto_response.data["id"])
            hal = await db.get(DriverPackage, hal_response.data["id"])
            self.assertEqual(("demo.autounit", "0.2.0", "pending_testing"), (auto.package_id, auto.version, auto.status))
            self.assertEqual(("demo-hal", "1.0.0", "pending_testing"), (hal.name, hal.version, hal.status))
            self.assertEqual(hal.sha256, hal_response.data["sha256"])

            replacement = _zip({
                "drivion.project.json": json.dumps({
                    "name": "Demo AutoUnit Updated",
                    "package_id": "demo.autounit",
                    "version": "0.2.0",
                    "module": "demo_autounit",
                })
            })
            replaced = await replace_autounit_artifact(
                auto.id,
                UploadFile(filename="demo-autounit-updated.zip", file=io.BytesIO(replacement)),
                db,
                self.local_principal,
            )
            self.assertEqual("Demo AutoUnit Updated", replaced.data["name"])
            self.assertEqual("pending_testing", replaced.data["status"])


if __name__ == "__main__":
    unittest.main()
