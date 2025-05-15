from django.contrib import admin
from gitlab_classroom.models import Teacher, Classroom, Assignment, Student
from django.contrib.auth.admin import UserAdmin

# admin.site.register(Teacher, UserAdmin)
# admin.site.register(Classroom)
admin.site.register(Student)

@admin.register(Teacher)
class TeacherAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("gitlab_id",)
    fieldsets = UserAdmin.fieldsets + (("Gitlab Information", {"fields": ("gitlab_id",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Gitlab Information", {"fields": ("gitlab_id",)}),)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ["title", "creation_date", "organization", "created_by",]
    list_filter = ["created_by", ]
    search_fields = ["title", ]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "creation_date", "deadline", "is_group", "classroom", ]
    list_filter = ["creation_date", ]
    search_fields = ["title", ]
