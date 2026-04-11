from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    university = models.ForeignKey('University', on_delete=models.CASCADE)
    academic_profile = models.ForeignKey('AcademicProfile', on_delete=models.SET_NULL, null=True)

class University(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

class AcademicProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    major = models.CharField(max_length=100)
    gpa = models.FloatField()

class ChatSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)

class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)