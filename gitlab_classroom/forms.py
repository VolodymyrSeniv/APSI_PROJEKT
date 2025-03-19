from django import forms
from gitlab_classroom.models import Assignment, Student, Classroom


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "description", "template_id", "deadline"]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'template_id': forms.TextInput(attrs={'type': 'text'}),
        }
        # It's important to specify the input format if you're using a custom format
        input_formats = ['%Y-%m-%dT%H:%M']

class AddStudentToClassroomForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),  # Start with an empty queryset
        label="",
        required=True
    )

    def __init__(self, *args, **kwargs):
        classroom_id = kwargs.pop('classroom_id', None)
        super(AddStudentToClassroomForm, self).__init__(*args, **kwargs)
        if classroom_id:
            classroom = Classroom.objects.get(pk=classroom_id)
            # Exclude students who are already in this classroom
            self.fields['student'].queryset = Student.objects.exclude(id__in=classroom.students.all())


class RemoveStudentFromClassroomForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.none(), label="Select Student to Remove")


class ClassroomSearchForm(forms.Form):
    title = forms.CharField(max_length=255,
                            required=False,
                            label="",
                            widget=forms.TextInput(
                                attrs={
                                    "placeholder": "search by title"
                                }
                            )
                        )


class AssignmentSearchForm(forms.Form):
    title = forms.CharField(max_length=255,
                            required=False,
                            label="",
                            widget=forms.TextInput(
                                attrs={
                                    "placeholder": "search by title"
                                }
                            )
                        )


class StudentSearchForm(forms.Form):
    gitlab_username = forms.CharField(max_length=255,
                                      required=False,
                                      label="",
                                      widget=forms.TextInput(
                                          attrs={
                                              "placeholder":"search by username"
                                          }
                                    )
                                )

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label=None,  # No label is displayed
        widget=forms.ClearableFileInput(attrs={
            'class': 'custom-file-input',  # Custom class for Bootstrap styling
            'id': 'customFile',  # Custom ID for the input element
        }),
    )
