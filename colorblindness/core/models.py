from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Simulation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_image = models.ImageField(upload_to='originals/')
    transformed_image = models.ImageField(upload_to='transformed/')
    blindness_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.blindness_type} ({self.created_at.strftime('%Y-%m-%d')})"
    
class ColorDetection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='color_detector/')
    detected_color = models.CharField(max_length=50)
    rgb_value = models.CharField(max_length=50)
    hex_value = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.detected_color}"
    
class TestQuestion(models.Model):
    question_number = models.PositiveIntegerField()
    image = models.ImageField(upload_to="test_images/")
    correct_answer = models.CharField(max_length=10)

    def __str__(self):
        return f"Question {self.question_number}"


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_taken = models.DateTimeField(auto_now_add=True)
    total_questions = models.PositiveIntegerField()
    correct_count = models.PositiveIntegerField()
    percentage = models.FloatField()
    diagnosis = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.date_taken.strftime('%Y-%m-%d %H:%M')}"