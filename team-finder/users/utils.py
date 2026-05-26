import re 
from urllib.parse import urlparse 
from django import forms 

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")

def normalize_phone(phone): 
    """Приводит 8XXXXXXXXXX и +7XXXXXXXXXX к единому виду +7XXXXXXXXXX.""" 
    phone = phone.strip().replace(" ", "") 
    if phone.startswith("8"): 
        phone = "+7" + phone[1:] 
    return phone


def validate_github(url): 
    if not url: 
        return url 
    host = (urlparse(url).netloc or "").lower() 
    if host.startswith("www."): 
        host = host[4:] 
    if host != "github.com": 
        raise forms.ValidationError("Ссылка должна вести на github.com") 
    return url 


def clean_phone(self): 
        phone = self.cleaned_data.get("phone", "").strip() 
        if not phone: 
            return phone 
        phone = normalize_phone(phone) 
        if not PHONE_RE.match(phone): 
            raise forms.ValidationError( 
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX" 
            ) 
        qs = User.objects.filter(phone=phone).exclude(pk=self.instance.pk) 
        if qs.exists(): 
            raise forms.ValidationError("Этот номер телефона уже используется") 
        return phone
