import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """Initialize the database with tables and a default user."""
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User(username='bob', email='bob@mail.com', password='bobpass')
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username: str = typer.Argument(..., help="The username of the user to retrieve")):
    """Retrieve a user by their exact username."""
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """Retrieve and list all users in the database."""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(
    username: str = typer.Argument(..., help="The username of the user to update"),
    new_email: str = typer.Argument(..., help="The new email address to assign to the user")
):
    """Update the email address of an existing user."""
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: str = typer.Argument(..., help="The username for the new user"),
    email: str = typer.Argument(..., help="The email address for the new user"),
    password: str = typer.Argument(..., help="The password for the new user")
):
    """Create a new user and add them to the database."""
    with get_session() as db: # Get a connection to the database
        newuser = User(username=username, email=email, password=password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command()
def delete_user(username: str = typer.Argument(..., help="The username of the user to delete")):
    """Delete a user from the database by their username."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

# Exercise 1 - Search for a user by partial match of username or email
@cli.command()
def search_users(query: str = typer.Argument(..., help="Partial username or email to search for")):
    """Find users by a partial match of their username or email."""
    with get_session() as db:
        users = db.exec(
            select(User).where(
                (User.username.contains(query)) | (User.email.contains(query))
            )
        ).all()
        if not users:
            print(f"No users found matching '{query}'")
            return
        for user in users:
            print(user)

# Exercise 2 - List the first N users with pagination support
@cli.command()
def list_users(
    limit: int = typer.Argument(10, help="Maximum number of users to return (default: 10)"),
    offset: int = typer.Argument(0, help="Number of users to skip before returning results (default: 0)")
):
    """List users from the database using limit and offset for pagination."""
    with get_session() as db:
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        if not users:
            print("No users found.")
            return
        for user in users:
            print(user)

if __name__ == "__main__":
    cli()