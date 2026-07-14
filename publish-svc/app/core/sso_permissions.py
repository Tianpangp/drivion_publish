"""将 SSO 权限快照映射为发布系统界面权限。"""
from app.core.permissions import Permission


SSO_PERMISSION_MAP: dict[str, set[str]] = {
    Permission.FACILITY_FACTORY_VIEW.value: {"platform.site.read"},
    Permission.FACILITY_FACTORY_CREATE.value: {"platform.site.create"},
    Permission.FACILITY_FACTORY_EDIT.value: {"platform.site.update"},
    Permission.FACILITY_FACTORY_DELETE.value: {"platform.site.delete"},
    Permission.FACILITY_LINE_VIEW.value: {"platform.line.read"},
    Permission.FACILITY_LINE_CREATE.value: {"platform.line.create"},
    Permission.FACILITY_LINE_EDIT.value: {"platform.line.update"},
    Permission.FACILITY_LINE_DELETE.value: {"platform.line.delete"},
    Permission.FACILITY_STATION_VIEW.value: {"platform.station.read"},
    Permission.FACILITY_STATION_CREATE.value: {"platform.station.create"},
    Permission.FACILITY_STATION_EDIT.value: {"platform.station.update"},
    Permission.FACILITY_STATION_DELETE.value: {"platform.station.delete"},
    Permission.FACILITY_EQUIPMENT_VIEW.value: {"platform.equipment.read"},
    Permission.FACILITY_EQUIPMENT_MANAGE.value: {
        "platform.equipment.create", "platform.equipment.update", "platform.equipment.delete"
    },
    Permission.BINDING_VIEW.value: {"platform.equipment.read"},
    Permission.BINDING_AUTOUNIT_MANAGE.value: {"platform.equipment.update"},
    Permission.AUTOUNIT_VIEW.value: {"autounit.definition.read"},
    Permission.AUTOUNIT_DOWNLOAD.value: {"artifact.package.download"},
    Permission.AUTOUNIT_UPLOAD.value: {"autounit.definition.upload"},
    Permission.AUTOUNIT_UPDATE.value: {"autounit.definition.update"},
    Permission.AUTOUNIT_DELETE.value: {"autounit.definition.delete"},
    Permission.AUTOUNIT_SUBMIT_TEST.value: {"autounit.definition.submit"},
    Permission.AUTOUNIT_SUBMIT_PUBLISH.value: {"release.request.create"},
    Permission.AUTOUNIT_SUBMIT_REMOVE.value: {"release.request.create"},
    Permission.DRIVER_VIEW.value: {"hal.driver.read"},
    Permission.DRIVER_DOWNLOAD.value: {"hal.driver.download", "artifact.package.download"},
    Permission.DRIVER_UPLOAD.value: {"hal.driver.upload"},
    Permission.DRIVER_UPDATE.value: {"hal.driver.update"},
    Permission.DRIVER_DELETE.value: {"hal.driver.delete"},
    Permission.DRIVER_SUBMIT_TEST.value: {"hal.driver.submit"},
    Permission.DRIVER_SUBMIT_PUBLISH.value: {"release.request.create"},
    Permission.DRIVER_SUBMIT_REMOVE.value: {"release.request.create"},
    Permission.APPROVAL_TEST_VIEW.value: {"autounit.test.read", "hal.test.read"},
    Permission.APPROVAL_TEST_REVIEW.value: {"autounit.test.approve", "hal.test.approve"},
    Permission.APPROVAL_RELEASE_VIEW.value: {"release.request.read"},
    Permission.APPROVAL_RELEASE_REVIEW.value: {"release.request.approve"},
    Permission.LOG_VIEW.value: {"release.request.read", "iam.audit.read"},
    Permission.LOG_EXPORT.value: {"iam.audit.export"},
}


def map_sso_permissions(permissions: list[str], roles: list[str]) -> set[str]:
    if "platform.super_admin" in roles:
        return {item.value for item in Permission}
    source = set(permissions)
    return {
        internal for internal, external_options in SSO_PERMISSION_MAP.items()
        if source.intersection(external_options)
    }
