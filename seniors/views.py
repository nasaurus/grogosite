# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from scripts.seniors.models import Senior, SeniorForm, ActivityForm, Activity
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms
from django.db.models import Q
from django.forms import ModelForm
from django.forms.models import model_to_dict
from django.forms.formsets import formset_factory
from django.core.mail import send_mail, EmailMessage
from django.core.exceptions import ObjectDoesNotExist
import csv

__CURRENT_TNQ_YEAR = 2012

class KerberosForm (forms.Form):
    kerberos = forms.CharField(max_length=8)

def closed(request):
    return render_to_response('seniors/closed.html')

def enterinfo(request):
    ActivityFormSet = formset_factory(ActivityForm, extra=4)
    if request.method == 'POST': #If the form has been submitted
        form = SeniorForm(request.POST)
        formset = ActivityFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            senior = form.save(commit=False)
            senior.tnq_year = __CURRENT_TNQ_YEAR
            senior.save()
            for act_form in formset.forms:
                if act_form.is_valid() and "title" in act_form.cleaned_data.keys() and act_form.cleaned_data['title']:  #Activity is valid and not blank
                    activity = act_form.save(commit=False)
                    activity.senior = senior
                    activity.save()
            
            request.session['seniorid'] = senior.id;
            sendemail(senior)
            return HttpResponseRedirect('/scripts/seniors/thanks/')
    else:
        form = SeniorForm()
        formset = ActivityFormSet()

    return render_to_response('seniors/enterinfo.html', { 'form':form, 'formset':formset } )

def thanks(request):
    if 'seniorid' in request.session:
        try:
            senior = Senior.objects.get(id=request.session['seniorid'])
        except:
            del request.session['seniorid']
            return HttpResponseRedirect('/scripts/seniors/')
    else:
        return HttpResponseRedirect('/scripts/seniors/')

    senior_object = SeniorForm(data=model_to_dict(senior))
    activities = Activity.objects.filter(senior = senior)

    return render_to_response('seniors/thanks.html', { 'senior':senior, 'senior_object':senior_object, 'activities':activities })


def email(request):
    name = "NOTHING"
    if request.method == 'POST':
        form = KerberosForm(request.POST)
        if form.is_valid():
            kerberos = form.cleaned_data['kerberos']
            request.session['kerberos'] = kerberos
            try:
                senior = Senior.objects.get(kerberos=kerberos)
                sendemail(senior)
                return HttpResponseRedirect('/scripts/seniors/emailsent/')
            except ObjectDoesNotExist:
                return HttpResponseRedirect('/scripts/seniors/noinfo/')
    else:
        form = KerberosForm()
    return render_to_response('seniors/email.html', { 'form':form })

def noinfo(request):
    if 'kerberos' in request.session:
        kerberos = request.session['kerberos']
        del request.session['kerberos']
        return render_to_response('seniors/noinfo.html', { 'kerberos':kerberos })
    else:
        return HttpResponseRedirect('/scripts/seniors/email/')

def emailsent(request):
    if 'kerberos' in request.session:
        kerberos = request.session['kerberos']
        del request.session['kerberos']
        return render_to_response('seniors/emailsent.html', { 'kerberos':kerberos })
    else:
        return HttpResponseRedirect('/scripts/seniors/email/')


def sendemail(senior):
    activities = Activity.objects.filter(senior=senior)
    message = """
This is an automated message generated by the Technique Senior Information database.

We have received the following information for inclusion in Technique 2012.  Please note that we may trim or consolidate your information to meet space constraints:

Name: %s
Name Comments: %s
Sort Letter: %s
Kerberos: %s
Major: %s
Minor: %s
Home Town: %s
Home State or Country: %s
Living Group: %s
Quote: %s
Quote Author: %s
""" % (senior.name, senior.name_comments, senior.sort_letter, senior.kerberos, senior.major, senior.minor, senior.home_town, senior.home_state_or_country, senior.lg, senior.quote, senior.quote_author)

    for activity in activities:
        message = message + "\n%s" %(activity)

    subject = "Technique 2012 Senior Information for %s"%(senior.name)
    to = ["%s@mit.edu"%senior.kerberos]
    bcc = ["tnq-seniors-info@mit.edu"]
    sender = "tnq-seniors@mit.edu"
    email = EmailMessage(subject, message, sender, to, bcc)
    email.send()

def sendsenioremail(fileobject):
    reader = csv.DictReader(fileobject)

    base_message = """Hi Senior!

Your friendly Technique staphers are busily laying out the Senior section of the yearbook, and we want to do one final check of your picture and data before we submit them.  

This is it.  What appears below goes into the book, so please double- and triple-check everything to make sure we haven't made any mistakes.  Make especially sure to check the picture (it will be much higher quality in the book!)

For our sanity please don't ask us to make any major additions, but if your name is incorrect or we spelled something wrong please let us know immediately by emailing tnq-seniors@mit.edu.  Don't email us if everything is perfect.

Requisite plug: since you're appearing in this book, don't you want to have one to keep forever?  Order a copy at http://technique.mit.edu/buy/order/ ! </plug>

See you all at our book distribution in May!

--The Staph of Technique 2012

P.S. Everyone who we think had their portrait taken should have recieved an email like this.  Obviously we can't tell if someone isn't on the list, so please ask all your senior friends to email us RIGHT NOW if they had their portrait taken and did not get this email.

Name as it will appear: %s
Picture: http://technique.mit.edu/seniorphoto/%s
Major: %s
Minor: %s
Home Town: %s
Home State (or Country): %s
Living Group: %s
Quote: %s
Author: %s
Activity 1: %s
Years 1: %s
Offices 1: %s
Activity 2: %s
Years 2: %s
Offices 2: %s
Activity 3: %s
Years 3: %s
Offices 3: %s
Activity 4: %s
Years 4: %s
Offices 4: %s
"""

    for senior in reader:
        message = base_message % (senior['BOOKNAME'],
                         senior['KERBEROS'] + senior['@FILENAME'].replace(".tif", ".JPG"),
                         senior['MAJOR'],
                         senior['MINOR'],
                         senior['HOMETOWN'],
                         senior['HOMESTATE'],
                         senior['LG'],
                         senior['QUOTE'],
                         senior['AUTHOR'],
                         senior['ACTIVITY1'],
                         senior['YEAR1'],
                         senior['OFFICE1'],
                         senior['ACTIVITY2'],
                         senior['YEAR2'],
                         senior['OFFICE2'],
                         senior['ACTIVITY3'],
                         senior['YEAR3'],
                         senior['OFFICE3'],
                         senior['ACTITY4'],
                         senior['YEAR4'],
                         senior['OFFICE4'])

        subject = "Technique 2011 Senior Information for %s"%(senior['BOOKNAME'])
        to = ["%s@mit.edu" % senior['KERBEROS']]
        bcc = ["tnq-seniors-info@mit.edu"]
        sender = "tnq-seniors@mit.edu"
        email = EmailMessage(subject, message, sender, to, bcc)
        email.send()
