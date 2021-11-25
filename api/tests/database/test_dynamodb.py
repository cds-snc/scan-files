from database.dynamodb import get_scan_result, log_scan_result
from unittest.mock import patch


@patch("database.dynamodb.get_session")
def test_get_dynamodb_record_exists(mock_aws_session):
    mock_aws_session().resource().Table().get_item.return_value = {"Item": "foo"}
    response = get_scan_result("123")
    assert response is True


@patch("database.dynamodb.get_session")
def test_get_dynamodb_doesnt_exst(mock_aws_session):
    mock_aws_session().resource().Table().get_item.return_value = {}
    response = get_scan_result("123")
    assert response is False


@patch("database.dynamodb.get_session")
def test_insert_dynamodb_record(mock_aws_session):
    mock_aws_session().resource().Table().put_item.return_value = {"Item": "foo"}
    response = log_scan_result("123")
    assert response is True


@patch("database.dynamodb.get_session")
def test_insert_dynamodb_record_random_error(mock_aws_session):
    mock_aws_session().resource().Table().put_item.side_effect = Exception

    response = log_scan_result("123")
    assert response is False
