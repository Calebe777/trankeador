import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from .models import TrackedLink, ClickLog
import qrcode
import io

def redirect_view(request, shortcode):
    link = get_object_or_404(TrackedLink, shortcode=shortcode)
    
    # 1. Registrar o clique
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    if ip and ',' in ip:
        ip = ip.split(',')[0]
        
    ClickLog.objects.create(
        tracked_link=link,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
    )
    
    # 2. Montar a URL final com UTMs
    target = link.page.target_url
    
    # Extrair os query params que já estão no target_url (se houver)
    parsed_url = urllib.parse.urlparse(target)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    # Adicionar UTMs gerados automaticamente (limpando espaços para evitar urls zoadas)
    source = link.person.name.replace(' ', '_').lower()
    campaign = link.campaign.name.replace(' ', '_').lower()
    
    query_params['utm_source'] = [source]
    query_params['utm_campaign'] = [campaign]
    query_params['utm_medium'] = ['tracker']
    
    # Adicionar parâmetros extras que o usuário possa ter passado no link curto
    # Ex: go.acadiprev.com.br/xyz?fbclid=123
    for key, value in request.GET.items():
        query_params[key] = [value]
        
    # Reconstruir a query string
    new_query_string = urllib.parse.urlencode(query_params, doseq=True)
    
    # Construir a URL final
    final_url = urllib.parse.urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query_string,
        parsed_url.fragment
    ))
    
    return HttpResponseRedirect(final_url)

def generate_qr(request, shortcode):
    link = get_object_or_404(TrackedLink, shortcode=shortcode)
    
    # A URL completa que o QR code vai apontar
    full_url = request.build_absolute_uri(f"/go/{shortcode}")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import Page, Campaign, Person, TrackedLink, Invite

def register_view(request):
    code = request.GET.get('code')
    if not code:
        return render(request, 'registration/register_invalid.html', {'error': 'Código de convite ausente.'})
        
    try:
        invite = Invite.objects.get(code=code)
    except Invite.DoesNotExist:
        return render(request, 'registration/register_invalid.html', {'error': 'Código de convite inválido.'})
        
    if invite.is_used:
        return render(request, 'registration/register_invalid.html', {'error': 'Este convite já foi utilizado.'})
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            invite.is_used = True
            invite.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form, 'code': code})

@login_required
def dashboard_view(request):
    user = request.user
    links = TrackedLink.objects.filter(user=user).select_related('page', 'campaign', 'person').annotate(click_count=Count('clicks')).order_by('-created_at')[:10]
    total_links = TrackedLink.objects.filter(user=user).count()
    total_clicks = ClickLog.objects.filter(tracked_link__user=user).count()
    return render(request, 'core/dashboard.html', {
        'links': links,
        'total_links': total_links,
        'total_clicks': total_clicks
    })

from django.http import JsonResponse

@login_required
def clicks_api(request):
    """Endpoint JSON para polling de cliques em tempo real."""
    user = request.user
    links = TrackedLink.objects.filter(user=user).annotate(click_count=Count('clicks'))
    total_clicks = ClickLog.objects.filter(tracked_link__user=user).count()
    total_links = TrackedLink.objects.filter(user=user).count()
    
    link_data = {
        str(link.id): link.click_count for link in links
    }
    
    return JsonResponse({
        'total_clicks': total_clicks,
        'total_links': total_links,
        'links': link_data,
    })

class UserOwnedMixin(LoginRequiredMixin):
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
        
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# === PAGES ===
class PageListView(LoginRequiredMixin, ListView):
    model = Page
    template_name = 'core/list.html'
    context_object_name = 'items'
    extra_context = {'title': 'Páginas Globais', 'create_url': 'page_create'}

class PageCreateView(LoginRequiredMixin, CreateView):
    model = Page
    fields = ['name', 'target_url']
    template_name = 'core/form.html'
    success_url = reverse_lazy('page_list')
    extra_context = {'title': 'Nova Página', 'back_url': reverse_lazy('page_list')}
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# === CAMPAIGNS ===
class CampaignListView(UserOwnedMixin, ListView):
    model = Campaign
    template_name = 'core/list.html'
    context_object_name = 'items'
    extra_context = {'title': 'Minhas Campanhas', 'create_url': 'campaign_create'}

class CampaignCreateView(UserOwnedMixin, CreateView):
    model = Campaign
    fields = ['name', 'description']
    template_name = 'core/form.html'
    success_url = reverse_lazy('campaign_list')
    extra_context = {'title': 'Nova Campanha', 'back_url': reverse_lazy('campaign_list')}

# === PERSONS ===
class PersonListView(UserOwnedMixin, ListView):
    model = Person
    template_name = 'core/list.html'
    context_object_name = 'items'
    extra_context = {'title': 'Minhas Pessoas/Parceiros', 'create_url': 'person_create'}

class PersonCreateView(UserOwnedMixin, CreateView):
    model = Person
    fields = ['name', 'email_or_whatsapp']
    template_name = 'core/form.html'
    success_url = reverse_lazy('person_list')
    extra_context = {'title': 'Nova Pessoa', 'back_url': reverse_lazy('person_list')}

# === TRACKED LINKS ===
from django.db.models import Count

class TrackedLinkListView(UserOwnedMixin, ListView):
    model = TrackedLink
    template_name = 'core/link_list.html'
    context_object_name = 'items'
    extra_context = {'title': 'Meus Links Rastreados', 'create_url': 'link_create'}
    
    def get_queryset(self):
        return super().get_queryset().select_related('page', 'campaign', 'person').annotate(click_count=Count('clicks'))

class TrackedLinkCreateView(UserOwnedMixin, CreateView):
    model = TrackedLink
    fields = ['page', 'campaign', 'person']
    template_name = 'core/form.html'
    success_url = reverse_lazy('link_list')
    extra_context = {'title': 'Novo Link Rastreado', 'back_url': reverse_lazy('link_list')}
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Páginas são globais, Campanhas e Pessoas permanecem privadas
        form.fields['page'].queryset = Page.objects.all()
        form.fields['campaign'].queryset = Campaign.objects.filter(user=self.request.user)
        form.fields['person'].queryset = Person.objects.filter(user=self.request.user)
        return form

