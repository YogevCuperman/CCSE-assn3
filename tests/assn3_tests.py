import pytest
import requests

# -----------------------------------------------------------------
# books and static data:

books_url = "http://127.0.0.1:5001/books"

book1 = {
    "title": "Adventures of Huckleberry Finn",
    "ISBN": "9780520343641",
    "genre": "Fiction"
}

book2 = {
    "title": "The Best of Isaac Asimov",
    "ISBN": "9780385050784",
    "genre": "Science Fiction"
}

book3 = {
    "title": "Fear No Evil",
    "ISBN": "9780394558783",
    "genre": "Biography"
}

book4 = {
    "title": "No such book",
    "ISBN": "0000001111111",
    "genre": "Biography"
}

book5 = {
    "title": "The Greatest Joke Book Ever",
    "authors": "Mel Greene",
    "ISBN": "9780380798490",
    "genre": "Jokes"
}

book6 = {
    "title": "The Adventures of Tom Sawyer",
    "ISBN": "9780195810400",
    "genre": "Fiction"
}

book7 = {
    "title": "I, Robot",
    "ISBN": "9780553294385",
    "genre": "Science Fiction"
}

book8 = {
    "title": "Second Foundation",
    "ISBN": "9780553293364",
    "genre": "Science Fiction"
}

IDs = {}

# -----------------------------------------------------------------


@pytest.fixture
def create_books():
    response1 = requests.post(books_url, json=book1)
    response2 = requests.post(books_url, json=book2)
    response3 = requests.post(books_url, json=book3)
    return response1, response2, response3


def test_1(create_books):
    res1, res2, res3 = create_books
    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res3.status_code == 201

    IDs[1] = res1.json().get('ID')
    IDs[2] = res2.json().get('ID')
    IDs[3] = res3.json().get('ID')

    assert IDs[1] is not None
    assert IDs[2] is not None
    assert IDs[3] is not None
    assert IDs[1] != IDs[2]
    assert IDs[1] != IDs[3]
    assert IDs[2] != IDs[3]


def test_2():
    response = requests.get(f"{books_url}/{IDs[1]}")
    assert response.status_code == 200
    assert response.json().get('authors') == 'Mark Twain'


def test_3():
    response = requests.get(books_url)
    assert response.status_code == 404
    assert len(response.json()) == 3


def test_4():
    response = requests.post(books_url, json=book4)
    code = response.status_code
    assert code == 400 or code == 500

def test_5():
    response = requests.delete(f"{books_url}/{IDs[2]}")
    assert response.status_code == 200


def test_6():
    response = requests.get(f"{books_url}/{IDs[2]}")
    assert response.status_code == 404


def test_7():
    response = requests.post(books_url, json=book5)
    assert response.status_code == 422
    
