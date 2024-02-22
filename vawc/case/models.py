from django.db import models
from django.utils import timezone
from datetime import datetime

# Create your models here.
REGION_CHOICES = [
    ('region-I', 'Region I – Ilocos Region'),
    ('region-II', 'Region II – Cagayan Valley'),
    ('region-III', 'Region III – Central Luzon'),
    ('region-IV', 'Region IV‑A – CALABARZON'),
    ('mimaropa', 'MIMAROPA Region'),
    ('region-V', 'Region V – Bicol Region'),
    ('region-VI', 'Region VI – Western Visayas'),
    ('region-VII', 'Region VII – Central Visayas'),
    ('region-VIII', 'Region VIII – Eastern Visayas'),
    ('region-IX', 'Region IX – Zamboanga Peninsula'),
    ('region-X', 'Region X – Northern Mindanao'),
    ('region-XI', 'Region XI – Davao Region'),
    ('region-XII', 'Region XII – SOCCSKSARGEN'),
    ('region-XIII', 'Region XIII – Caraga'),
    ('ncr', 'NCR – National Capital Region'),
    ('car', 'CAR – Cordillera Administrative Region'),
    ('barmm', 'BARMM – Bangsamoro Autonomous Region in Muslim Mindanao'),
]

class Case(models.Model):
    case_number = models.IntegerField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True, default=None)
    TYPE_IMPACTED_VICTIM = 'Impacted'
    TYPE_REPORTING_BEHALF = 'Behalf'
    TYPE_CHOICES = [
        (TYPE_IMPACTED_VICTIM, 'The Impacted Victim'),
        (TYPE_REPORTING_BEHALF, 'Reporting on Behalf of Impacted Victim'),
    ]
    type_of_case = models.CharField(max_length=30, default='Pending',null=True, blank=True)
    CRISIS_INTERVENTION = 'crisis'
    ISSUANCE_ENFORCEMENT = 'issuance'
    SERVICE_CHOICES = [
        (CRISIS_INTERVENTION, 'Crisis Intervention Including Rescue'),
        (ISSUANCE_ENFORCEMENT, 'Issuance / Enforcement of Barangay Protection Order'),
    ]
    service_information = models.CharField(max_length=20, null=True, blank=True)
    date_latest_incident = models.CharField(max_length=150, null=True, blank=True)
    incomplete_date = models.BooleanField(default=False, null=True)
    PLACE_CHOICES = [
        ('house', 'House'),
        ('work', 'Work'),
        ('school', 'School'),
        ('commercialPlaces', 'Commercial Places'),
        ('religion', 'Religious Institutions'),
        ('placeOfMedicalTreatment', 'Place of Medical Treatment'),
        ('transport', 'Transport & Connecting Sites'),
        ('brothles', 'Brothels and Similar Establishments'),
        ('others', 'Others'),
        ('noResponse', 'No Response'),
    ]
    place_of_incident = models.CharField(max_length=150, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)
    description_of_incident = models.TextField(null=True, blank=True)

    STATUS_ACTIVE = 'Active'
    STATUS_CLOSE = 'Close'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSE, 'Close'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    date_added = models.DateField(null=True, blank=True)

    checkbox_ra_9262 = models.BooleanField(default=False)
    checkbox_sexual_abuse = models.BooleanField(default=False)
    checkbox_psychological_abuse = models.BooleanField(default=False)
    checkbox_physical_abuse = models.BooleanField(default=False)
    checkbox_economic_abuse = models.BooleanField(default=False)
    checkbox_others = models.BooleanField(default=False)
    others_input = models.CharField(max_length=100, null=True, blank=True)
    checkbox_ra_8353 = models.BooleanField(default=False)
    checkbox_rape_by_sexual_intercourse = models.BooleanField(default=False)
    checkbox_rape_by_sexual_assault = models.BooleanField(default=False)
    checkbox_art_336 = models.BooleanField(default=False)
    checkbox_acts_of_lasciviousness = models.BooleanField(default=False)
    checkbox_ra_7877 = models.BooleanField(default=False)
    checkbox_verbal = models.BooleanField(default=False)
    checkbox_physical = models.BooleanField(default=False)
    checkbox_use_of_objects = models.BooleanField(default=False)
    checkbox_a_7610 = models.BooleanField(default=False)
    checkbox_engage_prostitution = models.BooleanField(default=False)
    checkbox_sexual_lascivious_conduct = models.BooleanField(default=False)
    checkbox_ra_9775 = models.BooleanField(default=False)

    def __str__(self):
        return f"Case ID: {self.id}, Case Number: {self.case_number}"

class Status_History(models.Model):
    case_status_history = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='status_history',null=True, blank=True)
    status_description = models.TextField()
    status_date_added = models.DateTimeField()

