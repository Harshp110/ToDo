# 📝 Ticklyy – Advanced To-Do & Task Management App (Flask + SQLAlchemy)

Ticklyy is a full-stack productivity application built using **Flask**,  
featuring user authentication, Kanban-style task management, file uploads,  
subtasks, reminders, analytics dashboard, and Excel export.

This project demonstrates backend engineering, ORM modeling, secure authentication,  
file handling, REST APIs, and real-world cloud deployment using **Render + Gunicorn**.

---

## 🚀 Features

### 🔐 Authentication & Security
- Secure signup & login using **Flask-Login**
- Password hashing using **Werkzeug (PBKDF2)**
- Session-based authentication
- Protected routes using `@login_required`

---

## 🗂️ Task Management
- Create, edit, delete todos
- Priority & category support
- Due dates & reminders
- Add subtasks
- Mark complete / incomplete
- Automatic ordering with "position" field

---

## 🚀 Kanban Board
Drag-and-drop Kanban UI with three columns:
- **To-Do**
- **In-Progress**
- **Done**

Kanban state is saved in the database via REST endpoints.

---

## 📎 File Attachments
- Upload images, PDFs, text files, documents
- Uses `secure_filename()` for safe uploads
- Files stored in `/uploads`
- Attachment metadata stored in DB

---

## 📊 Dashboard & Analytics
Backend-generated analytics using Python:
- Total tasks
- Completed vs Pending
- Category distribution
- Priority distribution
- Last 7 days completion graph

---

## 📤 Export to Excel
Export all tasks to `.xlsx` using **openpyxl**:
- Serial number
- Title
- Description
- Priority
- Category
- Due date
- Completion state
- Timestamp

---

## 🧠 Optional AI Integration
Automatic task summary using **OpenAI API** (if API key is provided).

---

## 🧱 Tech Stack

### 🔥 Backend
- Python 3
- Flask (routing + views)
- SQLAlchemy ORM
- Flask-Login (authentication)
- Werkzeug (security + safe filenames)
- Pathlib (file handling)
- OpenPyXL (Excel export)

### 🎨 Frontend
- HTML5 + CSS3
- Jinja2 templating
- JavaScript (AJAX for REST calls)

### ☁ Deployment
- Render Cloud Hosting
- Gunicorn WSGI server
- Procfile-based startup
- requirements.txt for dependency management

---

## 📁 Project Structure

