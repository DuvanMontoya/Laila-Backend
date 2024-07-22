# evaluaciones/admin.py

from django.contrib import admin
from .models import Evaluacion, Pregunta, Opcion, RespuestaPregunta, IntentoEvaluacion, ResultadoEvaluacion, Tag
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget



class CKEditorWidget(forms.Textarea):
    class Media:
        js = ('https://cdn.ckeditor.com/ckeditor5/41.4.2/classic/ckeditor.js', 'path/to/your/custom/config.js')




class PreguntaAdminForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = '__all__'
        widgets = {
            'texto_pregunta': CKEditor5Widget(config_name='default'),
        }





class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.save()  # Simplemente guardamos la instancia, no es necesario asignar la pregunta aquí
        formset.save_m2m()


class PreguntaAdmin(admin.ModelAdmin):
    form = PreguntaAdminForm

    list_display = ('texto_pregunta', 'tipo_pregunta', 'dificultad', 'puntos', 'activa')
    search_fields = ('texto_pregunta',)
    list_filter = ('tipo_pregunta', 'dificultad', 'activa')
    inlines = [OpcionInline]

    def save_model(self, request, obj, form, change):
        obj.save()

    def save_related(self, request, form, formsets, change):
        form.instance = form.save(commit=False)
        form.instance.save()  # Guardar el objeto Pregunta para obtener un ID
        for formset in formsets:
            if formset.model == Opcion:
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.pregunta = form.instance
                    instance.save()
                formset.save_m2m()
            else:
                formset.save()
    


class RespuestaPreguntaAdmin(admin.ModelAdmin):
    list_display = ('pregunta', 'usuario', 'intento', 'respuesta', 'es_correcta', 'puntos_obtenidos')
    search_fields = ('pregunta__texto_pregunta', 'usuario__username')
    list_filter = ('es_correcta',)
    readonly_fields = ('id',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id', 'pregunta', 'usuario', 'intento')
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        obj.save()

    def save_related(self, request, form, formsets, change):
        form.instance.calcular_puntaje_obtenido()
        form.instance.save()




class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_inicio', 'fecha_fin', 'intentos_permitidos', 'ponderacion', 'resultados_visibles', 'mostrar_resultados', 'mostrar_opciones_correctas')
    search_fields = ('titulo', 'descripcion')
    list_filter = ('tipo', 'fecha_inicio', 'fecha_fin', 'resultados_visibles', 'mostrar_resultados', 'mostrar_opciones_correctas')
    filter_horizontal = ('preguntas',)
    readonly_fields = ('id',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calcular_puntaje_maximo()

class PreguntaAdmin(admin.ModelAdmin):
    form = PreguntaAdminForm
    list_display = ('texto_pregunta', 'dificultad', 'puntos', 'activa')
    search_fields = ('texto_pregunta',)
    list_filter = ('dificultad', 'activa')
    inlines = [OpcionInline]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

class IntentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_inicio', 'fecha_fin', 'puntaje_obtenido', 'completado')
    list_filter = ('fecha_inicio', 'fecha_fin', 'usuario', 'completado')
    search_fields = ('evaluacion__titulo', 'usuario__username')
    readonly_fields = ('id',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'usuario', 'puntaje_total', 'fecha_resultado')
    search_fields = ('evaluacion__titulo', 'usuario__username')
    list_filter = ('fecha_resultado',)
    readonly_fields = ('id',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

class TagAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}

admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Evaluacion, EvaluacionAdmin)
admin.site.register(Opcion)
admin.site.register(RespuestaPregunta, RespuestaPreguntaAdmin)
admin.site.register(IntentoEvaluacion, IntentoEvaluacionAdmin)
admin.site.register(ResultadoEvaluacion, ResultadoEvaluacionAdmin)
admin.site.register(Tag, TagAdmin)
