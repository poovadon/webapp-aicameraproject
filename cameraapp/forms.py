from django import forms

class LicensePlateSearchForm(forms.Form):
    plate_part1 = forms.CharField(max_length=10, label="อักษรต้น")
    plate_part2 = forms.CharField(max_length=10, label="เลขทะเบียน")
    plate_part3 = forms.CharField(max_length=50, label="จังหวัด")
