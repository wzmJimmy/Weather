from django import forms
from reminder.models import Reminder
from  reminder.models import ReminderTime

class AddReminderForm(forms.Form):
   zipcode = forms.CharField(
       required=True,
       label="Zipcode",
       error_messages={'required': 'Please input zipcode'},
       widget=forms.TextInput(
           attrs={
               'placeholder': "zipcode",
               'class': 'form-control',
           }
       )
   )
   reminder = forms.ChoiceField(
       choices = Reminder.WARNING_CHOICE,
       widget=forms.Select(
           attrs={
               'class': 'form-control',
           }
       )
   )

class ReminderTimeForm(forms.Form):
   remindertime = forms.ChoiceField(
       choices = ReminderTime.Time_CHOICE,
       widget=forms.Select(
           attrs={
               'class': 'form-control',
           }
       )
   )
