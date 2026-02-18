# server/models.py
# Model-level validations for the lab.
# Tests expect ValueError to be raised for invalid inputs.

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy import inspect

db = SQLAlchemy()

# Post title must contain at least ONE of these phrases
CLICKBAIT_PHRASES = ["Won't Believe", "Secret", "Top", "Guess"]

# Post category must be exactly one of these
ALLOWED_CATEGORIES = ["Fiction", "Non-Fiction"]


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)

    # DB-level constraints (still keep these):
    # - unique=True enforces uniqueness at the DB
    # - nullable=False enforces not-null at the DB
    name = db.Column(db.String, unique=True, nullable=False)

    # Store as string to preserve leading zeros and validate digits easily
    phone_number = db.Column(db.String)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # ---------- VALIDATORS ----------

    @validates("name")
    def validate_name(self, key, value):
        """
        Rules:
        1) Name is required (non-empty)
        2) Name must be unique (raise ValueError on duplicate)
        Note: During very early test setup, tables might not exist yet.
              We guard by checking if the table exists before querying.
        """
        # required name
        if value is None or str(value).strip() == "":
            raise ValueError("Author must have a name.")

        # Use the SESSION bind (reliable in Flask test/app contexts)
        bind = db.session.get_bind()
        inspector = inspect(bind)

        # Only query for duplicates if the authors table exists
        if "authors" in inspector.get_table_names():
            existing = Author.query.filter(Author.name == value).first()
            if existing is not None:
                raise ValueError("Author name must be unique.")

        return value

    @validates("phone_number")
    def validate_phone_number(self, key, value):
        """
        Rule:
        - phone number must be exactly 10 digits (digits only)
        """
        # Not tested, but reasonable to allow missing phone number
        if value is None:
            return value

        value_str = str(value)

        if len(value_str) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")

        if not value_str.isdigit():
            raise ValueError("Phone number must contain digits only.")

        return value_str

    def __repr__(self):
        return f"Author(id={self.id}, name={self.name})"


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)

    # Tests require title to be present (non-empty)
    title = db.Column(db.String, nullable=False)

    # Tests require min length 250 via validator
    content = db.Column(db.String)

    # Tests require category in ALLOWED_CATEGORIES
    category = db.Column(db.String)

    # Tests require summary max length 250 (summary optional)
    summary = db.Column(db.String)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # ---------- VALIDATORS ----------

    @validates("title")
    def validate_title(self, key, value):
        """
        Rules:
        1) title required (non-empty)
        2) must contain at least one clickbait phrase:
           "Won't Believe", "Secret", "Top", "Guess"
        """
        if value is None or str(value).strip() == "":
            raise ValueError("Post must have a title.")

        if not any(phrase in value for phrase in CLICKBAIT_PHRASES):
            raise ValueError("Title must contain clickbait keywords.")

        return value

    @validates("content")
    def validate_content(self, key, value):
        """
        Rule:
        - content must be at least 250 characters
        """
        if value is None:
            raise ValueError("Post must have content.")

        if len(value) < 250:
            raise ValueError("Content must be at least 250 characters.")

        return value

    @validates("summary")
    def validate_summary(self, key, value):
        """
        Rule:
        - summary max 250 characters
        Summary is optional.
        """
        if value is None:
            return value

        if len(value) > 250:
            raise ValueError("Summary must be 250 characters or fewer.")

        return value

    @validates("category")
    def validate_category(self, key, value):
        """
        Rule:
        - category must be exactly "Fiction" or "Non-Fiction"
        """
        if value not in ALLOWED_CATEGORIES:
            raise ValueError("Category must be Fiction or Non-Fiction.")

        return value

    def __repr__(self):
        return (
            f"Post(id={self.id}, title={self.title} content={self.content}, summary={self.summary})"
        )
