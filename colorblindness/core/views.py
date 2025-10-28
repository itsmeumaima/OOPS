from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from PIL import Image
import numpy as np
from .forms import CorrectorForm,ColorDetectorForm
from django.conf import settings
import os
from PIL import Image
from .models import ColorDetection,Simulation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import TestQuestion, TestResult
from django.utils import timezone

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "core/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data["password"]
            password2 = form.cleaned_data["confirm_password"]
            if password1 != password2:
                messages.error(request, "Passwords do not match.")
            else:
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=password1,
                )
                login(request, user)
                return redirect("dashboard")
        else:
            print("Form errors ❌:", form.errors)  # 🔍 Add this line
    else:
        form = SignUpForm()
    return render(request, "core/signup.html", {"form": form})

@login_required
def dashboard(request):
    simulations = Simulation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "core/dashboard.html", {"simulations": simulations})


@login_required
def simulator_view(request):
    transformed_image_url = None
    original_image_url = None

    if request.method == "POST" and "image" in request.FILES:
        image_file = request.FILES["image"]
        blindness_type = request.POST.get("type")

        # Ensure folders exist
        originals_dir = os.path.join(settings.MEDIA_ROOT, "originals")
        transformed_dir = os.path.join(settings.MEDIA_ROOT, "transformed")
        os.makedirs(originals_dir, exist_ok=True)
        os.makedirs(transformed_dir, exist_ok=True)

        # Save original image inside /media/originals/
        original_filename = image_file.name
        original_path = os.path.join(originals_dir, original_filename)
        with open(original_path, "wb+") as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        # Open image and apply transformation
        image = Image.open(original_path).convert("RGB")
        transformed = apply_color_blindness(image, blindness_type)

        # Save transformed image inside /media/transformed/
        transformed_filename = f"transformed_{original_filename}"
        transformed_path = os.path.join(transformed_dir, transformed_filename)
        transformed.save(transformed_path)

        # Build URLs
        original_image_url = settings.MEDIA_URL + f"originals/{original_filename}"
        transformed_image_url = settings.MEDIA_URL + f"transformed/{transformed_filename}"

        # Save to database
        Simulation.objects.create(
            user=request.user,
            original_image=f"originals/{original_filename}",
            transformed_image=f"transformed/{transformed_filename}",
            blindness_type=blindness_type,
        )

    return render(request, "core/simulator.html", {
        "transformed_image_url": transformed_image_url,
        "original_image_url": original_image_url,
    })


def apply_color_blindness(image, blindness_type):
    """Simulate color blindness using transformation matrices"""
    arr = np.array(image).astype(float)

    matrices = {
        "Protanopia": np.array([[0.567, 0.433, 0.0],
                                [0.558, 0.442, 0.0],
                                [0.0,   0.242, 0.758]]),
        "Deuteranopia": np.array([[0.625, 0.375, 0.0],
                                  [0.7,   0.3,   0.0],
                                  [0.0,   0.3,   0.7]]),
        "Tritanopia": np.array([[0.95,  0.05,  0.0],
                                [0.0,   0.433, 0.567],
                                [0.0,   0.475, 0.525]]),
    }

    matrix = matrices.get(blindness_type, matrices["Protanopia"])
    transformed = np.dot(arr, matrix.T)
    transformed = np.clip(transformed, 0, 255).astype(np.uint8)

    return Image.fromarray(transformed)


