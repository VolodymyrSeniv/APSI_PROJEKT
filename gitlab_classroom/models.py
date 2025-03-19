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
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name="classroom"
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
    template_id = models.IntegerField()
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment"
        )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="assignment"
        )

    class Meta:
        ordering = ['-creation_date']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):#getting the url
        return reverse("gitlab_classroom:assignment-detail", args=[str(self.id)])
