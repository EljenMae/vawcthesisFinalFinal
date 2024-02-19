from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotFound, QueryDict
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
# Create your views here.

from .utils import encrypt_data, decrypt_data
import base64

#models
from case.models import *
from account.models import *

def home_view (request):
    return render(request, 'landing/home.html')

def login_view (request):
    return render(request, 'login/login.html')

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


def report_violence_view (request):
    return render(request, 'landing/report_violence.html')

def impact_victim_view (request):
    return render(request, 'landing/case_type/impacted-victim.html')

def behalf_victim_view (request):
    return render(request, 'landing/case_type/behalf-victim.html')

def add_case(request):
    if request.method == 'POST':
        
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


@login_required
def view_case(request, case_id):
    try:
        # Retrieve the case object from the database based on the case_id
        case = Case.objects.get(id=case_id)
        # Retrieve related objects such as contact persons, evidence, victims, perpetrators, and parents
        contact_persons = Contact_Person.objects.filter(case_contact=case)
        evidences = Evidence.objects.filter(case=case)
        victims = Victim.objects.filter(case_victim=case)
        perpetrators = Perpetrator.objects.filter(case_perpetrator=case)
        parents = Parent.objects.filter(victim_parent__in=victims)
        
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
                perpetrator.date_of_birth = decrypt_data(perpetrator.date_of_birth)
                perpetrator.nationality = decrypt_data(perpetrator.nationality)
                perpetrator.house_information = decrypt_data(perpetrator.house_information)
                perpetrator.street = decrypt_data(perpetrator.street)
                perpetrator.barangay = decrypt_data(perpetrator.barangay)
                perpetrator.province = decrypt_data(perpetrator.province)
                perpetrator.region = decrypt_data(perpetrator.region)
        

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
        return render(request, 'barangay-admin/case/view-case.html', {
            'case': case,
            'contact_persons': contact_persons,
            'evidence': evidences,
            'victims': victims,
            'perpetrators': perpetrators,
            'parents': parents,
            'global': request.session
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
        first_name = request.POST.get('victim_first_name')
        middle_name = request.POST.get('victim_middle_name')
        last_name = request.POST.get('victim_last_name')
        suffix = request.POST.get('victim_suffix_name')
        date_of_birth = request.POST.get('victim_date_of_birth')
        sex = request.POST.get('victim_sex')
        civil_status = request.POST.get('victim_civil_status')
        educational_attainment = request.POST.get('victim_educational_attainment')
        occupation = request.POST.get('victim_occupation')
        type_of_disability = request.POST.get('victim_type_of_disability')
        nationality = request.POST.get('victim_nationality')
        religion = request.POST.get('victim_religion')
        contact_number = request.POST.get('victim_contact_number')
        telephone_number = request.POST.get('victim_telephone_number')
        house_information = request.POST.get('victim_house_information')
        street = request.POST.get('victim_street')
        barangay = request.POST.get('victim_barangay')
        province = request.POST.get('victim_province')
        city = request.POST.get('victim_city')
        region = request.POST.get('victim_region')

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
        first_name = request.POST.get('perpetrator_first_name')
        middle_name = request.POST.get('perpetrator_middle_name')
        last_name = request.POST.get('perpetrator_last_name')
        suffix = request.POST.get('perpetrator_suffix_name')
        perpetrator_identifying_marks = request.POST.get('perpetrator_identifying_marks')
        perpetrator_alias = request.POST.get('perpetrator_alias')
        perp_relationship_victim = request.POST.get('perp-relationship-victim')
        date_of_birth = request.POST.get('perpetrator_date_of_birth')
        sex = request.POST.get('perpetrator_sex')
        civil_status = request.POST.get('perpetrator_civil_status')
        educational_attainment = request.POST.get('perpetrator_educational_attainment')
        occupation = request.POST.get('perpetrator_occupation')
        type_of_disability = request.POST.get('perpetrator_type_of_disability')
        nationality = request.POST.get('perpetrator_nationality')
        religion = request.POST.get('perpetrator_religion')
        contact_number = request.POST.get('perpetrator_contact_number')
        telephone_number = request.POST.get('perpetrator_telephone_number')
        house_information = request.POST.get('perpetrator_house_information')
        street = request.POST.get('perpetrator_street')
        barangay = request.POST.get('perpetrator_barangay')
        province = request.POST.get('perpetrator_province')
        city = request.POST.get('perpetrator_city')
        region = request.POST.get('perpetrator_region')

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
    return JsonResponse({'success': True, 'message': 'Perpetrator deleted successfully'})

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

@require_POST
def update_status(request):
    case_id = request.POST.get('case_id')
    status_text = request.POST.get('status_text')
    status_date = request.POST.get('status_date')
    
    # Retrieve the Case object
    case = Case.objects.get(id=case_id)
    
    # Update the status fields
    if status_text:
        status_text = status_text.capitalize()
        case.status_description = status_text
    if status_date:
        case.status_date = status_date
    case.save()  # Save the changes
    
    # Return the updated status as JSON response
    return JsonResponse({'status_description': status_text, 'status_date': status_date})

@require_POST
def update_status_case(request):
    case_id = request.POST.get('case_id')
    status = request.POST.get('status_case')

    print (status)

    # Update the status for the given case_id
    case = Case.objects.get(id=case_id)
    case.status = status
    case.save()

    # Return success response
    return JsonResponse({'status': 'success'})

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


        # Process other fields in the form and save them to Case model
        case_id = request.POST.get('case_id')
        case = Case.objects.get(id=case_id)
        print(case_id)

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