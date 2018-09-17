import urllib, json, traceback
from collections import defaultdict
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth
from django.core.mail import EmailMessage
from reminder.models import Reminder, ReminderTime, Weather
from reminder.forms import AddReminderForm, ReminderTimeForm
from urllib.request import urlopen

# Create your views here.
'''comment here'''


def manage(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/accounts/login")
    user_id = request.user.id

    if request.method == 'POST':
        post_form = AddReminderForm(request.POST)
        if post_form.is_valid():
            zipcode = post_form.cleaned_data['zipcode']
            reminder = post_form.cleaned_data['reminder']
            if not Reminder.objects.filter(user_id=user_id, zipcode=zipcode, warning_event=reminder).exists():
                Reminder.objects.create(user_id=user_id, zipcode=zipcode, warning_event=reminder)

    reminders = Reminder.objects.filter(user_id=user_id).order_by('zipcode')
    if not ReminderTime.objects.filter(user_id=user_id).exists():
        ReminderTime.objects.create(user_id=user_id)
    reminder_time = ReminderTime.objects.get(user_id=user_id)
    form = AddReminderForm()
    return render(request, 'manage.html',
                  {'form': form, 'reminders': reminders, 'logged_in': True, 'Time': reminder_time})


def change_time(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/accounts/login")
    user_id = request.user.id
    one = ReminderTime.objects.get(user_id=user_id)

    if request.method == 'POST':
        post_form = ReminderTimeForm(request.POST)
        if post_form.is_valid():
            one.reminder_time = post_form.cleaned_data['remindertime']
            one.save()
        return HttpResponseRedirect("/")

    form = ReminderTimeForm()
    return render(request, 'changetime.html', {'form': form})


def del_reminder(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/accounts/login")
    try:
        reminder_id = int(request.GET.get('id', ''))
        p = Reminder.objects.get(id=reminder_id)
        p.delete()
    except:
        pass
    return HttpResponseRedirect("/")

def compute_time(forecast):
    hour, time = datetime.now().hour, datetime.now().date()
    if hour > 10: time += timedelta(1)
    if not forecast: time -= timedelta(1)
    return time

def get_weather(zipcode, forecast=True):
    time = compute_time(forecast)
    if not Weather.objects.filter(zipcode=zipcode,time=time).exists():
        save_weather(zipcode,time,forecast)

    return Weather.objects.get(zipcode=zipcode,time=time)

def save_weather(zipcode, time, forecast=True):
    appid = '5aa7fbc0996d84b75c4b68ecb948567a'  # your own API key
    baseurl = 'http://api.openweathermap.org/data/2.5/'
    endpoint = ('forecast' if forecast else 'weather') + '?'
    query = 'zip=%s&appid=%s&units=imperial' % (zipcode, appid)
    if forecast: query += '&cnt=16'
    actual_url = baseurl + endpoint + query
    data = {}
    with urlopen(actual_url) as result:
        data = json.loads(result.read())


    if not forecast:
        weather = [str.lower(unit['main']) for unit in data['weather']]
        type_head = [unit['id']//100 for unit in data['weather']]
        city = data['name']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']
    else:
        st,ed,timestamps = -1,-1,[unit['dt'] for unit in data['list']]
        for i,dt in enumerate(timestamps):
            if datetime.fromtimestamp(dt).date()==time:
                if st<0: st = i
                ed = i
        ed += 1

        type_head = [unit['weather'][0]['id']//100 for unit in data['list'][st:ed]]
        weather = list(set([str.lower(unit['weather'][0]['main']) for unit in data['list'][st:ed]]))
        print(st,ed,weather)
        city = data['city']['name']
        temp_min = min([unit['main']['temp_min'] for unit in data['list'][st:ed]])
        temp_max = max([unit['main']['temp_max'] for unit in data['list'][st:ed]])

    description,sign = '',0
    if len(weather) < 2:
        description += weather[0]
    else:
        for unit in weather[:-1]:
            description += unit + ", "
        description += "and " + weather[-1]
    for head in type_head:
        if head in {2, 3, 5}: sign |= 1
        elif head == 6: sign |= 2

    Weather.objects.create(zipcode=zipcode,time=time,description=description,
                           city=city,temp_max=temp_max,temp_min=temp_min,weather_sign=sign)

def generate_weather_string(data):
    return "The weather condition will be %s in %s on %s. The temperature will be %s to %s F." % (
        data.description,
        data.city,
        data.time.strftime('%m/%d/%Y'),
        data.temp_min,
        data.temp_max,
    )


def test_email(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/accounts/login")
    user_id = request.user.id
    reminders = Reminder.objects.filter(user_id=user_id)

    zipcodes = set()  # De-duplicate zipcode.
    for reminder in reminders:
        zipcodes.add(reminder.zipcode)

    body = "Dear %s,\n\n" % request.user.username
    for zipcode in zipcodes:
        body += generate_weather_string(get_weather(zipcode)) + "\n"
    body += "\nBest,\nWeather Reminder"

    message = EmailMessage("Weather Report", body, to=[request.user.email])
    message.send()
    return HttpResponseRedirect("/")

def fetch_weather(zipcodes):
    forecast_time = compute_time(True)
    today_time = forecast_time-timedelta(1)
    for zip in zipcodes:
        if not Weather.objects.filter(zipcode=zip, time=forecast_time).exists():
            save_weather(zip, forecast_time, True)
        if not Weather.objects.filter(zipcode=zip, time=today_time).exists():
            save_weather(zip, today_time, False)


def secret_trigger(request):
    pwd = request.GET.get('pwd')
    time_choice = int(request.GET.get('time'))
    if not pwd or pwd != '1214': return HttpResponse(json.dumps({'error':'not athourized'}))
    fetch_weather(set([unit.zipcode for unit in Reminder.objects.all()]))

    # percent = float(request.GET.get('percent','100'))
    reminders = Reminder.objects.filter(user__remindertime__reminder_time = time_choice)
    zip_reminders_map = defaultdict(list)
    for reminder in reminders: zip_reminders_map[reminder.zipcode].append(reminder)
    # Aggregate by user email
    emails = defaultdict(dict)
    for zipcode in zip_reminders_map:
        warnings = generate_warnings(zipcode)
        for reminder in zip_reminders_map[zipcode]:
            if reminder.warning_event in warnings:
                if zipcode not in emails[(reminder.user.username, reminder.user.email)]:
                    emails[(reminder.user.username, reminder.user.email)][zipcode] = warnings[0]
                emails[(reminder.user.username, reminder.user.email)][zipcode] += warnings[reminder.warning_event]
                reminder.reminder_sent = datetime.now()
                reminder.save()

    response = {'emails_sent': []}
    for user_id, email in emails:
        body = "Dear %s,\n\n" % user_id
        for zipcode in emails[(user_id, email)]:
            body += emails[(user_id, email)][zipcode] + "\n"
        body += "\n Best,\nWeather Reminder"
        message = EmailMessage("Weather Reminder", body, to=[email])

        message.send()
        response['emails_sent'].append(email)
    return HttpResponse(json.dumps(response))


def generate_warnings(zipcode):
    warnings = dict()
    try:
        today_weather = get_weather(zipcode, False)
        tomorrow_weather = get_weather(zipcode)
        warnings[0] = generate_weather_string(tomorrow_weather)
        warnings[1] = ""
        if tomorrow_weather.weather_sign&1 == 1:
            warnings[2] = " It will be raining, please remember to take your umbrella."
        elif tomorrow_weather.weather_sign&2 == 1:
            warnings[3] = " It will be snowing, please drive carefully."
        if float(tomorrow_weather.temp_min) - float(today_weather.temp_min) <= -10:
            warnings[4] = " The temperature will drop by more than 10 F, please wear warmer clothes."
        elif float(tomorrow_weather.temp_max) - float(today_weather.temp_max) >= 10:
            warnings[5] = " The temperature will rise by more than 10 F."
    except:
        print(traceback.format_exc())
    return warnings
