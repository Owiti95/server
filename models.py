from sqlalchemy.ext.associationproxy import association_proxy  # Helps create a proxy to simplify many-to-many relationships
from sqlalchemy.orm import validates  # Provides validation hooks for model attributes
from config import db
from sqlalchemy import MetaData, Table  # MetaData for schema definition & table for defining association tables
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt
import re


bcrypt = Bcrypt()


metadata = MetaData()


class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = ('-events', '-rsvps.user', '-rsvps.event') # exclude circular references when serializing
    
    # Define columns in the users table
    id = db.Column(db.Integer, primary_key=True)  # Primary key as unique identifier
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)  # password hash for secure storagerequired
    is_admin = db.Column(db.Boolean, default=False)  # Boolean field to check if the user is an admin
    
    

    # one user can have multiple RSVPs (One-to-Many relationship)
    rsvps = db.relationship('RSVP', back_populates='user')
    
    # one user can create multiple events (One-to-Many relationship)
    events = db.relationship('Event', back_populates='user')



    # Email validation method
    @validates('email')
    def validate_email(self, key, email):
        # Regular expression for validating an email
        valid_email = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(valid_email, email):
            raise ValueError("Invalid email")
        return email



    # method to set password (hashes the password using bcrypt)
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # method to check if the entered password matches the hashed password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    # string representation of the User object
    def __repr__(self):
        return f'<User {self.name}, Name: {self.name}, Email: {self.email}>'

# Association table for the Many-to-Many relationship between Event and Category
# This table has two columns: event_id and category_id, both of which are foreign keys that form the composite primary key
event_categories = Table('event_categories', db.Model.metadata,
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),  # Foreign key to the events table
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)  # Foreign key to the categories table
)


class Event(db.Model, SerializerMixin):
    __tablename__ = 'events'

    serialize_rules = ('-user.events', '-rsvps.event', '-categories.events')
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    date_of_event = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)  # Add image URL field
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    time = db.Column(db.Time, nullable=False) 
    booked_tickets = db.Column(db.Integer, default=0)  # Default to 0
    available_tickets = db.Column(db.Integer, default=0)

    # one event can have multiple RSVPs (one-to-many relationship)
    rsvps = db.relationship('RSVP', back_populates='event')  # Connects Event with RSVP
    
    # many-to-many relationship between event and category
    categories = db.relationship('Category', secondary=event_categories, back_populates='events')

    # adding back_populates to define the inverse relationship with the user
    user = db.relationship('User', back_populates='events')

    def __repr__(self):
        return f'<Event {self.title}, Description: {self.description}, Date of Event: {self.date_of_event}, Location: {self.location}>'


class RSVP(db.Model, SerializerMixin):
    __tablename__ = 'rsvps'

    serialize_rules = ('-user.rsvps', '-event.rsvps', '-user.events')
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String, nullable=False)  # RSVP status
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # foreign key linking to the user who RSVPed
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)  # foreign key linking to the event

    
    # RSVP is linked to User (many-to-one relationship)
    user = db.relationship('User', back_populates='rsvps')
    
    # RSVP is linked to Event (many-to-one relationship)
    event = db.relationship('Event', back_populates='rsvps')

    # predefined valid statuses for RSVPs
    VALID_STATUSES = ['Attending', 'Not Attending']

    # validation method for RSVP status checks if the provided status is valid
    @validates('status')
    def validate_status(self, key, status):
        if status not in self.VALID_STATUSES:
            raise ValueError("Status must be 'Attending' or 'Not Attending'")
        return status

    def __repr__(self):
        return f'<RSVP {self.status} by User {self.user_id} for Event {self.event_id}>'

class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'

    serialize_rules = ('-events.categories','-events.user')
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    # many-to-many relationship between category and event
    events = db.relationship('Event', secondary=event_categories, back_populates='categories')


    def __repr__(self):
        return f'<Category {self.name}>'