@login_required
def color_detector_view(request):
    detected_color = None
    rgb_value = None
    hex_value = None
    image_url = None

    # ✅ Handle AJAX click requests (detect color)
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        x = int(request.POST.get("x"))
        y = int(request.POST.get("y"))
        image_rel_path = request.POST.get("image_path")

        image_path = os.path.join(settings.MEDIA_ROOT, image_rel_path)
        image = Image.open(image_path)
        pixel = image.getpixel((x, y))

        rgb_value = f"({pixel[0]}, {pixel[1]}, {pixel[2]})"
        hex_value = '#%02x%02x%02x' % (pixel[0], pixel[1], pixel[2])
        detected_color = get_color_name(pixel)

        # ✅ Save result to DB
        ColorDetection.objects.create(
            user=request.user,
            image=image_rel_path,
            detected_color=detected_color,
            rgb_value=rgb_value,
            hex_value=hex_value
        )

        return JsonResponse({
            "detected_color": detected_color,
            "rgb_value": rgb_value,
            "hex_value": hex_value
        })

    # ✅ Handle image upload
    elif request.method == "POST":
        form = ColorDetectorForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            image_url = obj.image.url
    else:
        form = ColorDetectorForm()

    return render(request, "core/color_detector.html", {
        "form": form,
        "detected_color": detected_color,
        "rgb_value": rgb_value,
        "hex_value": hex_value,
        "image_url": image_url,
    })


def get_color_name(rgb):
    """Approximate name finder for basic colors."""
    color_map = {
        (255, 0, 0): "Red",
        (0, 255, 0): "Green",
        (0, 0, 255): "Blue",
        (255, 255, 0): "Yellow",
        (255, 165, 0): "Orange",
        (128, 0, 128): "Purple",
        (255, 192, 203): "Pink",
        (165, 42, 42): "Brown",
        (0, 0, 0): "Black",
        (255, 255, 255): "White",
        (128, 128, 128): "Gray",
    }
    closest_name = "Unknown"
    min_dist = float("inf")

    for rgb_key, name in color_map.items():
        dist = sum((rgb_key[i] - rgb[i]) ** 2 for i in range(3)) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest_name = name

    return closest_name
@login_required
def corrector_view(request):
    corrected_image_url = None
    original_image_url = None  # ✅ initialize this variable

    form = CorrectorForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        image_file = form.cleaned_data["image"]
        correction_type = form.cleaned_data["correction_type"]  # radio: e.g. 'type1','type2','type3'
        hue = form.cleaned_data["hue"]  # integer slider value (can be negative)

        # ensure media subfolders
        originals_dir = os.path.join(settings.MEDIA_ROOT, "originals")
        transformed_dir = os.path.join(settings.MEDIA_ROOT, "corrected")
        os.makedirs(originals_dir, exist_ok=True)
        os.makedirs(transformed_dir, exist_ok=True)

        # save original file under originals/
        original_filename = image_file.name
        original_path = os.path.join(originals_dir, original_filename)
        with open(original_path, "wb+") as dest:
            for chunk in image_file.chunks():
                dest.write(chunk)

        # process image (PIL loads in RGB)
        pil = Image.open(original_path).convert("RGB")
        corrected_pil = apply_corrector(pil, correction_type, int(hue))

        # save corrected
        corrected_filename = f"corrected_{original_filename}"
        corrected_path = os.path.join(transformed_dir, corrected_filename)
        corrected_pil.save(corrected_path)

        # create DB record (optional)
        # Simulation.objects.create(
        #     user=request.user,
        #     original_image=f"originals/{original_filename}",
        #     transformed_image=f"corrected/{corrected_filename}",
        #     blindness_type=f"corrector-{correction_type}"
        # )

        corrected_image_url = settings.MEDIA_URL + f"corrected/{corrected_filename}"
        original_image_url = settings.MEDIA_URL + f"originals/{original_filename}"

    return render(request, "core/corrector.html", {
        "form": form,
        "corrected_image_url": corrected_image_url,
        "original_image_url": original_image_url,
    })


