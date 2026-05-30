import re 

from urllib.parse import urlparse 
from django import forms 
from django.core.paginator import Paginator

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")
AVATAR_FONT_SIZE = 130
PER_PAGE = 12

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


def generate_avatar(user):
        size = 256
        bg = random.choice(AVATAR_COLORS)
        image = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(image)
        letter = (self.name[:1] or "?").upper()

        font_path = (
            settings.BASE_DIR / "static" / "fonts"
            / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
        )
        try:
            font = ImageFont.truetype(str(font_path), AVATAR_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        position = ((size - text_w) / 2 - bbox[0], (size - text_h) / 2 - bbox[1])
        draw.text(position, letter, fill="#FFFFFF", font=font)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        filename = f"avatar_{uuid.uuid4()}.png"
        user.avatar.save(filename, ContentFile(buffer.getvalue()), save=False)

def paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))
