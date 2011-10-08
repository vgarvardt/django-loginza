# -*- coding:utf-8 -*-
from django import forms
from django.contrib.auth.models import User


class CompleteReg(forms.Form):

    username = forms.RegexField(label=u'Имя пользователя', max_length=30, min_length=4, 
                                required=True, regex=r'^[\w.@+-]+$') 
    email = forms.EmailField(label=u'Email', required=True) 


    def __init__(self, user_id, *args, **kwargs):
        super(CompleteReg, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def clean_username(self):
        if self.cleaned_data['username']:
            try: 
                u = User.objects.exclude(id=self.user_id).get(username=self.cleaned_data['username'])
            # if username is unique - it's ok
            except User.DoesNotExist: 
                u = None

            if u is not None:
                raise forms.ValidationError(u'Пользователь с таким именем уже зарегистрирован')
        return self.cleaned_data['username']

    def clean_email(self):
        if self.cleaned_data['email']:
            try: 
                u = User.objects.exclude(id=self.user_id).get(email=self.cleaned_data['email'])
            # if email is unique - it's ok
            except User.DoesNotExist: 
                u = None

            if u is not None:
                raise forms.ValidationError(u'Пользователь с этим адресом уже зарегистрирован')
        return self.cleaned_data['email']