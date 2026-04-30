from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

class Page(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário Proprietário")
    name = models.CharField(max_length=255, verbose_name="Nome da Página")
    target_url = models.URLField(max_length=2000, verbose_name="URL de Destino")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Página"
        verbose_name_plural = "Páginas"

class Campaign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário Proprietário")
    name = models.CharField(max_length=255, verbose_name="Nome da Campanha")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Campanha"
        verbose_name_plural = "Campanhas"

class Person(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário Proprietário")
    name = models.CharField(max_length=255, verbose_name="Nome da Pessoa")
    email_or_whatsapp = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email ou WhatsApp")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

class TrackedLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário Proprietário")
    page = models.ForeignKey(Page, on_delete=models.CASCADE, verbose_name="Página")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name="Campanha")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="Pessoa")
    shortcode = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Código Encurtado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    def save(self, *args, **kwargs):
        if not self.shortcode:
            self.shortcode = get_random_string(6).lower()
            while TrackedLink.objects.filter(shortcode=self.shortcode).exists():
                self.shortcode = get_random_string(6).lower()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.page.name} - {self.campaign.name} ({self.person.name})"
        
    class Meta:
        verbose_name = "Link Rastreado"
        verbose_name_plural = "Links Rastreados"
        unique_together = ('page', 'campaign', 'person')

class ClickLog(models.Model):
    tracked_link = models.ForeignKey(TrackedLink, on_delete=models.CASCADE, related_name="clicks")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="Navegador/Dispositivo")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora")
    
    def __str__(self):
        return f"Clique em {self.tracked_link.shortcode} ({self.timestamp})"
        
    class Meta:
        verbose_name = "Registro de Clique"
        verbose_name_plural = "Registros de Cliques"

class Invite(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Código do Convite")
    is_used = models.BooleanField(default=False, verbose_name="Já foi usado?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(10)
            while Invite.objects.filter(code=self.code).exists():
                self.code = get_random_string(10)
        super().save(*args, **kwargs)
        
    def __str__(self):
        status = "Usado" if self.is_used else "Disponível"
        return f"Convite {self.code} ({status})"
        
    class Meta:
        verbose_name = "Convite de Cadastro"
        verbose_name_plural = "Convites de Cadastro"
