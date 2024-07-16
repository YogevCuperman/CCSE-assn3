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


# -----------------------------------------------------------------\

res1 = requests.post(books_url, json=book1)
print(res1.json())

res2 = requests.post(books_url, json=book2)
print(res2.json())

res3 = requests.post(books_url, json=book3)
print(res3.json())

res6 = requests.post(books_url, json=book6)
print(res6.json())

res7 = requests.post(books_url, json=book7)
print(res7.json())

res8 = requests.post(books_url, json=book8)
print(res8.json())