from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

# ----------------------------------------------------------------------------------------
# SETUPS

# flask app setup
app = Flask(__name__)

# database setup
mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client["books_lib"]
library = db["library"]
ratings = db["ratings"]

# constant data
post_book_fields = ['title', 'ISBN', 'genre']
update_book_fields = ['_id', 'title', 'authors', 'ISBN', 'publisher', 'publishedDate', 'genre']


# ----------------------------------------------------------------------------------------
# ROUTING

@app.route("/")
def hello():
    return "<h1>Welcome to my books API :)</h1>"


@app.route("/books", methods=['GET', 'POST'])
def handle_books():
    if request.method == 'GET':
        filters = {}
        for name, value in request.args.items():
            filters[name] = value

        search_results = []
        for book in library.find(filters):
            book_json = {}
            for field, value in book.items():
                if field == '_id':
                    book_json[field] = str(value)
                else:
                    book_json[field] = value
            search_results.append(book_json)

        if len(search_results) == 0:
            return jsonify("There are no books matching the selected filters."), 200
        return search_results, 200

    elif request.method == 'POST':
        try:
            info = request.get_json()
        except:
            return jsonify("Invalid JSON."), 415

        isbn_num = info['ISBN']

        if check_if_book_exist(isbn_num):
            return jsonify("This book already exist in the library."), 422

        if not check_valid_genre(info['genre']):
            return jsonify("Invalid book genre."), 422

        if not check_valid_fields(info, post_book_fields):
            return jsonify("Invalid JSON fields."), 422

        # Make a request to Google books API to get additional information
        google_books_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_num}'

        try:
            google_books_response = requests.get(google_books_url)
        except:
            return jsonify("Unable to connect to Google."), 500

        try:
            google_books_data = google_books_response.json()['items'][0]['volumeInfo']
        except:
            if google_books_response.json()['totalItems'] == 0:
                return jsonify({"error": "no items returned from Google Book API for given ISBN number"}), 400

        authors_str = ", ".join(google_books_data.get("authors"))
        book = {
            "ISBN": isbn_num,
            "title": info["title"],
            "genre": info["genre"],
            "authors": authors_str,
            "publisher": google_books_data.get("publisher"),
            "publishedDate": google_books_data.get("publishedDate")
        }

        library.insert_one(book)
        book_id = str(library.find_one({"ISBN": isbn_num}).get('_id'))

        rating_json = {
            "values": [],
            "average": 0,
            "title": info["title"],
            "id": book_id
        }

        ratings.insert_one(rating_json)

        return jsonify({"ID": str(book_id)}), 201


@app.route("/books/<id>", methods=['GET', 'DELETE', 'PUT'])
def handle_book_with_id(id):
    if library.count_documents({'_id': ObjectId(id)}) == 0:
        return jsonify(f'{id} is not a recognized book id'), 404

    try:
        if request.method == 'GET':
            result = library.find_one({'_id': ObjectId(id)})
            book_json = {}
            for field, value in result.items():
                if field == '_id':
                    book_json[field] = str(value)
                else:
                    book_json[field] = value

            return book_json, 200

        elif request.method == 'DELETE':
            library.delete_one({'_id': ObjectId(id)})
            ratings.delete_one({'id': id})
            return jsonify({"ID": str(id)}), 200

        elif request.method == 'PUT':
            try:
                updated_info = request.get_json()
            except:
                return jsonify("Invalid JSON."), 415

            if not check_valid_genre(updated_info['genre']):
                return jsonify("Invalid book genre."), 422

            if not check_valid_fields(updated_info, update_book_fields):
                return jsonify("Invalid JSON fields."), 422

            json_without_id = {}
            for field, value in updated_info.items():

                if field != '_id':
                    json_without_id[field] = value
            library.update_one({'_id': ObjectId(id)}, {"$set": json_without_id})

            return jsonify({"ID": str(id)}), 200

    except Exception as e:
        return jsonify(f"Internal server error: {e}."), 500


@app.route("/ratings", methods=['GET'])
def handle_ratings():
    search_results = []
    filter = {}
    if 'id' in request.args.keys():
        filter['id'] = request.args.get('id')

    for r in ratings.find(filter):
        rate_json = {}
        for field, value in r.items():
            if field != '_id':
                rate_json[field] = value
        search_results.append(rate_json)

    return search_results, 200


@app.route("/ratings/<id>", methods=['GET'])
def handle_ratings_with_id(id):
    if ratings.count_documents({'id': id}) == 0:
        return jsonify(f'{id} is not a recognized book id'), 404

    rate_json = {}
    for field, value in ratings.find_one({'id': id}).items():
        if field != '_id':
            rate_json[field] = value

    return rate_json, 200


@app.route("/ratings/<id>/values", methods=['POST'])
def handle_rate_post(id):
    if ratings.count_documents({'id': id}) == 0:
        return jsonify(f'{id} is not a recognized book id'), 404

    try:
        new_value = request.get_json()['value']
    except:
        return jsonify("Invalid rating JSON."), 422

    if new_value not in list(range(1, 6)):
        return jsonify("Invalid rating value."), 422

    rating = ratings.find_one({'id': id})
    values = rating['values']
    values.append(new_value)
    new_average = sum(values) / len(values)

    updated_json = {
        "id": id,
        "title": rating['title'],
        "values": values,
        "average": new_average
    }

    ratings.update_one({'id': id}, {"$set": updated_json})

    return jsonify(new_average), 201


@app.route("/top", methods=['GET'])
def handle_top():
    top = []
    last_avg = 0
    # filter out book ratings with less than 3 ratings
    relevant_books = ratings.find({"values.2": {"$exists": True}}).sort("average", -1)

    for i, book in enumerate(relevant_books):
        if i < 3:
            top.append(create_top_element_json(book))
            last_avg = book['average']

        # there are more than 3 on the top response only if there are more books with the same average
        else:
            if book['average'] == last_avg:
                top.append(create_top_element_json(book))

    return jsonify(top), 200


# ----------------------------------------------------------------------------------------
# AUXILIARY METHODS


def check_if_book_exist(isbn):
    return library.count_documents({"ISBN": isbn}) > 0


def check_valid_genre(genre):
    return genre in ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']


def check_valid_fields(json, fields):
    fields_set = set(fields)
    json_keys_set = set(json.keys())
    return json_keys_set.issubset(fields_set) and fields_set.issubset(json_keys_set)


def create_top_element_json(json):
    return {
        "id": json['id'],
        "title": json['title'],
        "average": json['average']
    }


# ----------------------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8090)

