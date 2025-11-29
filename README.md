# Vehicle Parking System – MAD-2 Project

This project implements a complete multi-user parking management system using **Flask (Backend)**, **SQLite**, **Vue.js (Frontend)**, **Redis + Celery (Background Jobs)**, and **MailHog (Email Testing)**. It was developed as part of the **IITM BS Degree – Modern Application Development 2 (MAD-2)** course.

---

## 1. Overview

The Vehicle Parking System enables users to search parking lots, view available slots, make or release bookings, and export booking history.  
Administrators can manage parking lots, view all users, and trigger background jobs such as cleanup, daily reminders, and monthly activity reports.

---

## 2. Features

### 2.1 User Features
- User registration and login  
- Search parking lots by PIN code  
- View available parking slots  
- Book and release slots  
- View booking history  
- Export booking history as CSV (asynchronous Celery job)

### 2.2 Admin Features
- Create, edit, and delete parking lots  
- View registered users and their active/inactive status  
- Run background jobs:
  - Cleanup stale bookings  
  - Daily reminder emails  
  - Monthly activity report generation  
- Monitor system-level operations

---

## 3. Technology Stack

### Frontend
- Vue.js 3  
- Vue Router  
- Axios  
- Bootstrap 5  

### Backend
- Python 3  
- Flask  
- SQLAlchemy ORM  
- SQLite Database  

### Background Processing
- Redis  
- Celery  
- MailHog (Email testing)

---

## 4. Database Schema

Insert the generated ER diagram PNG image here:

<img width="1099" height="650" alt="DB-diagram" src="https://github.com/user-attachments/assets/0621f925-d9f0-4107-b3da-8b4d77d5615a" />


---

## 5. Project Folder Structure

vehicle-parking-app/
│
├── backend/
│ ├── app.py
│ ├── config.py
│ ├── celery_worker.py
│ ├── extensions.py
│ ├── models.py
│ ├── routes/
│ ├── exports/
│ └── reports/
│
└── frontend/
├── src/
├── router/
├── package.json
├── index.html
└── vite.config.js

## 6. Installation and Setup

### 6.1 Backend Setup
cd backend
pip install -r requirements.txt
python app.py

### 6.2 Start Redis
redis-server

### 6.3 Start Celery Worker
cd backend
celery -A celery_worker.celery worker --loglevel=info

### 6.4 Start Celery Beat
cd backend
celery -A celery_worker.celery beat --loglevel=info

### 6.5 Start MailHog
http://localhost:8025

### 6.6 Frontend Setup
cd frontend
npm install
npm run dev










