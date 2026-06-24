# FastAPI Library Management System

A FastAPI for managing users, books, universities, and departments with JWT authentication and MongoDB as the database.

## Features

### User Management
- ✅ User registration
- ✅ User login with JWT token generation
- ✅ Role assignment to users (admin, librarian, student, etc.)
- ✅ User filtering by role
- ✅ University and department assignment to users
- ✅ Get user details including:
  - Username
  - University name
  - Department
  - Assigned books

### Book Management
- ✅ Create books
- ✅ Assign books to departments
- ✅ Get all books

### University Management
- ✅ Create universities
- ✅ Get list of all universities
- ✅ Get departments assigned to a university

### Department Management
- ✅ Create departments
- ✅ Assign departments to universities
- ✅ Get list of all departments
- ✅ Get books assigned to a department

## Technologies Used

- **Backend**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT (JSON Web Tokens)
- **Python Libraries**:
  - PyMongo (MongoDB driver)
  - Passlib (password hashing)
  - Python-JOSE (JWT implementation)
  - 

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:AdeelMalik22/UniversityManagementSystem.git