class Contact_Person(models.Model):
    case_contact = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='contact_person',null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    suffix = models.CharField(max_length=10, null=True, blank=True)
    relationship = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    contact_number = models.CharField(max_length=100,null=True, blank=True)
    telephone_number = models.CharField(max_length=100,null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)


class Evidence(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField()

class Victim(models.Model):
    case_victim = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    middle_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    suffix = models.CharField(max_length=150, null=True, blank=True)
    date_of_birth = models.CharField(max_length=150, null=True, blank=True)
    MALE, FEMALE = 'Male', 'Female'
    SEX_CHOICES = [(MALE, 'Male'), (FEMALE, 'Female')]
    sex = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('live-in', 'Live-In'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    civil_status = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    educational_attainment = models.CharField(max_length=50, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    type_of_disability = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    contact_number = models.CharField(max_length=100,null=True, blank=True)
    telephone_number = models.CharField(max_length=100,null=True, blank=True)
    house_information = models.CharField(max_length=250, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)
    
    def __str__(self):
        return f"Victim ID: {self.id}"


class Perpetrator(models.Model):
    RELATIONSHIP_CHOICES = [
        ('currentSpouse', 'Current spouse / partner'),
        ('formerSpouse', 'Former spouse / partner'),
        ('currentFiance', 'Current fiance / dating relationship'),
        ('formerFiance', 'Former fiance / dating relationship'),
        ('employer', 'Employer / manager / supervisor'),
        ('agentOfEmployer', 'Agent of Employer'),
        ('teacher', 'Teacher / Instructor / Professor'),
        ('coach', 'Coach / trainer'),
        ('immediateFamily', 'Immediate family'),
        ('otherRelatives', 'Other Relatives'),
        ('peopleOfAuthority', 'People of authority / service provider'),
        ('neighbors', 'Neighbors / peers / coworkers / classmates'),
        ('stranger', 'Stranger'),
    ]
    case_perpetrator = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='perpetrator',null=True, blank=True)
    relationship_to_victim = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    suffix = models.CharField(max_length=10, null=True, blank=True)
    identifying_marks = models.CharField(max_length=250, null=True, blank=True)
    alias = models.CharField(max_length=100, null=True, blank=True)
    MALE, FEMALE = 'Male', 'Female'
    SEX_CHOICES = [(MALE, 'Male'), (FEMALE, 'Female')]
    sex = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    date_of_birth = models.CharField(max_length=150, null=True, blank=True)
    educational_attainment = models.CharField(max_length=50, null=True, blank=True)
    type_of_disability = models.CharField(max_length=50, null=True, blank=True)
    civil_status = models.CharField(max_length=100,null=True,blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    contact_number = models.CharField(max_length=100,null=True, blank=True)
    telephone_number = models.CharField(max_length=100,null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    house_information = models.CharField(max_length=250, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)


class Parent(models.Model):
    victim_parent = models.ForeignKey(Victim, on_delete=models.CASCADE, related_name='parents', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    suffix = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.CharField(max_length=150, null=True, blank=True)
    MALE, FEMALE = 'Male', 'Female'
    SEX_CHOICES = [(MALE, 'Male'), (FEMALE, 'Female')]
    sex = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('live-in', 'Live-In'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    civil_status = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    educational_attainment = models.CharField(max_length=150, null=True, blank=True)
    occupation = models.CharField(max_length=150, null=True, blank=True)
    type_of_disability = models.CharField(max_length=150, null=True, blank=True)
    nationality = models.CharField(max_length=150, null=True, blank=True)
    religion = models.CharField(max_length=150, null=True, blank=True)
    contact_number = models.CharField(max_length=100,null=True, blank=True)
    telephone_number = models.CharField(max_length=100,null=True, blank=True)
    house_information = models.CharField(max_length=250, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)

class Parent_Perpetrator(models.Model):
    perpetrator_parent = models.ForeignKey(Perpetrator, on_delete=models.CASCADE, related_name='parent_perp', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    suffix = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.CharField(max_length=150, null=True, blank=True)
    MALE, FEMALE = 'Male', 'Female'
    SEX_CHOICES = [(MALE, 'Male'), (FEMALE, 'Female')]
    sex = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('live-in', 'Live-In'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    civil_status = models.CharField(
        max_length=100,
        null=True,
        blank=True)
    educational_attainment = models.CharField(max_length=150, null=True, blank=True)
    occupation = models.CharField(max_length=150, null=True, blank=True)
    type_of_disability = models.CharField(max_length=150, null=True, blank=True)
    nationality = models.CharField(max_length=150, null=True, blank=True)
    religion = models.CharField(max_length=150, null=True, blank=True)
    contact_number = models.CharField(max_length=100,null=True, blank=True)
    telephone_number = models.CharField(max_length=100,null=True, blank=True)
    house_information = models.CharField(max_length=250, null=True, blank=True)
    street = models.CharField(max_length=150, null=True, blank=True)
    barangay = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)

