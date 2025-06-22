from django import forms
from gitlab_classroom.models import (Assignment,
                                     Student,
                                     Classroom,
                                     Teacher,
                                     Assessment,
                                     GroupProject)
from django.forms import inlineformset_factory


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "description", "is_group", "template_id", "deadline"]
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


class AddTeachersToClassroomForm(forms.Form):
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        label="",
        required=True
    )

    def __init__(self, *args, **kwargs):
        classroom_id = kwargs.pop('classroom_id', None)
        super(AddTeachersToClassroomForm, self).__init__(*args, **kwargs)
        if classroom_id:
            classroom = Classroom.objects.get(pk=classroom_id)
            # Exclude students who are already in this classroom
            self.fields['teacher'].queryset = Teacher.objects.exclude(id__in=classroom.teachers.all())


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


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ["score", "feedback"]
        widgets = {
            "score": forms.NumberInput(attrs={
                "class": "form-control form-control-sm",
                "min": 0,
                "step": 1,             
            }),
            "feedback": forms.Textarea(attrs={
                "rows": 2, 
                "class": "form-control form-control-sm"
            }),
        }


AssessmentFormSet = inlineformset_factory(
    Assignment,
    Assessment,
    form=AssessmentForm,
    extra=0,                
    can_delete=False,
)


class GroupProjectForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        label='Studenci',
        required=True,
    )

    class Meta:
        model = GroupProject
        fields = ['name', 'description', 'students']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        assignment_id = kwargs.pop('assignment_id', None)
        exclude_students = kwargs.pop('exclude_students', None)  # lista studentów do wykluczenia
        super().__init__(*args, **kwargs)
        if assignment_id:
            assignment = Assignment.objects.get(pk=assignment_id)
            classroom_students = assignment.classroom.students.all()
            if exclude_students:
                classroom_students = classroom_students.exclude(id__in=exclude_students)
            self.fields['students'].queryset = classroom_students
        else:
            self.fields['students'].queryset = Student.objects.none()
