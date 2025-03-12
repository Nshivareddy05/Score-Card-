import sqlite3
import streamlit as st
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("flight_reservation.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS Passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    seats_available INTEGER NOT NULL,
    price REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_id INTEGER,
    flight_id INTEGER,
    status TEXT DEFAULT 'Booked',
    FOREIGN KEY (passenger_id) REFERENCES Passengers(passenger_id),
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id)
)
''')

conn.commit()

# Streamlit UI
st.title("✈️ Flight Reservation System")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Book a Flight", "Manage Flights", "Manage Tickets", "View Data"])

# ------------------ Book a Flight ------------------
if menu == "Book a Flight":
    st.subheader("📌 Book a Flight Ticket")

    # Show available flights
    cursor.execute("SELECT * FROM Flights WHERE seats_available > 0")
    flights = cursor.fetchall()
    if flights:
        df_flights = pd.DataFrame(flights, columns=["Flight ID", "Airline", "Origin", "Destination", "Departure", "Seats", "Price"])
        st.dataframe(df_flights)

        # Booking Form
        name = st.text_input("Enter Your Name")
        email = st.text_input("Enter Your Email")
        flight_id = st.number_input("Enter Flight ID to Book", min_value=1, step=1)

        if st.button("Confirm Booking"):
            try:
                cursor.execute("INSERT INTO Passengers (name, email) VALUES (?, ?)", (name, email))
                passenger_id = cursor.lastrowid
                cursor.execute("INSERT INTO Tickets (passenger_id, flight_id) VALUES (?, ?)", (passenger_id, flight_id))
                cursor.execute("UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id = ?", (flight_id,))
                conn.commit()
                st.success("✅ Booking Confirmed!")
            except:
                st.error("⚠️ Error in booking. Check details.")

# ------------------ Manage Flights ------------------
elif menu == "Manage Flights":
    st.subheader("🛫 Manage Flights")

    # Add Flight
    with st.form("add_flight"):
        airline = st.text_input("Airline Name")
        origin = st.text_input("Origin")
        destination = st.text_input("Destination")
        departure_time = st.text_input("Departure Time")
        seats_available = st.number_input("Available Seats", min_value=1, step=1)
        price = st.number_input("Ticket Price", min_value=0.0, step=100.0)
        add_flight_btn = st.form_submit_button("Add Flight")

    if add_flight_btn:
        cursor.execute("INSERT INTO Flights (airline, origin, destination, departure_time, seats_available, price) VALUES (?, ?, ?, ?, ?, ?)", 
                       (airline, origin, destination, departure_time, seats_available, price))
        conn.commit()
        st.success("✅ Flight Added Successfully!")

    # Remove Flight
    flight_id_to_remove = st.number_input("Enter Flight ID to Remove", min_value=1, step=1)
    if st.button("Remove Flight"):
        cursor.execute("DELETE FROM Flights WHERE flight_id = ?", (flight_id_to_remove,))
        conn.commit()
        st.warning("🗑️ Flight Removed!")

# ------------------ Manage Tickets ------------------
elif menu == "Manage Tickets":
    st.subheader("📃 Manage Tickets")

    # Show booked tickets
    cursor.execute('''SELECT t.ticket_id, p.name, f.airline, f.origin, f.destination, t.status 
                      FROM Tickets t 
                      JOIN Passengers p ON t.passenger_id = p.passenger_id 
                      JOIN Flights f ON t.flight_id = f.flight_id''')
    tickets = cursor.fetchall()

    if tickets:
        df_tickets = pd.DataFrame(tickets, columns=["Ticket ID", "Passenger", "Airline", "Origin", "Destination", "Status"])
        st.dataframe(df_tickets)

        # Cancel Ticket
        ticket_id = st.number_input("Enter Ticket ID to Cancel", min_value=1, step=1)
        if st.button("Cancel Ticket"):
            cursor.execute("UPDATE Tickets SET status = 'Cancelled' WHERE ticket_id = ?", (ticket_id,))
            cursor.execute("UPDATE Flights SET seats_available = seats_available + 1 WHERE flight_id = (SELECT flight_id FROM Tickets WHERE ticket_id = ?)", (ticket_id,))
            conn.commit()
            st.warning("❌ Ticket Cancelled!")

# ------------------ View Data ------------------
elif menu == "View Data":
    st.subheader("📊 View All Data")

    # Show all flights
    st.write("### ✈️ Available Flights")
    cursor.execute("SELECT * FROM Flights")
    flights = cursor.fetchall()
    if flights:
        df_flights = pd.DataFrame(flights, columns=["Flight ID", "Airline", "Origin", "Destination", "Departure", "Seats", "Price"])
        st.dataframe(df_flights)
    else:
        st.write("No flights available.")

    # Show all bookings
    st.write("### 🎟️ Booked Tickets")
    cursor.execute('''SELECT t.ticket_id, p.name, f.airline, f.origin, f.destination, t.status 
                      FROM Tickets t 
                      JOIN Passengers p ON t.passenger_id = p.passenger_id 
                      JOIN Flights f ON t.flight_id = f.flight_id''')
    tickets = cursor.fetchall()
    if tickets:
        df_tickets = pd.DataFrame(tickets, columns=["Ticket ID", "Passenger", "Airline", "Origin", "Destination", "Status"])
        st.dataframe(df_tickets)
    else:
        st.write("No tickets booked.")

