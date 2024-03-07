from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotFound, QueryDict, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Max
from django.core.files.storage import FileSystemStorage
import os
from django.contrib import auth
from django.conf import settings
import uuid
from django.core.mail import send_mail, EmailMultiAlternatives 
from django.template.loader import render_to_string
from django.conf import settings
import random
import string
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required, permission_required
from django.template.loader import render_to_string
import json
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
# Create your views here.

from .utils import encrypt_data, decrypt_data
import base64

#models
from case.models import *
from account.models import *

def home_view (request):
    return render(request, 'landing/home.html')

def error_view (request):
    return render(request, 'landing/error_404.html')

def login_view (request):
    return render(request, 'login/login.html')

def track_case_view (request):
    return render(request, 'landing/track_case.html')

def check_email_case(request):
    if request.method == 'POST':
        email = request.POST.get('email', None)  # Get the email from the POST data
        if email:
            # Check if there is any case associated with the given email
            if Case.objects.filter(email=email).exists():
                return JsonResponse({'success': True, 'message': 'There is an Email associated with at least one case.'})
            else:
                return JsonResponse({'success': False, 'message': 'There is no Email associated with any case.'})
        else:
            return JsonResponse({'success': False, 'message': 'No email provided.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

# Set expiration time for tokens (30 minutes)
TOKEN_EXPIRATION_TIMEDELTA = timedelta(minutes=30)

def verify_otp_email_track_case(request):
    if request.method == 'POST':
        otp_entered = ''
        for i in range(1, 7):  # Iterate through OTP fields from 1 to 6
            otp_entered += request.POST.get(f'otp_{i}', '')

        otp_saved = request.session.get('otp')
        otp_expiry_str = request.session.get('otp_expiry')
        user_email = request.session.get('user_email')  # Retrieving user email from session
        print(user_email)

        if otp_saved and otp_expiry_str and user_email:  # Check if user_email exists
            otp_expiry = timezone.datetime.fromisoformat(otp_expiry_str)
            if timezone.now() < otp_expiry and otp_entered == otp_saved:
                # Clear session data after successful OTP verification
                request.session.pop('otp')
                request.session.pop('otp_expiry')
                request.session.pop('user_email')
                print('OTP Verified Succesfully, Used Email:', user_email)

                # Generate a unique token for password reset using Django's default_token_generator
                token = generate_token(user_email)

                return JsonResponse({'success': True, 'message': 'OTP verified successfully.', 'user_email': user_email, 'token': token})
            elif timezone.now() >= otp_expiry:
                return JsonResponse({'success': False, 'message': 'OTP has expired.'})
        return JsonResponse({'success': False, 'message': 'Incorrect OTP.', 'user_email': user_email})

def generate_token(user_email):
    # Create a temporary user object with the email address
    temp_user = User(email=user_email)
    # Generate a unique token for password reset using Django's default_token_generator
    token = default_token_generator.make_token(temp_user)
    # Get current timestamp
    timestamp = timezone.now()
    return token

def track_case_info_view(request, user_email, token):
    try:
        # Create a temporary user object with the email address
        temp_user = User(email=user_email)
    except User.DoesNotExist:
        return redirect('error_view')

    # Check if the token is valid for the temporary user
    if not default_token_generator.check_token(temp_user, token):
        return redirect('error_view')

    # Fetch cases related to the user_email and prefetch related status history
    cases = Case.objects.filter(email=user_email).prefetch_related('status_history')

    # Token is valid, render the template
    return render(request, 'landing/track_case_info.html', {'user_email': user_email, 'token': token, 'cases': cases})

@login_required
def logout_view(request):
    logout(request)
    return redirect(reverse('login'))

@login_required
def admin_dashboard_view (request):
    return render(request, 'super-admin/dashboard.html')

@login_required
def admin_graph_view (request):
    return render(request, 'super-admin/graph_report.html')

@login_required
def barangay_dashboard_view (request):
    return render(request, 'barangay-admin/dashboard.html')

@login_required
def barangay_settings_view (request):
    return render(request, 'barangay-admin/settings.html', {'global': request.session})

@login_required
def barangay_case_view(request):
    cases = Case.objects.all()  # Retrieve all cases from the database
    
    print(request.session['security_status'])
    
    return render(request, 'barangay-admin/case/case.html', {
        'cases': cases,
        'global': request.session
    })


def send_otp_email(email, otp):
    subject = 'One-Time Password Verification'
    message = (
        f'--------------------------\n'
        f'One-Time Password Verification\n'
        f'--------------------------\n\n'
        f'Your One-Time Password (OTP) is: {otp}\n\n'
        f'Please use this OTP to verify your account.\n\n'
        f'This OTP will expire in 5 minutes.\n\n'
        f'--------------------------\n'
        f'This email was sent automatically. Please do not reply.'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def login_with_otp(request):
    if request.method == 'POST':
        email = request.POST.get('barangay-email')
        passkey = request.POST.get('barangay-passkey')
        # Check if the user exists
        user = CustomUser.objects.filter(email=email).first()
        if user:
            # Validate passkey
            user_authenticated = authenticate(request, username=email, password=passkey)
            if user_authenticated:
                otp = generate_otp()
                request.session['otp'] = otp
                request.session['user_email'] = email  # Store user email in session for later retrieval
                otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
                request.session['otp_expiry'] = otp_expiry.isoformat()  # Convert datetime to string
                send_otp_email(email, otp)
                return JsonResponse({'success': True, 'message': 'OTP has been sent to your email.'})
            else:
                print('Invalid passkey. Please try again.')
                return JsonResponse({'success': False, 'message': 'Invalid passkey. Please try again.'})
        else:
            print('Account not found.')
            return JsonResponse({'success': False, 'message': 'Account not found.'})
    return render(request, 'login/login.html')


def verify_otp(request):
    if request.method == 'POST':
        otp_entered = ''
        for i in range(1, 7):  # Iterate through OTP fields from 1 to 6
            otp_entered += request.POST.get(f'otp_{i}', '')

        otp_saved = None
        otp_expiry_str = None

        # Check all possible OTP fields
        for i in range(1, 4):  # Adjust the range based on your maximum OTP fields
            otp_saved = request.session.get('otp')
            otp_expiry_str = request.session.get('otp_expiry')
            user_email = request.session.get('user_email')
            print(user_email)
            if otp_saved and otp_expiry_str:
                otp_expiry = timezone.datetime.fromisoformat(otp_expiry_str)
                if timezone.now() < otp_expiry and otp_entered == otp_saved:
                    user = CustomUser.objects.filter(email=user_email).first()
                    if user:
                        login(request, user)  # Logging in the user
                        request.session.pop('otp')
                        request.session.pop('otp_expiry')
                        request.session.pop('user_email')

                        # Fetch the account type of the user
                        account_type = Account.objects.filter(user=user).first().type

                        # Print a success message
                        print("User logged in successfully")
                        print(account_type)

                        request.session['security_status'] = "encrypted"
                        print(request.session['security_status'])

                        # Return success along with account type
                        return JsonResponse({'success': True, 'message': 'Login successful.', 'account_type': account_type, 'otp_expiry': otp_expiry_str})
                    else:
                        return JsonResponse({'success': False, 'message': 'User not found.'})
                elif timezone.now() >= otp_expiry:
                    return JsonResponse({'success': False, 'message': 'Code is already expired.', 'otp_expiry': otp_expiry_str})
                else:
                    break
        # If OTP is incorrect
        return JsonResponse({'success': False, 'message': 'OTP Inputted is not Correct.', 'otp_expiry': otp_expiry_str})

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, encoder=DjangoJSONEncoder)

def resend_otp(request):
    if request.method == 'GET':
        user_email = request.session.get('user_email')  # Corrected key
        if user_email:
            try:
                user = CustomUser.objects.get(email=user_email)
                otp = generate_otp()  # Assuming you have a function to generate OTP
                request.session['otp'] = otp
                otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
                request.session['otp_expiry'] = otp_expiry.isoformat()
                send_otp_email(user_email, otp)  # Assuming you have a function to send OTP email
                return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
            except ObjectDoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found.'})
        else:
            return JsonResponse({'success': False, 'message': 'User email not found in session.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def email_confirm(request):
    if request.method == 'POST':
        email = request.POST.get('emailConfirm')
        print('Email Inputted:',email)

        otp = generate_otp()
        request.session['otp'] = otp
        request.session['user_email'] = email  # Store user email in session for later retrieval
        otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
        request.session['otp_expiry'] = otp_expiry.isoformat()  # Convert datetime to string
        send_otp_email(email, otp)
        return JsonResponse({'success': True, 'message': 'OTP has been sent to your email.'})


def verify_otp_email(request):
    if request.method == 'POST':
        otp_entered = ''
        for i in range(1, 7):  # Iterate through OTP fields from 1 to 6
            otp_entered += request.POST.get(f'otp_{i}', '')

        otp_saved = request.session.get('otp')
        otp_expiry_str = request.session.get('otp_expiry')
        user_email = request.session.get('user_email')  # Retrieving user email from session
        print(user_email)

        if otp_saved and otp_expiry_str and user_email:  # Check if user_email exists
            otp_expiry = timezone.datetime.fromisoformat(otp_expiry_str)
            if timezone.now() < otp_expiry and otp_entered == otp_saved:
                # Clear session data after successful OTP verification
                request.session.pop('otp')
                request.session.pop('otp_expiry')
                request.session.pop('user_email')
                return JsonResponse({'success': True, 'message': 'OTP verified successfully.', 'user_email': user_email})
            elif timezone.now() >= otp_expiry:
                return JsonResponse({'success': False, 'message': 'OTP has expired.'})
        return JsonResponse({'success': False, 'message': 'Incorrect OTP.', 'user_email': user_email})



def resend_otp_email(request):
    if request.method == 'GET':
        user_email = request.session.get('user_email')  # Corrected key
        otp = generate_otp()  # Assuming you have a function to generate OTP
        request.session['otp'] = otp
        otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
        request.session['otp_expiry'] = otp_expiry.isoformat()
        send_otp_email(user_email, otp)  # Assuming you have a function to send OTP email
        return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def report_violence_view (request):
    return render(request, 'landing/report_violence.html')

def impact_victim_view (request):
    return render(request, 'landing/case_type/impacted-victim.html')

def behalf_victim_view (request):
    return render(request, 'landing/case_type/behalf-victim.html')

def add_case(request):
    if request.method == 'POST':
        email = request.POST.get('email-confirmed')
        print('Entered Email:', email)

        # Create a new QueryDict object
        modified_post_data = QueryDict('', mutable=True)

        # Attributes to ignore for encryption
        ignore_key = [
            'type_of_case',
            'victim_count',
            'perpetrator_count',
            'incomplete-date',
            'service',
            'csrfmiddlewaretoken',
            'status_date',
            'date_added'
        ]

        for key, values in request.POST.lists():
            modified_values = []

            if key in ignore_key:
                for value in values:
                    modified_values.append(value)
            else:
                for value in values:
                    modified_values.append(encrypt_data(value).decode('utf-8'))
            modified_post_data.setlist(key, modified_values)

        request.POST = modified_post_data

        case_data = {
            'case_number': get_next_case_number(),
            'email':email,
            'date_latest_incident': request.POST.get('date-latest-incident'),
            'incomplete_date': request.POST.get('incomplete-date'),
            'place_of_incident': request.POST.get('place-incident'),
            'street': request.POST.get('incident-street'),
            'barangay': request.POST.get('incident-barangay'),
            'province': request.POST.get('incident-province'),
            'city': request.POST.get('incident-city'),
            'region': request.POST.get('incident-region'),
            'description_of_incident': request.POST.get('incident-desc'),
            'service_information': request.POST.get('service'),
            'type_of_case': request.POST.get('type_of_case'),  # Collecting type of case from the form
            'date_added': timezone.now(),
        }
        case_instance = Case.objects.create(**case_data)

        if 'evidence_file' in request.FILES:
            handle_evidence_files(request.FILES.getlist('evidence_file'), case_instance)

        # Get dynamic victim data
        victim_instances = []
        victim_form_prefix = 'victim-'  # Adjust this prefix according to your form field names
        victim_count = int(request.POST.get('victim_count'))  # Assuming you have a hidden input for victim count
        for i in range(victim_count):
            victim_data = get_victim_data(request.POST, prefix=victim_form_prefix, index=i)
            victim_instance = Victim.objects.create(case_victim=case_instance, **victim_data)
            victim_instances.append(victim_instance)

        # Perpetrator data handling
        perpetrator_count = int(request.POST.get('perpetrator_count'))  # Assuming you have a hidden input for perpetrator count
        for i in range(perpetrator_count):
            perpetrator_data = get_perpetrator_data(request.POST, index=i)
            perpetrator_instance = Perpetrator.objects.create(case_perpetrator=case_instance, **perpetrator_data)

        contact_person_data = get_contact_person_data(request.POST)
        contact_person_instance = Contact_Person.objects.create(case_contact=case_instance, **contact_person_data)

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_next_case_number():
    latest_case_number = Case.objects.aggregate(Max('case_number'))['case_number__max']
    return 1 if latest_case_number is None else latest_case_number + 1

def handle_evidence_files(files, case_instance):
    for file in files:
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        unique_filename = str(uuid.uuid4()) + os.path.splitext(file.name)[-1]
        filename = fs.save(unique_filename, file)
        evidence_instance = Evidence.objects.create(case=case_instance, file=filename)

def get_victim_data(post_data, prefix, index):
    victim_data = {
        'first_name': post_data.get(f'{prefix}firstname_{index}'),
        'middle_name': post_data.get(f'{prefix}middlename_{index}'),
        'last_name': post_data.get(f'{prefix}lastname_{index}'),
        'suffix': post_data.get(f'{prefix}Suffix_{index}'),
        'sex': post_data.get(f'{prefix}sex_{index}'),
        'date_of_birth': post_data.get(f'{prefix}date-of-birth_{index}'),
        'civil_status': post_data.get(f'{prefix}civilstatus_{index}'),
        'nationality': post_data.get(f'{prefix}nationality_{index}'),
        'contact_number': post_data.get(f'{prefix}contact-number_{index}'),
        'telephone_number': post_data.get(f'{prefix}tel-number_{index}'),
        'house_information': post_data.get(f'{prefix}house-info_{index}'),
        'street': post_data.get(f'{prefix}street_{index}'),
        'barangay': post_data.get(f'{prefix}barangay_{index}'),
        'province': post_data.get(f'{prefix}province_{index}'),
        'city': post_data.get(f'{prefix}city_{index}'),
        'region': post_data.get(f'{prefix}region_{index}'),
    }
    return victim_data

def get_perpetrator_data(post_data, index):
    perpetrator_data = {
        'first_name': post_data.get(f'perp-firstname_{index}'),
        'middle_name': post_data.get(f'perp-middlename_{index}'),
        'last_name': post_data.get(f'perp-lastname_{index}'),
        'suffix': post_data.get(f'perp-Suffix_{index}'),
        'alias': post_data.get(f'perp-alias_{index}'),
        'sex': post_data.get(f'perp-sex_{index}'),
        'date_of_birth': post_data.get(f'perp-date-of-birth_{index}'),
        'nationality': post_data.get(f'perp-nationality_{index}'),
        'identifying_marks': post_data.get(f'perp-identifying-marks_{index}'),
        'house_information': post_data.get(f'perp-address-info_{index}'),
        'street': post_data.get(f'perp-street_{index}'),
        'barangay': post_data.get(f'perp-barangay_{index}'),
        'province': post_data.get(f'perp-province_{index}'),
        'city': post_data.get(f'perp-city_{index}'),
        'region': post_data.get(f'perp-region_{index}'),
        'relationship_to_victim': post_data.get(f'perp-relationsip-victim_{index}'),
    }
    return perpetrator_data

def get_contact_person_data(post_data):
    contact_person_data = {
        'first_name': post_data.get('contact-firstname'),
        'middle_name': post_data.get('contact-midname'),
        'last_name': post_data.get('contact-lastname'),
        'suffix': post_data.get('contact-Suffix'),
        'relationship': post_data.get('relationship'),
        'street': post_data.get('contact-street'),
        'barangay': post_data.get('contact-barangay'),
        'city': post_data.get('contact-city'),
        'province': post_data.get('contact-province'),
        'contact_number': post_data.get('contact-number'),
        'telephone_number': post_data.get('contact-tel'),
        'region': post_data.get('contact-region'),
    }
    return contact_person_data


def add_new_case(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        type_of_case = request.POST.get('case_type')
        service_information = request.POST.get('service_type')
        status_case = request.POST.get('status_case')

        try:
            # Create and save the new case instance
            case = Case.objects.create(
                case_number=get_next_case_number(),
                email=email,
                type_of_case=type_of_case,
                service_information=service_information,
                status=status_case,  # Fixed field name
                date_added=timezone.now()  # Assign the current timestamp
            )
            # Return the case_id upon successful creation
            return JsonResponse({'success': True, 'case_id': case.id, 'type_of_case': type_of_case})
            #return redirect('barangay case') 
        except Exception as e:
            # Return error response if creation fails
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return HttpResponse("Method not allowed", status=405)

@login_required
def view_case_behalf(request, case_id):
    try:
        # Retrieve the case object from the database based on the case_id
        case = Case.objects.get(id=case_id)
        # Retrieve related objects such as contact persons, evidence, victims, perpetrators, and parents
        contact_persons = Contact_Person.objects.filter(case_contact=case)
        evidences = Evidence.objects.filter(case=case)
        victims = Victim.objects.filter(case_victim=case)
        perpetrators = Perpetrator.objects.filter(case_perpetrator=case)
        status_history = Status_History.objects.filter(case_status_history=case)

        # Retrieve only the latest status history entry
        latest_status_history = status_history.order_by('-status_date_added').first()

        print(request.session['security_status'])

        if request.session['security_status'] == "decrypted":
            case.street = decrypt_data(case.street)
            case.barangay = decrypt_data(case.barangay)
            case.date_latest_incident = decrypt_data(case.date_latest_incident)
            case.place_of_incident = decrypt_data(case.place_of_incident)
            case.province = decrypt_data(case.province)
            case.region = decrypt_data(case.region)
            case.description_of_incident = decrypt_data(case.description_of_incident)
            case.city = decrypt_data(case.city)

            # for victim in victims:
            #     victim.description
            for victim in victims:
                victim.first_name = decrypt_data(victim.first_name)
                victim.middle_name = decrypt_data(victim.middle_name)
                victim.last_name = decrypt_data(victim.last_name)
                victim.suffix = decrypt_data(victim.suffix)
                victim.date_of_birth = decrypt_data(victim.date_of_birth)
                victim.sex = decrypt_data(victim.sex)
                victim.civil_status = decrypt_data(victim.civil_status)
                victim.nationality = decrypt_data(victim.nationality)
                victim.contact_number = decrypt_data(victim.contact_number)
                victim.telephone_number = decrypt_data(victim.telephone_number)
                victim.house_information = decrypt_data(victim.house_information)
                victim.street = decrypt_data(victim.street)
                victim.barangay = decrypt_data(victim.barangay)
                victim.province = decrypt_data(victim.province)
                victim.city = decrypt_data(victim.city)
                victim.region = decrypt_data(victim.region)

            for perpetrator in perpetrators:
                perpetrator.relationship_to_victim = decrypt_data(perpetrator.relationship_to_victim)
                perpetrator.first_name = decrypt_data(perpetrator.first_name)
                perpetrator.middle_name = decrypt_data(perpetrator.middle_name)
                perpetrator.last_name = decrypt_data(perpetrator.last_name)
                perpetrator.suffix = decrypt_data(perpetrator.suffix)
                perpetrator.identifying_marks = decrypt_data(perpetrator.identifying_marks)
                perpetrator.alias = decrypt_data(perpetrator.alias)
                perpetrator.sex = decrypt_data(perpetrator.sex)
                #perpetrator.contact_number = decrypt_data(perpetrator.contact_number)
                #perpetrator.telephone_number = decrypt_data(perpetrator.telephone_number)
                print(perpetrator.contact_number)
                perpetrator.date_of_birth = decrypt_data(perpetrator.date_of_birth)
                perpetrator.nationality = decrypt_data(perpetrator.nationality)
                perpetrator.house_information = decrypt_data(perpetrator.house_information)
                perpetrator.street = decrypt_data(perpetrator.street)
                perpetrator.barangay = decrypt_data(perpetrator.barangay)
                perpetrator.province = decrypt_data(perpetrator.province)
                perpetrator.region = decrypt_data(perpetrator.region)
            
            print("contact")
            for contact_person in contact_persons:
                contact_person.first_name = decrypt_data(contact_person.first_name)
                contact_person.middle_name = decrypt_data(contact_person.middle_name)
                contact_person.last_name = decrypt_data(contact_person.last_name)
                contact_person.barangay = decrypt_data(contact_person.barangay)
                contact_person.city = decrypt_data(contact_person.city)
                contact_person.province = decrypt_data(contact_person.province)
                contact_person.telephone_number = decrypt_data(contact_person.telephone_number)

                # contact num
                # region
                # street
                # relationship
                # suffix

            # for contact_person in contact_persons:
            #     contact_person.first_name = decrypt_data(contact_person.first_name)
            #     contact_person.middle_name = decrypt_data(contact_person.middle_name)
            #     contact_person.last_name = decrypt_data(contact_person.last_name)
            #     contact_person.suffix = decrypt_data(contact_person.suffix)
            #     contact_person.relationship= decrypt_data(contact_person.relationship)
            #     contact_person.contact_number = decrypt_data(contact_person.contact_number)
            #     contact_person.telephone_number = decrypt_data(contact_person.telephone_number)
            #     contact_person.street = decrypt_data(contact_person.street)
            #     contact_person.city = decrypt_data(contact_person.city)
            #     contact_person.barangay = decrypt_data(contact_person.barangay)
            #     contact_person.province = decrypt_data(contact_person.province)
            #     contact_person.region = decrypt_data(contact_person.region)

        #print(decrypt_data(case.street))
        # if isinstance(encrypted_data_from_db, bytes):
        #     print("Decrypted: ", decrypt_data(encrypted_data_from_db))
        # else:
        #     print("Decrypted: ", decrypt_data())
        
        # for victim in victims:
        #     encryted_value = encrypt_data(victim.first_name)
        #     print("Encrypted: ", encryted_value)
        #     print("Decrypted: ", decrypt_data(encryted_value))

        # Render the view-case.html template with the case and related objects as context
        return render(request, 'barangay-admin/case/view-case-behalf.html', {
            'case': case,
            'contact_persons': contact_persons,
            'evidence': evidences,
            'victims': victims,
            'perpetrators': perpetrators,
            'status_histories': status_history,
            'latest_status_history': latest_status_history,
            'global': request.session,
        })
    except Case.DoesNotExist:
        # Handle case not found appropriately, for example, return a 404 page
        return HttpResponseNotFound("Case not found")

@login_required
def view_case_impact(request, case_id):
    try:
        # Retrieve the case object from the database based on the case_id
        case = Case.objects.get(id=case_id)
        # Retrieve related objects such as evidence, victims, perpetrators, and parents
        evidences = Evidence.objects.filter(case=case)
        victims = Victim.objects.filter(case_victim=case)
        perpetrators = Perpetrator.objects.filter(case_perpetrator=case)
        status_history = Status_History.objects.filter(case_status_history=case)
        witnesses = Witness.objects.filter(case_witness=case)

        # Retrieve only the latest status history entry
        latest_status_history = status_history.order_by('-status_date_added').first()

        print(request.session['security_status'])

        if request.session['security_status'] == "decrypted":
            case.street = decrypt_data(case.street)
            case.barangay = decrypt_data(case.barangay)
            case.date_latest_incident = decrypt_data(case.date_latest_incident)
            case.place_of_incident = decrypt_data(case.place_of_incident)
            case.province = decrypt_data(case.province)
            case.region = decrypt_data(case.region)
            case.description_of_incident = decrypt_data(case.description_of_incident)
            case.city = decrypt_data(case.city)

            # for victim in victims:
            #     victim.description
            for victim in victims:
                victim.first_name = decrypt_data(victim.first_name)
                victim.middle_name = decrypt_data(victim.middle_name)
                victim.last_name = decrypt_data(victim.last_name)
                victim.suffix = decrypt_data(victim.suffix)
                victim.date_of_birth = decrypt_data(victim.date_of_birth)
                victim.sex = decrypt_data(victim.sex)
                victim.civil_status = decrypt_data(victim.civil_status)
                victim.nationality = decrypt_data(victim.nationality)
                victim.contact_number = decrypt_data(victim.contact_number)
                victim.telephone_number = decrypt_data(victim.telephone_number)
                victim.house_information = decrypt_data(victim.house_information)
                victim.street = decrypt_data(victim.street)
                victim.barangay = decrypt_data(victim.barangay)
                victim.province = decrypt_data(victim.province)
                victim.city = decrypt_data(victim.city)
                victim.region = decrypt_data(victim.region)

            for perpetrator in perpetrators:
                perpetrator.relationship_to_victim = decrypt_data(perpetrator.relationship_to_victim)
                perpetrator.first_name = decrypt_data(perpetrator.first_name)
                perpetrator.middle_name = decrypt_data(perpetrator.middle_name)
                perpetrator.last_name = decrypt_data(perpetrator.last_name)
                perpetrator.suffix = decrypt_data(perpetrator.suffix)
                perpetrator.identifying_marks = decrypt_data(perpetrator.identifying_marks)
                perpetrator.alias = decrypt_data(perpetrator.alias)
                perpetrator.sex = decrypt_data(perpetrator.sex)
                #perpetrator.contact_number = decrypt_data(perpetrator.contact_number)
                #perpetrator.telephone_number = decrypt_data(perpetrator.telephone_number)
                print(perpetrator.contact_number)
                perpetrator.date_of_birth = decrypt_data(perpetrator.date_of_birth)
                perpetrator.nationality = decrypt_data(perpetrator.nationality)
                perpetrator.house_information = decrypt_data(perpetrator.house_information)
                perpetrator.street = decrypt_data(perpetrator.street)
                perpetrator.barangay = decrypt_data(perpetrator.barangay)
                perpetrator.province = decrypt_data(perpetrator.province)
                perpetrator.region = decrypt_data(perpetrator.region)

        # Render the view-case.html template with the case and related objects as context
        return render(request, 'barangay-admin/case/view-case-impacted.html', {
            'case': case,
            'evidence': evidences,
            'victims': victims,
            'perpetrators': perpetrators,
            'status_histories': status_history,
            'witnesses': witnesses,
            'latest_status_history': latest_status_history,
            'global': request.session,
        })
    except Case.DoesNotExist:
        # Handle case not found appropriately, for example, return a 404 page
        return HttpResponseNotFound("Case not found")


@require_POST
def save_victim_data(request, victim_id):
    try:
        victim = get_object_or_404(Victim, id=victim_id)

        # Update victim data
        victim.first_name = request.POST.get('victim_first_name_' + str(victim_id))
        victim.middle_name = request.POST.get('victim_middle_name_' + str(victim_id))
        victim.last_name = request.POST.get('victim_last_name_' + str(victim_id))
        victim.suffix = request.POST.get('victim_suffix_name_' + str(victim_id))
        victim.sex = request.POST.get('victim_sex_' + str(victim_id))
        victim.type_of_disability = request.POST.get('victim_type_of_disability_' + str(victim_id))
        victim.date_of_birth = request.POST.get('victim_date_of_birth_' + str(victim_id))
        victim.civil_status = request.POST.get('victim_civil_status_' + str(victim_id))
        victim.contact_number = request.POST.get('victim_contact_number_' + str(victim_id))
        victim.telephone_number = request.POST.get('victim_telephone_number_' + str(victim_id))
        victim.educational_attainment = request.POST.get('victim_educational_attainment_' + str(victim_id))
        victim.occupation = request.POST.get('victim_occupation_' + str(victim_id))
        victim.nationality = request.POST.get('victim_nationality_' + str(victim_id))
        victim.religion = request.POST.get('victim_religion_' + str(victim_id))
        victim.house_information = request.POST.get('victim_house_information_' + str(victim_id))
        victim.street = request.POST.get('victim_street_' + str(victim_id))
        victim.barangay = request.POST.get('victim_barangay_' + str(victim_id))
        victim.province = request.POST.get('victim_province_' + str(victim_id))
        victim.city = request.POST.get('victim_city_' + str(victim_id))
        victim.region = request.POST.get('victim_region_' + str(victim_id))

        # Save victim data
        victim.save()

        return JsonResponse({'success': True, 'message': 'Victim data saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def add_new_victim(request):
    try:
        case_id = request.POST.get('case_id')
        
        case_instance = get_object_or_404(Case, id=case_id)
        # Extract form data
        first_name = encrypt_data(request.POST.get('victim_first_name')).decode('utf-8')
        middle_name = encrypt_data(request.POST.get('victim_middle_name')).decode('utf-8')
        last_name = encrypt_data(request.POST.get('victim_last_name')).decode('utf-8')
        suffix = encrypt_data(request.POST.get('victim_suffix_name')).decode('utf-8')
        date_of_birth = encrypt_data(request.POST.get('victim_date_of_birth')).decode('utf-8')
        sex = encrypt_data(request.POST.get('victim_sex')).decode('utf-8')
        civil_status = encrypt_data(request.POST.get('victim_civil_status')).decode('utf-8')
        educational_attainment = encrypt_data(request.POST.get('victim_educational_attainment')).decode('utf-8')
        occupation = encrypt_data(request.POST.get('victim_occupation')).decode('utf-8')
        type_of_disability = encrypt_data(request.POST.get('victim_type_of_disability')).decode('utf-8')
        nationality = encrypt_data(request.POST.get('victim_nationality')).decode('utf-8')
        religion = encrypt_data(request.POST.get('victim_religion')).decode('utf-8')
        contact_number = encrypt_data(request.POST.get('victim_contact_number')).decode('utf-8')
        telephone_number = encrypt_data(request.POST.get('victim_telephone_number')).decode('utf-8')
        house_information = encrypt_data(request.POST.get('victim_house_information')).decode('utf-8')
        street = encrypt_data(request.POST.get('victim_street')).decode('utf-8')
        barangay = encrypt_data(request.POST.get('victim_barangay')).decode('utf-8')
        province = encrypt_data(request.POST.get('victim_province')).decode('utf-8')
        city = encrypt_data(request.POST.get('victim_city')).decode('utf-8')
        region = encrypt_data(request.POST.get('victim_region')).decode('utf-8')

        print(case_id)
        print(first_name)
        print(last_name)
        # Create and save the new victim instance
        victim = Victim.objects.create(
            case_victim=case_instance,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            date_of_birth=date_of_birth,
            sex=sex,
            civil_status=civil_status,
            educational_attainment=educational_attainment,
            occupation=occupation,
            type_of_disability=type_of_disability,
            nationality=nationality,
            religion=religion,
            contact_number=contact_number,
            telephone_number=telephone_number,
            house_information=house_information,
            street=street,
            barangay=barangay,
            province=province,
            city=city,
            region=region
        )

        # Return success response
        return JsonResponse({'success': True, 'message': 'Victim added successfully'})
    except Exception as e:
        # Return error response
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def add_new_perpetrator(request):
    try:
        case_id = request.POST.get('case_id')
        
        case_instance = get_object_or_404(Case, id=case_id)
        # Extract form data
        first_name = encrypt_data(request.POST.get('perpetrator_first_name')).decode('utf-8')
        middle_name = encrypt_data(request.POST.get('perpetrator_middle_name')).decode('utf-8')
        last_name = encrypt_data(request.POST.get('perpetrator_last_name')).decode('utf-8')
        suffix = encrypt_data(request.POST.get('perpetrator_suffix_name')).decode('utf-8')
        perpetrator_identifying_marks = encrypt_data(request.POST.get('perpetrator_identifying_marks')).decode('utf-8')
        perpetrator_alias = encrypt_data(request.POST.get('perpetrator_alias')).decode('utf-8')
        perp_relationship_victim = encrypt_data(request.POST.get('perp-relationship-victim')).decode('utf-8')
        date_of_birth = encrypt_data(request.POST.get('perpetrator_date_of_birth')).decode('utf-8')
        sex = encrypt_data(request.POST.get('perpetrator_sex')).decode('utf-8')
        civil_status = encrypt_data(request.POST.get('perpetrator_civil_status')).decode('utf-8')
        educational_attainment = encrypt_data(request.POST.get('perpetrator_educational_attainment')).decode('utf-8')
        occupation = encrypt_data(request.POST.get('perpetrator_occupation')).decode('utf-8')
        type_of_disability = encrypt_data(request.POST.get('perpetrator_type_of_disability')).decode('utf-8')
        nationality = encrypt_data(request.POST.get('perpetrator_nationality')).decode('utf-8')
        religion = encrypt_data(request.POST.get('perpetrator_religion')).decode('utf-8')
        contact_number = encrypt_data(request.POST.get('perpetrator_contact_number')).decode('utf-8')
        telephone_number = encrypt_data(request.POST.get('perpetrator_telephone_number')).decode('utf-8')
        house_information = encrypt_data(request.POST.get('perpetrator_house_information')).decode('utf-8')
        street = encrypt_data(request.POST.get('perpetrator_street')).decode('utf-8')
        barangay = encrypt_data(request.POST.get('perpetrator_barangay')).decode('utf-8')
        province = encrypt_data(request.POST.get('perpetrator_province')).decode('utf-8')
        city = encrypt_data(request.POST.get('perpetrator_city')).decode('utf-8')
        region = encrypt_data(request.POST.get('perpetrator_region')).decode('utf-8')

        print(case_id)
        print(first_name)
        print(last_name)
        # Create and save the new perpetrator instance
        perpetrator = Perpetrator.objects.create(
            case_perpetrator=case_instance,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            identifying_marks=perpetrator_identifying_marks,
            alias=perpetrator_alias,
            relationship_to_victim=perp_relationship_victim,
            date_of_birth=date_of_birth,
            sex=sex,
            civil_status=civil_status,
            educational_attainment=educational_attainment,
            occupation=occupation,
            type_of_disability=type_of_disability,
            nationality=nationality,
            religion=religion,
            contact_number=contact_number,
            telephone_number=telephone_number,
            house_information=house_information,
            street=street,
            barangay=barangay,
            province=province,
            city=city,
            region=region
        )

        # Return success response
        return JsonResponse({'success': True, 'message': 'Perpetrator added successfully'})
    except Exception as e:
        # Return error response
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def save_perpetrator_data(request, perpetrator_id):
    try:
        perpetrator = get_object_or_404(Perpetrator, id=perpetrator_id)

        # Update perpetrator data
        perpetrator.first_name = request.POST.get('perpetrator_first_name_' + str(perpetrator_id))
        perpetrator.middle_name = request.POST.get('perpetrator_middle_name_' + str(perpetrator_id))
        perpetrator.last_name = request.POST.get('perpetrator_last_name_' + str(perpetrator_id))
        perpetrator.suffix = request.POST.get('perpetrator_suffix_name_' + str(perpetrator_id))
        perpetrator.identifying_marks = request.POST.get('perpetrator_identifying_marks_' + str(perpetrator_id))
        perpetrator.alias = request.POST.get('perpetrator_alias_' + str(perpetrator_id))
        perpetrator.relationship_to_victim = request.POST.get('perp-relationship-victim_' + str(perpetrator_id))
        perpetrator.sex = request.POST.get('perpetrator_sex_' + str(perpetrator_id))
        perpetrator.type_of_disability = request.POST.get('perpetrator_type_of_disability_' + str(perpetrator_id))
        perpetrator.date_of_birth = request.POST.get('perpetrator_date_of_birth_' + str(perpetrator_id))
        perpetrator.civil_status = request.POST.get('perpetrator_civil_status_' + str(perpetrator_id))
        perpetrator.contact_number = request.POST.get('perpetrator_contact_number_' + str(perpetrator_id))
        perpetrator.telephone_number = request.POST.get('perpetrator_telephone_number_' + str(perpetrator_id))
        perpetrator.educational_attainment = request.POST.get('perpetrator_educational_attainment_' + str(perpetrator_id))
        perpetrator.occupation = request.POST.get('perpetrator_occupation_' + str(perpetrator_id))
        perpetrator.nationality = request.POST.get('perpetrator_nationality_' + str(perpetrator_id))
        perpetrator.religion = request.POST.get('perpetrator_religion_' + str(perpetrator_id))
        perpetrator.house_information = request.POST.get('perpetrator_house_information_' + str(perpetrator_id))
        perpetrator.street = request.POST.get('perpetrator_street_' + str(perpetrator_id))
        perpetrator.barangay = request.POST.get('perpetrator_barangay_' + str(perpetrator_id))
        perpetrator.province = request.POST.get('perpetrator_province_' + str(perpetrator_id))
        perpetrator.city = request.POST.get('perpetrator_city_' + str(perpetrator_id))
        perpetrator.region = request.POST.get('perpetrator_region_' + str(perpetrator_id))

        # Save perpetrator data
        perpetrator.save()

        return JsonResponse({'success': True, 'message': 'Perpetrator data saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def delete_perpetrator(request):
    perpetrator_id = request.POST.get('perpetrator_id')
    perpetrator = get_object_or_404(Perpetrator, id=perpetrator_id)
    perpetrator.delete()
    return JsonResponse({'success': True, 'message': 'Perpetrator and related Parents deleted successfully'})

@require_POST
def delete_case(request):
    case_id = request.POST.get('case_id')
    print('Case ID:', case_id)
    case = get_object_or_404(Case, id=case_id)
    case.delete()
    return JsonResponse({'success': True, 'message': 'Case Deleted successfully'})

def add_new_contact_person(request):
    try:
        case_id = request.POST.get('case_id')
        case_instance = get_object_or_404(Case, id=case_id)

        # Update contact_person data
        first_name = request.POST.get('contact_person_first_name')
        middle_name = request.POST.get('contact_person_middle_name')
        last_name = request.POST.get('contact_person_last_name')
        suffix = request.POST.get('contact_person_suffix_name')
        relationship = request.POST.get('contact_person-relationship')
        contact_number = request.POST.get('contact_person_contact-number')
        telephone_number = request.POST.get('contact_person_contact-tel')
        street = request.POST.get('contact_person_street')
        barangay = request.POST.get('contact_person_barangay')
        province = request.POST.get('contact_person_province')
        city = request.POST.get('contact_person_city')
        region = request.POST.get('contact_person_region')

        # Create and save the new victim instance
        contact_person = Contact_Person.objects.create(
            case_contact=case_instance,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            relationship=relationship,
            contact_number=contact_number,
            telephone_number=telephone_number,
            street=street,
            barangay=barangay,
            province=province,
            city=city,
            region=region
        )


        return JsonResponse({'success': True, 'message': 'Contact Person added successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def save_contact_person_data(request, contact_person_id):
    try:
        contact_person = get_object_or_404(Contact_Person, id=contact_person_id)

        # Update contact_person data
        contact_person.first_name = encrypt_data(request.POST.get('contact_person_first_name_' + str(contact_person_id))).decode('utf-8')
        contact_person.middle_name = encrypt_data(request.POST.get('contact_person_middle_name_' + str(contact_person_id))).decode('utf-8')
        contact_person.last_name = encrypt_data(request.POST.get('contact_person_last_name_' + str(contact_person_id))).decode('utf-8')
        # contact_person.suffix = request.POST.get('contact_person_suffix_name_' + str(contact_person_id))
        # contact_person.relationship = request.POST.get('contact_person-relationship_' + str(contact_person_id))
        # contact_person.contact_number = request.POST.get('contact_person_contact-number_' + str(contact_person_id))
        contact_person.telephone_number = encrypt_data(request.POST.get('contact_person_contact-tel_' + str(contact_person_id))).decode('utf-8')
        # contact_person.street = request.POST.get('contact_person_street_' + str(contact_person_id))
        contact_person.barangay = encrypt_data(request.POST.get('contact_person_barangay_' + str(contact_person_id))).decode('utf-8')
        contact_person.province = encrypt_data(request.POST.get('contact_person_province_' + str(contact_person_id))).decode('utf-8')
        contact_person.city = encrypt_data(request.POST.get('contact_person_city_' + str(contact_person_id))).decode('utf-8')
        # contact_person.region = request.POST.get('contact_person_region_' + str(contact_person_id))

        # Save contact_person data
        contact_person.save()

        return JsonResponse({'success': True, 'message': 'Contact Person data saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})



#parent victim data crud ----------------------------------------------------------------

@login_required
def add_parent_view(request, case_id, victim_id):
    # Get the Case and Victim objects
    case = Case.objects.get(id=case_id)
    victim = Victim.objects.get(id=victim_id)

    # Query Parent objects related to the Victim
    parents = Parent.objects.filter(victim_parent=victim)
    
    if request.session['security_status'] == "decrypted":
        for parent in parents:
            parent.first_name = decrypt_data(parent.first_name)
            parent.middle_name = decrypt_data(parent.middle_name)
            parent.last_name = decrypt_data(parent.last_name)
            parent.suffix = decrypt_data(parent.suffix)
            parent.date_of_birth = decrypt_data(parent.date_of_birth)
            parent.civil_status = decrypt_data(parent.civil_status)
            parent.educational_attainment = decrypt_data(parent.educational_attainment)
            parent.occupation = decrypt_data(parent.occupation)
            parent.type_of_disability = decrypt_data(parent.type_of_disability)
            parent.nationality = decrypt_data(parent.nationality)
            parent.religion = decrypt_data(parent.religion)
            parent.contact_number = decrypt_data(parent.contact_number)
            parent.telephone_number = decrypt_data(parent.telephone_number)
            parent.house_information = decrypt_data(parent.house_information)
            parent.street = decrypt_data(parent.street)
            parent.barangay = decrypt_data(parent.barangay)
            parent.province = decrypt_data(parent.province)
            parent.city = decrypt_data(parent.city)
            parent.region = decrypt_data(parent.region)

    return render(request, 'barangay-admin/case/add-parent.html', {
        'victim': victim,
        'case': case,
        'parents': parents,
    })

@require_POST
def save_parent_data(request, parent_id):
    try:
        parent = get_object_or_404(Parent, id=parent_id)

        # Update parent data
        parent.first_name = request.POST.get('parent_first_name_' + str(parent_id))
        parent.middle_name = request.POST.get('parent_middle_name_' + str(parent_id))
        parent.last_name = request.POST.get('parent_last_name_' + str(parent_id))
        parent.suffix = request.POST.get('parent_suffix_name_' + str(parent_id))
        parent.sex = request.POST.get('parent_sex_' + str(parent_id))
        parent.type_of_disability = request.POST.get('parent_type_of_disability_' + str(parent_id))
        parent.date_of_birth = request.POST.get('parent_date_of_birth_' + str(parent_id))
        parent.civil_status = request.POST.get('parent_civil_status_' + str(parent_id))
        parent.contact_number = request.POST.get('parent_contact_number_' + str(parent_id))
        parent.telephone_number = request.POST.get('parent_telephone_number_' + str(parent_id))
        parent.educational_attainment = request.POST.get('parent_educational_attainment_' + str(parent_id))
        parent.occupation = request.POST.get('parent_occupation_' + str(parent_id))
        parent.nationality = request.POST.get('parent_nationality_' + str(parent_id))
        parent.religion = request.POST.get('parent_religion_' + str(parent_id))
        parent.house_information = request.POST.get('parent_house_information_' + str(parent_id))
        parent.street = request.POST.get('parent_street_' + str(parent_id))
        parent.barangay = request.POST.get('parent_barangay_' + str(parent_id))
        parent.province = request.POST.get('parent_province_' + str(parent_id))
        parent.city = request.POST.get('parent_city_' + str(parent_id))
        parent.region = request.POST.get('parent_region_' + str(parent_id))

        # Save parent data
        parent.save()

        return JsonResponse({'success': True, 'message': 'Parent data saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def add_new_parent_form(request):
    try:
        victim_id = request.POST.get('victim_id')

        # Extract form data
        first_name = encrypt_data(request.POST.get('parent_first_name')).decode('utf-8')
        middle_name = encrypt_data(request.POST.get('parent_middle_name')).decode('utf-8')
        last_name = encrypt_data(request.POST.get('parent_last_name')).decode('utf-8')
        suffix = encrypt_data(request.POST.get('parent_suffix_name')).decode('utf-8')
        date_of_birth = encrypt_data(request.POST.get('parent_date_of_birth')).decode('utf-8')
        sex = encrypt_data(request.POST.get('parent_sex')).decode('utf-8')
        civil_status = encrypt_data(request.POST.get('parent_civil_status')).decode('utf-8')
        educational_attainment = encrypt_data(request.POST.get('parent_educational_attainment')).decode('utf-8')
        occupation = encrypt_data(request.POST.get('parent_occupation')).decode('utf-8')
        type_of_disability = encrypt_data(request.POST.get('parent_type_of_disability')).decode('utf-8')
        nationality = encrypt_data(request.POST.get('parent_nationality')).decode('utf-8')
        religion = encrypt_data(request.POST.get('parent_religion')).decode('utf-8')
        contact_number = encrypt_data(request.POST.get('parent_contact_number')).decode('utf-8')
        telephone_number = encrypt_data(request.POST.get('parent_telephone_number')).decode('utf-8')
        house_information = encrypt_data(request.POST.get('parent_house_information')).decode('utf-8')
        street = encrypt_data(request.POST.get('parent_street')).decode('utf-8')
        barangay = encrypt_data(request.POST.get('parent_barangay')).decode('utf-8')
        province = encrypt_data(request.POST.get('parent_province')).decode('utf-8')
        city = encrypt_data(request.POST.get('parent_city')).decode('utf-8')
        region = encrypt_data(request.POST.get('parent_region')).decode('utf-8')

        # Create and save the new parent instance
        parent = Parent.objects.create(
            victim_parent_id=victim_id,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            date_of_birth=date_of_birth,
            sex=sex,
            civil_status=civil_status,
            educational_attainment=educational_attainment,
            occupation=occupation,
            type_of_disability=type_of_disability,
            nationality=nationality,
            religion=religion,
            contact_number=contact_number,
            telephone_number=telephone_number,
            house_information=house_information,
            street=street,
            barangay=barangay,
            province=province,
            city=city,
            region=region
        )

        # Return success response
        return JsonResponse({'success': True, 'message': 'Parent added successfully'})
    except Exception as e:
        # Return error response
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def delete_parent(request):
    try:
        parent_id = request.POST.get('parent_id')
        parent = Parent.objects.get(id=parent_id)
        parent.delete()
        return JsonResponse({'success': True, 'message': 'Parent deleted successfully'})
    except Parent.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Parent does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


#parent victim data crud ----------------------------------------------------------------

#parent perp data crud ----------------------------------------------------------------
@login_required
def add_parent_perp_view(request, case_id, perp_id):
    # Get the Case and Victim objects
    case = Case.objects.get(id=case_id)
    perpetrator = Perpetrator.objects.get(id=perp_id)

    # Query Parent objects related to the Victim
    parents = Parent_Perpetrator.objects.filter(perpetrator_parent=perpetrator)
    
    print("test")
    
   
    if request.session['security_status'] == "decrypted":
        for parent in parents:
            parent.first_name = decrypt_data(parent.first_name)
            parent.middle_name = decrypt_data(parent.middle_name)
            parent.last_name = decrypt_data(parent.last_name)
            parent.suffix = decrypt_data(parent.suffix)
            parent.date_of_birth = decrypt_data(parent.date_of_birth)
            parent.civil_status = decrypt_data(parent.civil_status)
            parent.educational_attainment = decrypt_data(parent.educational_attainment)
            parent.occupation = decrypt_data(parent.occupation)
            parent.type_of_disability = decrypt_data(parent.type_of_disability)
            parent.nationality = decrypt_data(parent.nationality)
            parent.religion = decrypt_data(parent.religion)
            parent.contact_number = decrypt_data(parent.contact_number)
            parent.telephone_number = decrypt_data(parent.telephone_number)
            parent.house_information = decrypt_data(parent.house_information)
            parent.street = decrypt_data(parent.street)
            parent.barangay = decrypt_data(parent.barangay)
            parent.province = decrypt_data(parent.province)
            parent.city = decrypt_data(parent.city)
            parent.region = decrypt_data(parent.region)

    return render(request, 'barangay-admin/case/add-parent-perp.html', {
        'perpetrator': perpetrator,
        'case': case,
        'parents': parents,
    })

@require_POST
def add_new_parent_perp_form(request):
    try:
        perp_id = request.POST.get('perp_id')
        perpetrator = Perpetrator.objects.get(id=perp_id)

        # Extract form data
        first_name = encrypt_data(request.POST.get('parent_first_name')).decode('utf-8')
        middle_name = encrypt_data(request.POST.get('parent_middle_name')).decode('utf-8')
        last_name = encrypt_data(request.POST.get('parent_last_name')).decode('utf-8')
        suffix = encrypt_data(request.POST.get('parent_suffix_name')).decode('utf-8')
        date_of_birth = encrypt_data(request.POST.get('parent_date_of_birth')).decode('utf-8')
        sex = encrypt_data(request.POST.get('parent_sex')).decode('utf-8')
        civil_status = encrypt_data(request.POST.get('parent_civil_status')).decode('utf-8')
        educational_attainment = encrypt_data(request.POST.get('parent_educational_attainment')).decode('utf-8')
        occupation = encrypt_data(request.POST.get('parent_occupation')).decode('utf-8')
        type_of_disability = encrypt_data(request.POST.get('parent_type_of_disability')).decode('utf-8')
        nationality = encrypt_data(request.POST.get('parent_nationality')).decode('utf-8')
        religion = encrypt_data(request.POST.get('parent_religion')).decode('utf-8')
        contact_number = encrypt_data(request.POST.get('parent_contact_number')).decode('utf-8')
        telephone_number = encrypt_data(request.POST.get('parent_telephone_number')).decode('utf-8')
        house_information = encrypt_data(request.POST.get('parent_house_information')).decode('utf-8')
        street = encrypt_data(request.POST.get('parent_street')).decode('utf-8')
        barangay = encrypt_data(request.POST.get('parent_barangay')).decode('utf-8')
        province = encrypt_data(request.POST.get('parent_province')).decode('utf-8')
        city = encrypt_data(request.POST.get('parent_city')).decode('utf-8')
        region = encrypt_data(request.POST.get('parent_region')).decode('utf-8')
        # Create and save the new parent instance
        parent = Parent_Perpetrator.objects.create(
            perpetrator_parent=perpetrator,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            date_of_birth=date_of_birth,
            sex=sex,
            civil_status=civil_status,
            educational_attainment=educational_attainment,
            occupation=occupation,
            type_of_disability=type_of_disability,
            nationality=nationality,
            religion=religion,
            contact_number=contact_number,
            telephone_number=telephone_number,
            house_information=house_information,
            street=street,
            barangay=barangay,
            province=province,
            city=city,
            region=region
        )

        # Return success response
        return JsonResponse({'success': True, 'message': 'Parent added successfully'})
    except Exception as e:
        # Return error response
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def save_parent_perp_data(request, parent_id):
    try:
        parent = get_object_or_404(Parent_Perpetrator, id=parent_id)

        # Update parent data
        parent.first_name = request.POST.get('parent_first_name_' + str(parent_id))
        parent.middle_name = request.POST.get('parent_middle_name_' + str(parent_id))
        parent.last_name = request.POST.get('parent_last_name_' + str(parent_id))
        parent.suffix = request.POST.get('parent_suffix_name_' + str(parent_id))
        parent.sex = request.POST.get('parent_sex_' + str(parent_id))
        parent.type_of_disability = request.POST.get('parent_type_of_disability_' + str(parent_id))
        parent.date_of_birth = request.POST.get('parent_date_of_birth_' + str(parent_id))
        parent.civil_status = request.POST.get('parent_civil_status_' + str(parent_id))
        parent.contact_number = request.POST.get('parent_contact_number_' + str(parent_id))
        parent.telephone_number = request.POST.get('parent_telephone_number_' + str(parent_id))
        parent.educational_attainment = request.POST.get('parent_educational_attainment_' + str(parent_id))
        parent.occupation = request.POST.get('parent_occupation_' + str(parent_id))
        parent.nationality = request.POST.get('parent_nationality_' + str(parent_id))
        parent.religion = request.POST.get('parent_religion_' + str(parent_id))
        parent.house_information = request.POST.get('parent_house_information_' + str(parent_id))
        parent.street = request.POST.get('parent_street_' + str(parent_id))
        parent.barangay = request.POST.get('parent_barangay_' + str(parent_id))
        parent.province = request.POST.get('parent_province_' + str(parent_id))
        parent.city = request.POST.get('parent_city_' + str(parent_id))
        parent.region = request.POST.get('parent_region_' + str(parent_id))

        # Save parent data
        parent.save()

        return JsonResponse({'success': True, 'message': 'Parent data saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def delete_parent_perp(request):
    try:
        parent_id = request.POST.get('parent_id')
        parent = Parent_Perpetrator.objects.get(id=parent_id)
        parent.delete()
        return JsonResponse({'success': True, 'message': 'Parent deleted successfully'})
    except Parent_Perpetrator.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Parent does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

#parent perp data crud ----------------------------------------------------------------


@require_POST
def delete_victim(request):
    if request.method == 'POST':
        victim_id = request.POST.get('victim_id')
        print(victim_id)
        if victim_id:
            try:
                victim = Victim.objects.get(id=victim_id)
                # Delete related Parent instances
                Parent.objects.filter(victim_parent=victim).delete()
                # Delete the victim instance
                victim.delete()
                return JsonResponse({'success': True, 'message': 'Victim and related Parents deleted successfully'})
            except Victim.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Victim does not exist'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid victim ID'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

def check_parent_count(request):
    # Count the number of parents
    parent_count = Parent.objects.count()
    print (parent_count)

    # Return a success response if the limit is not exceeded
    return JsonResponse({'success': parent_count})

@require_POST
def delete_parent(request):
    try:
        parent_id = request.POST.get('parent_id')
        parent = Parent.objects.get(id=parent_id)
        parent.delete()
        return JsonResponse({'success': True, 'message': 'Parent deleted successfully'})
    except Parent.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Parent does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def process_incident_form(request):
    if request.method == 'POST':
        # Process removal of evidence
        evidence_to_delete = request.POST.getlist('evidenceToDelete')
        for evidence_id in evidence_to_delete:
            Evidence.objects.filter(id=evidence_id).delete()

        # Process upload of new evidence
        if 'evidence_file' in request.FILES:
            case_id = request.POST.get('case_id')
            case_instance = Case.objects.get(id=case_id)
            handle_evidence_files(request.FILES.getlist('evidence_file'), case_instance)

        # Process addition of new witnesses
        if 'witness_name' in request.POST:
            case_id = request.POST.get('case_id')
            case_instance = Case.objects.get(id=case_id)

            # Get data for all new witnesses
            witness_data = zip(
                request.POST.getlist('witness_name'),
                request.POST.getlist('witness_address'),
                request.POST.getlist('witness_number'),
                request.POST.getlist('witness_email')
            )

            # Create a new Witness object for each set of witness data
            for name, address, number, email in witness_data:
                Witness.objects.create(
                    case_witness=case_instance,
                    name=name,
                    address=address,
                    contact_number=number,
                    email=email
                )
        # Process removal of witnesses
        witnesses_to_delete = request.POST.getlist('witnesstoDelete')
        for witness_id in witnesses_to_delete:
            Witness.objects.filter(id=witness_id).delete()
        
        

        # Process other fields in the form and save them to Case model
        case_id = request.POST.get('case_id')
        case = Case.objects.get(id=case_id)
        print(case_id)
        
        # Retrieve existing witnesses associated with the case
        existing_witnesses = Witness.objects.filter(case_witness=case)

        # Iterate over existing witnesses and check for changes
        for witness_instance in existing_witnesses:
            witness_id = witness_instance.id
            name = request.POST.get(f'witness_name_{witness_id}')
            address = request.POST.get(f'witness_address_{witness_id}')
            number = request.POST.get(f'witness_number_{witness_id}')
            email = request.POST.get(f'witness_email_{witness_id}')
            
            # Check if witness data has been modified
            if (name != witness_instance.name or
                address != witness_instance.address or
                number != witness_instance.contact_number or
                email != witness_instance.email):
                
                # Update the witness instance with new data and save
                witness_instance.name = name
                witness_instance.address = address
                witness_instance.contact_number = number
                witness_instance.email = email
                witness_instance.save()

        date_latest_incident = request.POST.get('date_latest_incident')
        print(date_latest_incident)

        case.date_latest_incident = request.POST.get('date_latest_incident')
        case.incomplete_date = True if request.POST.get('incomplete_date') == 'true' else False
        case.place_of_incident = request.POST.get('place_of_incident')
        case.street = request.POST.get('street')
        case.barangay = request.POST.get('barangay')
        case.province = request.POST.get('province')
        case.city = request.POST.get('city')
        case.region = request.POST.get('region')
        case.description_of_incident = request.POST.get('description_of_incident')


        # Additional fields
        case.checkbox_ra_9262 = True if request.POST.get('checkbox_ra_9262') == 'true' else False
        case.checkbox_sexual_abuse = True if request.POST.get('checkbox_sexual_abuse') == 'true' else False
        case.checkbox_psychological_abuse = True if request.POST.get('checkbox_psychological_abuse') == 'true' else False
        case.checkbox_physical_abuse = True if request.POST.get('checkbox_physical_abuse') == 'true' else False
        case.checkbox_economic_abuse = True if request.POST.get('checkbox_economic_abuse') == 'true' else False
        case.checkbox_others = True if request.POST.get('checkbox_others') == 'true' else False
        case.others_input = request.POST.get('others_input')
        case.checkbox_ra_8353 = True if request.POST.get('checkbox_ra_8353') == 'true' else False
        case.checkbox_rape_by_sexual_intercourse = True if request.POST.get('checkbox_rape_by_sexual_intercourse') == 'true' else False
        case.checkbox_rape_by_sexual_assault = True if request.POST.get('checkbox_rape_by_sexual_assault') == 'true' else False
        case.checkbox_art_336 = True if request.POST.get('checkbox_art_336') == 'true' else False
        case.checkbox_acts_of_lasciviousness = True if request.POST.get('checkbox_acts_of_lasciviousness') == 'true' else False
        case.checkbox_ra_7877 = True if request.POST.get('checkbox_ra_7877') == 'true' else False
        case.checkbox_verbal = True if request.POST.get('checkbox_verbal') == 'true' else False
        case.checkbox_physical = True if request.POST.get('checkbox_physical') == 'true' else False
        case.checkbox_use_of_objects = True if request.POST.get('checkbox_use_of_objects') == 'true' else False
        case.checkbox_a_7610 = True if request.POST.get('checkbox_a_7610') == 'true' else False
        case.checkbox_engage_prostitution = True if request.POST.get('checkbox_engage_prostitution') == 'true' else False
        case.checkbox_sexual_lascivious_conduct = True if request.POST.get('checkbox_sexual_lascivious_conduct') == 'true' else False
        case.checkbox_ra_9775 = True if request.POST.get('checkbox_ra_9775') == 'true' else False

        # Save the case instance with updated fields
        case.save()

        # Return JSON response
        response_data = {
            'status': 'success',
            'message': 'Form submitted successfully.'
        }
        return JsonResponse(response_data)
    else:
        response_data = {
            'status': 'error',
            'message': 'Invalid request method.'
        }
        return JsonResponse(response_data)


def add_status(request, case_id):
    if request.method == 'POST':
        try:
            # Retrieve the case object based on the case_id
            case = Case.objects.get(id=case_id)
            
            # Extract status description from the POST data
            status_description = request.POST.get('status_text')

            # Create a new Status_History object
            status_history = Status_History.objects.create(
                case_status_history=case,
                status_description=status_description,
                status_date_added=timezone.now()
            )

            # Return success response
            return JsonResponse({'success': True, 'message': 'Status added successfully'})

        except Case.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Case not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

def edit_status(request, status_id):
    if request.method == 'GET':
        try:
            status = Status_History.objects.get(id=status_id)
            return JsonResponse({'success': True, 'status_description': status.status_description, 'status_date': status.status_date_added})
        except Status_History.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Status not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    elif request.method == 'POST':
        try:
            status = Status_History.objects.get(id=status_id)
            new_description = request.POST.get('new_description')
            new_date = request.POST.get('new_date')
            status.status_description = new_description
            status.status_date_added = new_date
            status.save()
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        except Status_History.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Status not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

def delete_status(request, status_id):
    if request.method == 'POST':
        try:
            status = Status_History.objects.get(id=status_id)
            status.delete()
            return JsonResponse({'success': True, 'message': 'Status deleted successfully'})
        except Status_History.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Status not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

def update_case_status(request, case_id):
    if request.method == 'POST':
        new_status = request.POST.get('status_case')  # Get the new status from the form data
        case = get_object_or_404(Case, pk=case_id)  # Get the case object
        case.status = new_status  # Update the status
        case.save()  # Save the changes
        return JsonResponse({'success': True})  # Return a JSON response indicating success
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})  # Return an error response if the request method is not POST

def tite(request):
    # check if what the button want to do. 
    action = request.POST.get('security_status')
    
    if action == "decrypted":
        request.session['security_status'] = "encrypted"
        return JsonResponse({'success': True, 'message': 'encryted successfully.'})
    
    real_passkey = 'gAAAAABlyy1ztYGcI6Qkx3bOjkMbGsEzhFFYlOU8ph3a-mGEG2yqmoKX07sIGc0bpOX2qNQcBRctnzF8GAqOI2pTNwiMo2m9SQ=='
    user_passkey = request.POST.get('user_passkey')
    
    decrypt_real_pk = decrypt_data(real_passkey)
    
    if decrypt_real_pk == user_passkey:
        request.session['security_status'] = "decrypted"
        return JsonResponse({'success': True, 'message': 'Valid passkey.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid passkey.'})