# Helper image processing functions (vectorized numpy)
def apply_corrector(pil_image: Image.Image, correction_type: str, hue_adjustment: int) -> Image.Image:
    """
    Convert RGB -> LMS, apply channel scaling + hue adjustment similarly to your C# code,
    blend with original, then convert back LMS -> RGB.
    """
    arr = np.asarray(pil_image).astype(np.float32) / 255.0  # shape (H,W,3), RGB, values 0..1

    # RGB -> LMS matrix (from your C# ConvertBGRToLMS: l = 0.3811*r + 0.5783*g + 0.0402*b, etc.)
    M_rgb2lms = np.array([
        [0.3811, 0.5783, 0.0402],
        [0.1967, 0.7244, 0.0782],
        [0.0241, 0.1288, 0.8444]
    ], dtype=np.float32)

    # Inverse LMS -> RGB (from your C# ConvertLMSToBGR inverse coefficients: r = 4.4679*l -3.5873*m +0.1193*s, ...)
    M_lms2rgb = np.array([
        [ 4.4679, -3.5873,  0.1193],
        [-1.2186,  2.3809, -0.1624],
        [ 0.0497, -0.2439,  1.2045]
    ], dtype=np.float32)

    h, w, _ = arr.shape
    flat = arr.reshape(-1, 3)  # (n,3)

    # convert RGB -> LMS
    lms = flat.dot(M_rgb2lms.T)  # (n,3)

    # Keep original LMS for blending later
    original_lms = lms.copy()

    # Decide L and M scaling factors based on correction_type (maps from your radio button logic)
    if correction_type == "type1":
        l_factor = 1.05
        m_factor = 0.95
    elif correction_type == "type2":
        l_factor = 0.95
        m_factor = 1.05
    elif correction_type == "type3":
        l_factor = 0.95
        m_factor = 0.95
    else:
        l_factor = 1.0
        m_factor = 1.0

    # Apply channel scaling
    lms[:, 0] *= l_factor
    lms[:, 1] *= m_factor

    # Apply hue adjustment (same formula: value * (1 + hue/360.0))
    hue_factor = 1.0 + (hue_adjustment / 360.0)
    lms[:, 0] = lms[:, 0] * hue_factor
    lms[:, 1] = lms[:, 1] * hue_factor

    # clamp LMS channels between 0 and 1
    lms = np.clip(lms, 0.0, 1.0)

    # Blend with original LMS (AddWeighted original*0.7 + lms*0.3)
    blended_lms = (original_lms * 0.7) + (lms * 0.3)

    # Convert back LMS -> RGB
    corrected_flat = blended_lms.dot(M_lms2rgb.T)

    # clamp corrected RGB to [0,1]
    corrected_flat = np.clip(corrected_flat, 0.0, 1.0)

    corrected = (corrected_flat.reshape(h, w, 3) * 255.0).astype(np.uint8)
    corrected_pil = Image.fromarray(corrected, mode="RGB")
    return corrected_pil
@login_required
def color_test_view(request):
    questions = TestQuestion.objects.all().order_by("question_number")
    total_questions = questions.count()

    # initialize session data
    if "current_q" not in request.session:
        request.session["current_q"] = 1
        request.session["correct_count"] = 0

    current_q = request.session["current_q"]
    question = questions.filter(question_number=current_q).first()

    if request.method == "POST":
        user_answer = request.POST.get("answer", "").strip()
        correct_answer = question.correct_answer.strip()

        if user_answer == correct_answer:
            request.session["correct_count"] += 1

        # move to next question or finish
        if current_q < total_questions:
            request.session["current_q"] += 1
            return redirect("color_test")  # reload next question
        else:
            # test finished
            correct_count = request.session["correct_count"]
            percentage = (correct_count / total_questions) * 100

            if correct_count == total_questions:
                diagnosis = "No color blindness detected."
            elif correct_count < 12:
                diagnosis = "You may have color blindness."
            else:
                diagnosis = "No color blindness detected."

            # Save result
            TestResult.objects.create(
                user=request.user,
                total_questions=total_questions,
                correct_count=correct_count,
                percentage=percentage,
                diagnosis=diagnosis,
            )

            # clear session
            del request.session["current_q"]
            del request.session["correct_count"]

            return render(request, "core/test_result.html", {
                "score": correct_count,
                "total": total_questions,
                "percentage": percentage,
                "diagnosis": diagnosis,
            })

    # ✅ Calculate progress for progress bar
    progress = (current_q / total_questions) * 100 if total_questions > 0 else 0

    return render(request, "core/test.html", {
        "question": question,
        "current_q": current_q,
        "total": total_questions,
        "progress": progress,  #  Send to template
    })
