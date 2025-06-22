# GitLab Classroom Application - Setup and Run Instructions

The **GitLab Classroom application** is a full-stack web tool developed as part of my thesis. It is designed to improve the management of classroom activities, assignments, and the assessment of student projects, labs, and tasks for teachers and professors of the Faculty of Electronics and Information Sciences at the Warsaw University of Technology.

By utilizing the powerful version control and project management functions of GitLab, along with the GitLab API, this application helps address the challenges of managing and evaluating assignments, providing timely feedback, and facilitating collaboration in programming projects.

## Prerequisites

Before running the GitLab Classroom application, make sure you have the following installed on your system:

1. **Python 3.8+**: You can download Python from [python.org](https://www.python.org/downloads/).
2. **Git**: Ensure Git is installed to clone the repository. You can download it from [git-scm.com](https://git-scm.com/downloads).
3. **Virtualenv**: It's recommended to use a virtual environment for managing dependencies. You can install it using:
   ```bash
   pip install virtualenv
   ```
## Setting Up the Environment

1. **Create a virtual environment**:
   ```bash
   virtualenv venv
   ```
3. **Activate the virtual environment**:
   *Windows*:
   ```bash
   venv\Scripts\activate
   ```
   *macOS/Linux*:
   ```bash
   source venv/bin/activate
   ```
5. **Install the required dependencies using pip**:
   ```bash
   pip install -r requirements.txt
   ```
7. **Apply the migrations to set up the database**:
   ```bash
   python manage.py migrate
   ```
10. **(Optional) If you want to load initial data, use**:
    ```bash
    python manage.py loaddata initial_data.json
    ```
12. **Start the Django development server**:
    ```bash
    python manage.py runserver
    ```
14. **Open your web browser and navigate to [site](http://127.0.0.1:8000/) to access the application**.

erDiagram
    TEACHER {
        int     id           PK
        string  username
        string  email
        string  gitlab_id    UNIQUE
    }
    STUDENT {
        int     id           PK
        string  gitlab_id
        string  gitlab_username  UNIQUE
        string  first_name
        string  second_name
        string  email
        string  student_id
        bool    gl_flag
    }
    CLASSROOM {
        int       id           PK
        string    title        UNIQUE
        text      description
        string    organization
        int       gitlab_id
        datetime  creation_date
        int       created_by   FK → TEACHER.id
    }
    -- tabele pośrednie dla M2M
    CLASSROOM_TEACHERS {
        int classroom_id  FK → CLASSROOM.id
        int teacher_id    FK → TEACHER.id
    }
    CLASSROOM_STUDENTS {
        int classroom_id  FK → CLASSROOM.id
        int student_id    FK → STUDENT.id
    }

    ASSIGNMENT {
        int       id           PK
        string    title        UNIQUE
        text      description
        url       repo_url
        int       gitlab_id
        datetime  creation_date
        datetime  deadline
        bool      is_group
        int       template_id
        int       classroom_id FK → CLASSROOM.id
    }
    ASSIGNMENT_STUDENTS {
        int assignment_id FK → ASSIGNMENT.id
        int student_id    FK → STUDENT.id
    }
    ASSIGNMENT_TEACHERS {
        int assignment_id FK → ASSIGNMENT.id
        int teacher_id    FK → TEACHER.id
    }

    ASSESSMENT {
        int      id           PK
        int      assignment_id FK → ASSIGNMENT.id
        int      student_id    FK → STUDENT.id
        int      teacher_id    FK → TEACHER.id
        string   score
        text     feedback
        datetime assessed_at
    }

    GROUPPROJECT {
        int     id              PK
        string  name            UNIQUE
        text    description
        int     gitlab_group_id
        int     assignment_id   FK → ASSIGNMENT.id
    }
    GROUPPROJECT_STUDENTS {
        int groupproject_id FK → GROUPPROJECT.id
        int student_id      FK → STUDENT.id
    }
    GROUPPROJECT_TEACHERS {
        int groupproject_id FK → GROUPPROJECT.id
        int teacher_id      FK → TEACHER.id
    }

    %% relacje
    TEACHER ||--o{ CLASSROOM            : "creates"
    TEACHER ||--o{ CLASSROOM_TEACHERS   : "teaches"
    TEACHER ||--o{ ASSIGNMENT_TEACHERS  : "teaches"
    TEACHER ||--o{ ASSESSMENT           : "gives"
    TEACHER ||--o{ GROUPPROJECT_TEACHERS: "oversees"

    STUDENT ||--o{ CLASSROOM_STUDENTS   : "attends"
    STUDENT ||--o{ ASSIGNMENT_STUDENTS  : "submits"
    STUDENT ||--o{ ASSESSMENT           : "receives"
    STUDENT ||--o{ GROUPPROJECT_STUDENTS: "participates"

    CLASSROOM ||--o{ ASSIGNMENT          : "contains"
    ASSIGNMENT ||--o{ ASSESSMENT          : "has"
    ASSIGNMENT ||--o{ GROUPPROJECT        : "spawns"

