from fastapi.testclient import TestClient
from backend.main import app
import pytest
import time

client = TestClient(app)
BASE_URL = "/api/chat/ask"


# ----------------------------------
# BASIC FUNCTIONAL TESTS
# ----------------------------------
def test_valid_query():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "What is AI?"})
    assert res.status_code == 200
    assert "answer" in res.json()


def test_valid_different_questions():
    questions = [
        "Explain Python",
        "What is DBMS?",
        "Latest AI trends",
        "Explain recursion",
        "What is cloud computing?"
    ]
    for q in questions:
        res = client.post(BASE_URL, json={"user_id": 1, "question": q})
        assert res.status_code == 200


# ----------------------------------
# VALIDATION TESTS
# ----------------------------------
def test_missing_question():
    res = client.post(BASE_URL, json={"user_id": 1})
    assert res.status_code == 422


def test_missing_user_id():
    res = client.post(BASE_URL, json={"question": "What is AI?"})
    assert res.status_code == 422


def test_invalid_type_question():
    res = client.post(BASE_URL, json={"user_id": 1, "question": 123})
    assert res.status_code == 422


def test_invalid_type_user():
    res = client.post(BASE_URL, json={"user_id": "abc", "question": "AI"})
    assert res.status_code == 422


# ----------------------------------
# EDGE CASES
# ----------------------------------
@pytest.mark.parametrize("query, expected_status", [
    ("", 422),
    (" ", 200),
    ("     ", 200),
    ("\n", 200),
    ("\t", 200),
    ("\r\n", 200),
    (" \t ", 200),
])
def test_empty_like_inputs(query, expected_status):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == expected_status


@pytest.mark.parametrize("query", [
    "AI", "Hi", "DB", "ML", "Go"
])
def test_short_queries(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


@pytest.mark.parametrize("query", [
    "AI " * 200,
    "Python " * 300,
    "Data Science " * 150,
])
def test_long_queries(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


# ----------------------------------
# SPECIAL CHARACTER TESTS
# ----------------------------------
@pytest.mark.parametrize("query", [
    "@@@###$$$",
    "!!!???",
    "&&&&&&",
    "<script>alert(1)</script>",
    "{}[]()<>",
    "~~~^^^|||"
])
def test_special_characters(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


# ----------------------------------
# SECURITY TESTS
# ----------------------------------
@pytest.mark.parametrize("query", [
    "' OR 1=1 --",
    "' DROP TABLE users;",
    "SELECT * FROM users;",
    "UNION SELECT password FROM users",
])
def test_sql_injection(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code in [200, 400]


@pytest.mark.parametrize("query", [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "<iframe src='evil.com'></iframe>"
])
def test_xss_inputs(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


# ----------------------------------
# USER TESTS
# ----------------------------------
@pytest.mark.parametrize("user_id", [1, 2, 3, 4])
def test_valid_users(user_id):
    res = client.post(BASE_URL, json={"user_id": user_id, "question": "AI"})
    assert res.status_code == 200


@pytest.mark.parametrize("user_id", [9999, 123456, -1])
def test_invalid_users(user_id):
    res = client.post(BASE_URL, json={"user_id": user_id, "question": "AI"})
    assert res.status_code in [200, 404]


def test_null_user():
    res = client.post(BASE_URL, json={"user_id": None, "question": "AI"})
    assert res.status_code in [200, 422]


# ----------------------------------
# PERFORMANCE TESTS
# ----------------------------------
def test_response_time():
    start = time.time()
    res = client.post(BASE_URL, json={"user_id": 1, "question": "AI"})
    end = time.time()
    assert res.status_code == 200
    assert (end - start) < 6


# ----------------------------------
# STRESS / LOAD TESTS
# ----------------------------------
def test_multiple_requests():
    for _ in range(7):
        res = client.post(BASE_URL, json={"user_id": 1, "question": "Python"})
        assert res.status_code == 200


def test_repeated_same_query():
    q = "What is Python?"
    for _ in range(3):
        res = client.post(BASE_URL, json={"user_id": 1, "question": q})
        assert res.status_code == 200


# ----------------------------------
# RANDOM INPUT TESTS
# ----------------------------------
@pytest.mark.parametrize("query", [
    "asdkjasdkj",
    "zzzzzzzzzz",
    "qwertyuiop",
    "random123",
    "xyz987"
])
def test_random_inputs(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


# ----------------------------------
# RESPONSE STRUCTURE TESTS
# ----------------------------------
def test_response_structure():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "AI"})
    data = res.json()
    assert isinstance(data, dict)
    assert "answer" in data


def test_response_not_empty():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "AI"})
    assert res.json().get("answer") != ""


# ----------------------------------
# MIXED TESTS
# ----------------------------------
@pytest.mark.parametrize("query", [
    "AI!!!???",
    "   Python   ",
    "Explain @ AI #2025",
    "AI 2025 trends!!!",
    "   @@Python##   "
])
def test_mixed_inputs(query):
    res = client.post(BASE_URL, json={"user_id": 1, "question": query})
    assert res.status_code == 200


# ----------------------------------
# EXTRA 3 TESTS (TO MAKE TOTAL 60)
# ----------------------------------
def test_numeric_string_query():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "123456"})
    assert res.status_code == 200


def test_alphanumeric_query():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "AI123"})
    assert res.status_code == 200


def test_unicode_query():
    res = client.post(BASE_URL, json={"user_id": 1, "question": "人工智能"})
    assert res.status_code == 200