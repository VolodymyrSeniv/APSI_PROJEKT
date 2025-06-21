from django.db import models
from django.contrib.auth.models import AbstractUser
from gitlab_service import settings
from django.urls import reverse


class Teacher(AbstractUser): #teacher database model
    gitlab_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.first_name} - {self.gitlab_id}"


class Student(models.Model): #student database model
    gitlab_id = models.CharField(max_length=255)
    gitlab_username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length = 100)
    email = models.EmailField()
    student_id = models.CharField(max_length=255, default="0")
    gl_flag = models.BooleanField(default=False)

    class Meta:
        ordering = ["-first_name"]

    def __str__(self):
        return f"{self.gitlab_username} - {self.gitlab_id}"

    def get_absolute_url(self):#getting the url
        return reverse("gitlab_classroom:student-detail", args=[str(self.id)])


class Classroom(models.Model): #classroom database model
    title = models.CharField(max_length=255, unique=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    organization = models.CharField(max_length=255, blank=False)
    gitlab_id = models.IntegerField(default=0, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name="classroom_created_by"
        )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="classroom_teachers"
    )
    students = models.ManyToManyField(Student, related_name="classroom")

    class Meta:#ordering
        ordering = ["-creation_date"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):#getting the url
        return reverse("gitlab_classroom:classroom-detail", args=[str(self.id)])


class Assignment(models.Model): #assigment database model
    title = models.CharField(max_length=255, unique=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    deadline = models.DateTimeField(help_text="The deadline for submitting this assignment.")
    repo_url = models.URLField()
    gitlab_id = models.IntegerField(default=0, blank=True)
    students = models.ManyToManyField(Student, related_name="assignment")
    is_group = models.BooleanField() 
    template_id = models.IntegerField()
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assignment_teachers"
        )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="assignment_classroom"
        )

    class Meta:
        ordering = ['-creation_date']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):#getting the url
        return reverse("gitlab_classroom:assignment-detail", args=[str(self.id)])


class Assessment(models.Model):
    assignment = models.ForeignKey(
        "Assignment",
        on_delete=models.CASCADE,
        related_name="assessments_assignment",
    )
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="assessments_students",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_assessments_teacher",
    )
    score = models.CharField(max_length=4, default="None")
    feedback = models.TextField(blank=True)
    assessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("assignment", "student", "teacher")


class GroupProject(models.Model):
    name = models.CharField(max_length=255, unique=True)  # chyba można zrobić unikatowe?
    description = models.TextField()
    students = models.ManyToManyField(
        Student,
        related_name="student_groups"
    )
    teacher = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="group_projects"
    )
    deadline = models.DateTimeField(help_text="The deadline of the project")

    class Meta:
        ordering = ["-name"]
