from flask import Flask, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager
)
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.orm import relationship

# Создаем приложение Flask
app = Flask(__name__)

# Настройки приложения
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'  # База данных SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db = SQLAlchemy(app)
jwt = JWTManager(app)


# Модели базы данных

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50))
    year_of_publication = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    author = relationship("Author")


class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = relationship("Book")


# Аутентификация и авторизация

@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if username != 'admin' or password != 'password':
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


# Операции над книгами

@app.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    genre_filter = request.args.get('genre')

    query = Book.query.join(Author).add_columns(
        Book.id, Book.title, Book.genre, Book.year_of_publication, Author.name.label('author_name')
    )

    if genre_filter:
        query = query.filter(Book.genre == genre_filter)

    pagination = query.paginate(page, per_page, error_out=False)

    results = []
    for book in pagination.items:
        results.append({
            'id': book.id,
            'title': book.title,
            'genre': book.genre,
            'year_of_publication': book.year_of_publication,
            'author': book.author_name
        })

    return jsonify({
        'results': results,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@app.route('/books/<int:id>', methods=['GET'])
@jwt_required()
def get_book_by_id(id):
    book = Book.query.filter_by(id=id).first_or_404()
    return jsonify({
        'id': book.id,
        'title': book.title,
        'genre': book.genre,
        'year_of_publication': book.year_of_publication,
        'author_id': book.author_id
    }), 200


@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    new_book = Book(title=data['title'], genre=data['genre'], year_of_publication=data['year_of_publication'],
                    author_id=data['author_id'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': f'Book {new_book.title} has been created'}), 201


@app.route('/books/<int:id>', methods=['PUT'])
@jwt_required()
def update_book(id):
    book = Book.query.filter_by(id=id).first_or_404()
    data = request.get_json()
    book.title = data.get('title', book.title)
    book.genre = data.get('genre', book.genre)
    book.year_of_publication = data.get('year_of_publication', book.year_of_publication)
    book.author_id = data.get('author_id', book.author_id)
    db.session.commit()
    return jsonify({'message': f'Book with ID {id} has been updated'}), 200


@app.route('/books/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_book(id):
    book = Book.query.filter_by(id=id).first_or_404()
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': f'Book with ID {id} has been deleted'}), 200


if __name__ == '__main__':
    app.run(debug=True)