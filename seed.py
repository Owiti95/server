from config import db, app
from models import User, Event, RSVP, Category
from datetime import datetime, time
from flask_bcrypt import Bcrypt

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt()

print("Starting seed...")

# Use the application context to access the database
with app.app_context():
    # Drop all existing tables and create new ones
    db.drop_all()
    db.create_all()
    print("Created all tables.")

    # Create categories first
    try:
        categories = [
            Category(name="Competition"),
            Category(name="Sales"),
            Category(name="Show"),
            Category(name="Experience"),
            Category(name="Gaming"),
        ]
        
        # Add categories to the session and commit
        db.session.add_all(categories)
        db.session.commit()
        print("Categories added successfully.")
    except Exception as e:
        print(f"Error creating categories: {e}")

    # Create users manually
    try:
        users = [
            User(name="Purity", email="purity@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Hannington", email="hannington@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Isaac", email="isaac@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Elsie", email="elsie@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Baimet", email="baimet@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="AdminUser", email="adminuser@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8'), is_admin=True),
        ]
        
        # Add all users to the session and commit
        db.session.add_all(users)
        db.session.commit()
        print("Users added successfully.")
    except Exception as e:
        print(f"Error creating users: {e}")

    # Create events manually
    try:
        events = [
            Event(
                title="Formula 1 Tournament",
                description="Join fellow motorsport enthusiasts for an experience of Formula 1 excitement simulation",
                date_of_event=datetime(2024, 11, 1).date(),  # Only the date
                time=time(14, 0),  # Example: 2 PM
                location="Gamers Arcade",
                image_url="https://www.affordableluxurytravel.co.uk/blog/wp-content/uploads/2024/08/formula-1-race.jpg",
                user_id=1,
                booked_tickets=0,  # Initialize with 0 booked tickets
                available_tickets=100  # Example: 100 tickets available
            ),
            Event(
                title="Off Road Adventure",
                description="An off-road adventure with 4x4 vehicles",
                date_of_event=datetime(2024, 11, 15).date(),
                time=time(10, 0),  # Example: 10 AM
                location="Lodwar",
                image_url="https://play-lh.googleusercontent.com/yzzfCuM1q4tRbG1GhH5Z07m6yMNGFxQ7yN3x8E9nzznBioNAPX6nAJO8ccg7we3OnIuJ",
                user_id=2,
                booked_tickets=0,
                available_tickets=50
            ),
            Event(
                title="Car Auction",
                description="Get the best deals",
                date_of_event=datetime(2024, 12, 10).date(),
                time=time(18, 0),  # Example: 6 PM
                location="Nairobi",
                image_url="https://gusarov-group.by/wp-content/uploads/2019/04/bidcar-auction-9.jpg",
                user_id=3,
                booked_tickets=0,
                available_tickets=200
            ),
            Event(
                title="Expo",
                description="Explore and discover",
                date_of_event=datetime(2024, 12, 5).date(),
                time=time(11, 30),  # Example: 11:30 AM
                location="Nairobi",
                image_url="https://static.autox.com/uploads/2023/01/Toyota-BZ4X-EV-1-.jpg",
                user_id=4,
                booked_tickets=0,
                available_tickets=150
            ),
            Event(
                title="Turbo Dogs",
                description="Top drivers compete",
                date_of_event=datetime(2024, 12, 20).date(),
                time=time(19, 0),  # Example: 7 PM
                location="Kisumu",
                image_url="https://b1858697.smushcdn.com/1858697/wp-content/uploads/2018/05/9story-Turbo-Dogs-006.jpg?lossy=1&strip=1&webp=1",
                user_id=5,
                booked_tickets=0,
                available_tickets=75
            ),
            Event(
                title="Racing Championship",
                description="Top drivers compete",
                date_of_event=datetime(2024, 12, 25).date(),
                time=time(16, 0),  # Example: 4 PM
                location="Nairobi",
                image_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSU03EzR5PraKLFJPEttBZX45SXG5fDQxI4Qg&s",
                user_id=6,
                booked_tickets=0,
                available_tickets=120
            ),
        ]
        
        # Add events to the session
        db.session.add_all(events)
        db.session.commit()
        print("Events added successfully.")
    except Exception as e:
        print(f"Error creating events: {e}")

    # Create RSVPs manually
    try:
        rsvps = [
            RSVP(status="Attending", user_id=1, event_id=1),
            RSVP(status="Not Attending", user_id=2, event_id=2),
            RSVP(status="Attending", user_id=3, event_id=3),
            RSVP(status="Attending", user_id=4, event_id=4),
            RSVP(status="Not Attending", user_id=5, event_id=5),
            RSVP(status="Attending", user_id=6, event_id=6),
        ]
        
        # Add RSVPs to the session and commit
        db.session.add_all(rsvps)
        db.session.commit()
        print("RSVPs added successfully.")
    except Exception as e:
        print(f"Error creating RSVPs: {e}")

    # Associate events and categories
    try:
        event_category_associations = [
            (1, 5),  # Formula 1 Tournament is a Gaming event
            (2, 4),  # Off Road Adventure is an Experience event
            (3, 2),  # Car Auction is a Sales event
            (4, 3),  # Expo is a Show event
            (5, 1),  # Turbo Dogs is a Competition event
            (6, 5),  # Racing Championship is a Gaming event
        ]

        # Loop through associations and append categories to events
        for event_id, category_id in event_category_associations:
            event = db.session.get(Event, event_id)
            category = db.session.get(Category, category_id)
            if event and category:
                event.categories.append(category)

        # Commit associations to the database
        db.session.commit()
        print("Events and categories associated successfully.")
    except Exception as e:
        print(f"Error associating events and categories: {e}")

print("Seeding complete.")
