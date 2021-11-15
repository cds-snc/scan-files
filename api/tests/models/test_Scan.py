from models.Scan import Scan


def test_scan_model():
    scan = Scan(
        file_name="file_name",
        file_size=100,
        save_path="save_path",
        sha256="sha256",
        scan_provider="scan_provider",
        submitter="submitter",
        verdict="clean",
        quarantine_path="quarantine_path",
        meta_data={}
    )
    assert scan.file_name == "file_name"
    assert scan.file_size == 100
    assert scan.save_path == "save_path"
    assert scan.sha256 == "sha256"
    assert scan.scan_provider == "scan_provider"
    assert scan.submitter == "submitter"
    assert scan.verdict == "clean"
    assert scan.quarantine_path == "quarantine_path"
    assert scan.meta_data == {}


def test_scan_model_saved(session):
    scan = Scan(
        file_name="file_name",
        file_size=100,
        save_path="save_path",
        sha256="sha256",
        scan_provider="scan_provider",
        submitter="submitter",
        verdict="clean",
        quarantine_path="quarantine_path",
        meta_data={}
    )
    session.add(scan)
    session.commit()
    assert scan.file_name == "file_name"
    assert scan.id is not None
    assert scan.submitted is not None
    session.delete(scan)
    session.commit()
