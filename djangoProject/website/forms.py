from django import forms


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField()


class OrderEmailForm(forms.Form):
    email = forms.EmailField()
