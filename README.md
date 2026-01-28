# 🚀 Candidate Management System (CMS)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)
![Django](https://img.shields.io/badge/Django-5.0+-green?style=flat&logo=django)
![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205-purple?style=flat&logo=bootstrap)
![Status](https://img.shields.io/badge/Status-Deployed-success)

## 📋 Project Overview
A robust, Role-Based Access Control (RBAC) system designed to streamline the recruitment process. This application allows HR staff to bulk import candidates via Excel, schedule interviews efficiently using range-based selection, and automate status transitions. It features a fully responsive custom dashboard and a secure portal for candidates to check their application status.

**Live Demo:** [render](https://candidate-system.onrender.com/)
---

## 🔐 Quick Start / Demo Access
Use the credentials below to test the different roles within the system:

| Role | Email / Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin1234` | **Full Access:** CRUD, Scheduling, Hiring, Role Management. |
| **Staff** | `staff1` | `Admin@2024Secure!` | **Restricted:** Upload Excel, View Lists, Download Phones. No Edit/Delete. |
| **Candidate** | `johndoe@example.com` | `9175551234` | **Read Only:** Can only view personal application status. |

> **Note for Candidate Login:** Candidates are automatically created upon Excel upload. The **Password** is set to their **Phone Number** (digits only, no spaces/dashes).

---

## ✅ Requirement Fulfillment Matrix
This project was built to strictly adhere to the IGL Web Team's specifications. Here is how each requirement was implemented:

### 1. Excel File Processing
| Requirement | Implementation Detail |
| :--- | :--- |
| **Input:** Excel file with candidate list. | Integrated `pandas` and `openpyxl` for robust file parsing. |
| **Data Extraction:** Name, Email, Phone, Exp, Institute, Age. | Data is cleaned, and phone numbers are normalized using Regex (`re`). |
| **Storage:** Save to DB (`candidates` table). | Mapped Excel columns to Django models. |
| **JSON Storage:** Previous Experience. | Implemented `models.JSONField` to store dynamic key-value pairs of "Institute: Position". |

### 2. Admin Panel Features
| Requirement | Implementation Detail |
| :--- | :--- |
| **View/Edit/Delete:** List with actions. | Full CRUD operations implemented. Staff is restricted from Edit/Delete via `user_passes_test` decorators. |
| **Filtering:** Separate lists (Hired, Rejected). | Dynamic filtering implemented (`/candidates/hired`, `/candidates/rejected`). |
| **Schedule Interviews:** Checkbox & Range (2-10). | Built a custom form handling both specific IDs (checkbox) and ID Ranges (e.g., "5-15") in a single transaction. |
| **Upcoming List:** Auto-move if date passed. | Logic implemented in views: `Interview.objects.filter(date__lt=now).update(status='completed')`. Runs automatically on page load. |
| **Download Phones:** File generation. | Implemented a feature to export phone numbers of upcoming candidates into a `.txt` file. |
| **Status Management:** Pass/Reject/2nd Round. | Workflow buttons added to "Completed Interviews" for seamless status transition. |

### 3. Roles & Permissions (RBAC)
| Role | Implementation Detail |
| :--- | :--- |
| **Admin** | Superuser status. Access to all routes, including `delete`, `edit`, and `hire`. |
| **Staff** | `is_staff=True`. Access to Upload, Dashboard, and Lists. Buttons for critical actions are hidden/disabled. |
| **Candidate** | Automatic User creation linked to Candidate Profile. Can only access the `Check Status` portal. |

---

## 🛠 Tech Stack & Design Choices

### Backend
*   **Framework:** Django (Python) - *Chosen for rapid development and secure built-in authentication.*
*   **Database:** PostgreSQL (Production) / SQLite (Dev) - *configured via `dj_database_url`.*
*   **Data Processing:** Pandas - *Used for efficient bulk processing of Excel rows.*

### Frontend
*   **Framework:** Bootstrap 5 - *Ensures a fully responsive mobile-first design.*
*   **Templating:** Django Jinja2 - *Server-side rendering for security and speed.*

### Key Design Decisions
1.  **Candidate Authentication:** To avoid a complex registration flow for candidates, the system **automatically creates a User account** when an Excel file is uploaded. The Candidate's **Email** becomes the Username, and **Phone Number** (normalized) becomes the Password.
2.  **Transactional Integrity:** Excel uploads and Bulk Scheduling use `transaction.atomic()`. If one record fails (e.g., duplicate email), the entire batch rolls back to prevent data inconsistency.
3.  **JSON Field for Experience:** Instead of creating a separate table for "Previous Experience," a JSONField was used. This allows flexibility if a candidate has 1 company or 10 companies without schema changes.

---

## 💻 Local Installation Guide

Follow these steps to run the project on your local machine.

### Prerequisites
*   Python 3.10+
*   Git
