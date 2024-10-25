#!/usr/bin/env python3

# Standard library imports

# Remote library imports
from flask import request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime

# Local imports
from config import db, app, api
from models import User, Event, RSVP, Category

# Set secret key for sessions
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize bcrypt
bcrypt = Bcrypt(app)

# Helper function to check if user is an admin
def is_admin():
    user_id = session.get('user_id')
    if not user_id:
        return False
    user = User.query.get(user_id)
    print("User ID:", user_id, "Is Admin:", user.is_admin if user else "No user found")  # Debugging line
    return user.is_admin if user else False

# Resource for registering users
class Register(Resource):
    def post(self):
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return {"error": "Missing required fields"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "Email already exists"}, 400

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return user.to_dict(), 201

# Resource for login
class Login(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return {"message": "Login successful", "user": user.to_dict()}, 200
        else:
            return {"error": "Invalid credentials"}, 401

# Resource for event management (non-admin)
class EventList(Resource):
    def get(self):
        events = Event.query.all()
        return [event.to_dict() for event in events], 200

# Resource for event detail
class EventDetail(Resource):
    def get(self, event_id):
        event = Event.query.get(event_id)
        if not event:
            return {"error": "Event not found"}, 404
        return event.to_dict(), 200

# Resource for RSVP (non-admin)
class RSVPList(Resource):
    def get(self, event_id):
        rsvps = RSVP.query.filter_by(event_id=event_id).all()
        return [rsvp.to_dict() for rsvp in rsvps], 200
    
    def post(self, event_id):
        from models import RSVP, Event
        data = request.json
        status = data.get('status')
        user_id = session.get('user_id')

        if not user_id:
            return {"error": "Unauthorized"}, 401

        if status not in ['Attending', 'Not Attending']:
            return {"error": "Invalid RSVP status"}, 400

        rsvp = RSVP.query.filter_by(user_id=user_id, event_id=event_id).first()
        event = Event.query.get(event_id)

        if not event:
            return {"error": "Event not found"}, 404

        if not rsvp:
            if event.available_tickets > 0:
                # Create a new RSVP and decrement available tickets
                rsvp = RSVP(status=status, user_id=user_id, event_id=event_id)
                db.session.add(rsvp)
                event.available_tickets -= 1
                event.booked_tickets += 1
            else:
                return {"error": "No available tickets"}, 400
        else:
            # Update RSVP status only if changing to "Attending"
            if status == "Attending" and rsvp.status != "Attending":
                if event.available_tickets > 0:
                    event.available_tickets -= 1
                    event.booked_tickets += 1
                else:
                    return {"error": "No available tickets"}, 400
            elif status == "Not Attending" and rsvp.status == "Attending":
                # If changing to "Not Attending", adjust ticket counts
                event.available_tickets += 1
                event.booked_tickets -= 1

            rsvp.status = status

        db.session.commit()  # Commit changes to the database

        # Return the updated ticket information along with RSVP data
        return {
            "rsvp": rsvp.to_dict(),
            "available_tickets": event.available_tickets,
            "booked_tickets": event.booked_tickets
        }, 201
    
    def delete(self, event_id):
        user_id = session.get('user_id')

        if not user_id:
            return {"error": "Unauthorized"}, 401

        rsvp = RSVP.query.filter_by(user_id=user_id, event_id=event_id).first()

        if not rsvp:
            return {"error": "RSVP not found"}, 404

        db.session.delete(rsvp)
        db.session.commit()

        return {"message": "RSVP canceled"}, 200

# Resource for managing the list of users RSVPs
class UserRsvps(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            return {"error": "Unauthorized"}, 401

        rsvps = RSVP.query.filter_by(user_id=user_id).all()
        return [rsvp.to_dict() for rsvp in rsvps], 200

# Resource for categories
class CategoryList(Resource):
    def get(self):
        categories = Category.query.all()
        return [category.to_dict() for category in categories], 200
    
# Resource for user list
class UserList(Resource):
    def get(self):
        users = User.query.all()
        return [user.to_dict() for user in users], 200
 
# Admin-specific dashboard for managing events and attendees
class AdminDashboard(Resource):
    def get(self):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403

        events = Event.query.all()
        rsvps = RSVP.query.all()

        return {
            "events": [event.to_dict() for event in events],
            "attendees": [rsvp.to_dict() for rsvp in rsvps]
        }, 200

# Admin-specific route for managing events
class AdminEvent(Resource):
    def post(self):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403

        data = request.json
        title = data.get('title')
        description = data.get('description')
        date_of_event = data.get('date_of_event')  # Ensure this is in 'YYYY-MM-DD' format
        location = data.get('location')
        available_tickets = data.get('available_tickets')  # Accept available_tickets field
        image_url = data.get('image_url')
        category_id = data.get('category_id')
        time_str = data.get('time')  # Accept time field in 'HH:MM' format

        # Convert time string to a time object
        if time_str:
            try:
                time_object = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                return {"error": "Invalid time format, should be HH:MM"}, 400
        else:
            return {"error": "Time field is required"}, 400

        # Create a new Event instance
        event = Event(
            title=title,
            description=description,
            date_of_event=date_of_event,
            time=time_object,  # Use the time object
            location=location,
            available_tickets=available_tickets,
            image_url=image_url,
            category_id=category_id,
            user_id=session.get('user_id')  # Ensure session management is handled
        )

        db.session.add(event)
        db.session.commit()

        return event.to_dict(), 201

class AdminEventDetail(Resource):
    def patch(self, event_id):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403

        data = request.json
        event = Event.query.get(event_id)

        if not event:
            return {"error": "Event not found"}, 404

        # Update fields with the provided data, if available
        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.date_of_event = data.get('date_of_event', event.date_of_event)

        # Handle time update
        time_str = data.get('time')
        if time_str:
            try:
                event.time = datetime.strptime(time_str, '%H:%M').time()  # Convert to time object
            except ValueError:
                return {"error": "Invalid time format, should be HH:MM"}, 400
        
        event.location = data.get('location', event.location)
        event.available_tickets = data.get('available_tickets', event.available_tickets)
        event.image_url = data.get('image_url', event.image_url)

        db.session.commit()
        return event.to_dict(), 200

    def delete(self, event_id):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403

        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
            return {"message": "Event deleted"}, 200
        else:
            return {"error": "Event not found"}, 404    

# Admin-specific route for viewing attendees
class AdminEventAttendees(Resource):
    def get(self, event_id):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403

        rsvps = RSVP.query.filter_by(event_id=event_id).all()
        return [rsvp.to_dict() for rsvp in rsvps], 200

# Resource for logout
class Logout(Resource):
    def post(self):
        session.pop('user_id', None)
        return {"message": "Logged out"}, 200

# Check admin status
class CheckAdminStatus(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user and user.is_admin:
                return {"isAdmin": True}, 200
        return {"isAdmin": False}, 200


# Add the API resources to the app
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(EventList, '/events')
api.add_resource(EventDetail, '/events/<int:event_id>')
api.add_resource(RSVPList, '/events/<int:event_id>/rsvps')
api.add_resource(UserRsvps, '/events/my-rsvps')
api.add_resource(CategoryList, '/categories')
api.add_resource(UserList, '/user')

# Admin routes
api.add_resource(AdminDashboard, '/admin/dashboard')
api.add_resource(AdminEvent, '/admin/dashboard/event')
api.add_resource(AdminEventDetail, '/admin/dashboard/event/<int:event_id>')
api.add_resource(AdminEventAttendees, '/admin/dashboard/event/<int:event_id>/attendees')
api.add_resource(CheckAdminStatus, '/check-admin-status')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
