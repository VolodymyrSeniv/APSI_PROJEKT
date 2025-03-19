import csv
import json
import gitlab
import re
from django.contrib.auth.decorators import login_required
from django.forms import BaseModelForm
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.views import generic
from gitlab_classroom.forms import (ClassroomSearchForm,
                                    AssignmentSearchForm,
                                    StudentSearchForm,
                                    AddStudentToClassroomForm,
                                    UploadFileForm)
from gitlab_classroom.models import Classroom, Assignment, Student
from gitlab_classroom.forms import AssignmentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from gitlab import GitlabGetError


# Create your views here.
@login_required
def index(request: HttpResponse) -> HttpRequest:
    context = {
        "name": request.session["name"],
        "email": request.session["email"]
    }
    return render(request, "gitlab_classroom/index.html", context=context)


#this is a classbased representation of a classrooms
class ClassroomsListView(LoginRequiredMixin, generic.ListView):
    model = Classroom
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ClassroomsListView, self).get_context_data(**kwargs)
        title = self.request.GET.get("title", "")
        context["search_form"] = ClassroomSearchForm(
            initial={"title": title}
        )
        return context

    def get_queryset(self):
        queryset = Classroom.objects.select_related("teacher").prefetch_related("students").filter(teacher=self.request.user)
        form = ClassroomSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(title__icontains=form.cleaned_data["title"])
        """Override to filter assignments to those owned by the current user."""
        return queryset


class ClassroomsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Classroom
    context_object_name = 'classroom'
    template_name = 'gitlab_classroom/classroom_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classroom_id = self.kwargs.get('pk')
        context['add_student_form'] = AddStudentToClassroomForm(classroom_id=classroom_id)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        classroom_id = self.kwargs.get('pk')
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
        if 'add_student' in request.POST:
            add_form = AddStudentToClassroomForm(request.POST, classroom_id=classroom_id)
            if add_form.is_valid():
                try:
                    group = gl.groups.get(self.object.gitlab_id)
                    subgroups = group.subgroups.list(all=True)
                    members_group = gl.groups.get(subgroups[1].id)
                    student = add_form.cleaned_data['student']
                    if subgroups:
                        member = members_group.members.create({'user_id': student.gitlab_id,
                                                            'access_level': gitlab.const.DEVELOPER_ACCESS})
                    self.object.students.add(student)
                    messages.success(self.request, "Student was successfully added")
                    return HttpResponseRedirect(self.object.get_absolute_url())
                except GitlabGetError:
                    messages.error(self.request, "Student has no account on GitLab.")
                except Exception as e:
                    messages.error(self.request, "Student has no account on GitLab.")

        elif 'remove_student' in request.POST:
            student_id = request.POST.get('student_id')
            if student_id:
                try:
                    group = gl.groups.get(self.object.gitlab_id)
                    subgroups = group.subgroups.list(all=True)
                    members_group = gl.groups.get(subgroups[1].id)
                    student = get_object_or_404(Student, id=student_id)
                    member = members_group.members.get(student.gitlab_id)
                    member.delete()
                    self.object.students.remove(student)
                    return HttpResponseRedirect(self.object.get_absolute_url())
                except GitlabGetError:
                    messages.error(self.request, "Student is no longer a GitLab group member.")
                    self.object.students.remove(student)
                except Exception as e:
                    messages.error(self.request, f"Student is no longer a GitLab group member: {e}.")

        elif 'fork_projects' in request.POST:
            assignment_id = request.POST.get('assignment_id')
            assignment = get_object_or_404(Assignment, pk=assignment_id)
            try:
                    gitlab_template_id = assignment.template_id
                    assignments_group = gl.groups.get(assignment.gitlab_id)
                    classroom_group = gl.groups.get(self.object.gitlab_id)
                    members_group = self.create_or_get_subgroup(classroom_group, 'MEMBERS')
                    self.fork_project_for_students(assignments_group, gitlab_template_id, members_group)
                    messages.success(self.request, "Projects successfully forked for all students.")
            except Exception as e:
                    messages.error(self.request, f"An error occurred during forking: {e}")

            return HttpResponseRedirect(self.object.get_absolute_url())

        return self.render_to_response(self.get_context_data())

    def create_or_get_subgroup(self, parent_group, subgroup_name):
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
        subgroups = parent_group.subgroups.list(all=True)
        for subgroup in subgroups:
            if subgroup.name == subgroup_name:
                return gl.groups.get(subgroup.id)
        subgroup_data = {
            'name': subgroup_name,
            'path': subgroup_name,
            'parent_id': parent_group.id
        }
        return gl.groups.create(subgroup_data)

    def fork_project_for_students(self, assignments_group, base_project_id, student_group):
        user = self.request.user
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
        students = gl.groups.get(student_group.id).members.list(all=True)
        base_project = gl.projects.get(base_project_id)
        for student in students:
            if int(student.id) != int(user.gitlab_id):
                # Sanitize the project name and path
                personal_group_name = sanitize_name(f"{assignments_group.name}_{student.username}")
                existing_projects = gl.projects.list(search=f"{personal_group_name}_project")
                project_exists = any(proj for proj in existing_projects if proj.namespace['id'] == assignments_group.id)
                if not project_exists:
                    sanitized_project_name = sanitize_name(f"{personal_group_name}_project")
                    forked_project_data = base_project.forks.create({
                        'namespace': assignments_group.id,
                        'name': sanitized_project_name,
                        'path': sanitized_project_name
                    })
                    forked_project = gl.projects.get(forked_project_data.id)

                    forked_project.members.create({
                        'user_id': student.id,
                        'access_level': gitlab.const.AccessLevel.DEVELOPER
                    })
                    print(f"Project forked for {student.username} in subgroup {personal_group_name}")

        return self.render_to_response(self.get_context_data())

def sanitize_name(name):
        # Replace any invalid characters with '_'
        sanitized_name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', name)
        # Ensure the name does not start with '-', end with '.', '.git', or '.atom'
        sanitized_name = sanitized_name.strip('-.')
        return sanitized_name

class ClassroomCreateView(LoginRequiredMixin, generic.CreateView):
    model = Classroom
    fields = ["title", "description", "organization"]
    success_url = reverse_lazy("gitlab_classroom:classroom-list")
    template_name = "gitlab_classroom/classroom_form.html"
    
    def form_valid(self, form):
        user = self.request.user
        form.instance.teacher = user
        response = super().form_valid(form)

        try:
            access_token = self.request.session["access_token"]
        except KeyError:
            return HttpResponse(status=403)  # Forbidden if no access token

        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=access_token)

        # Sanitize the title to create a valid path
        sanitized_title = re.sub(r'[^a-zA-Z0-9_\-.]', '_', self.object.title.lower()).strip('-.')

        group_data = {
            'name': self.object.title,
            'path': sanitized_title,
            'description': self.object.description
        }

        try:
            group = gl.groups.create(group_data)
        except gitlab.exceptions.GitlabCreateError:
            self.object.delete()  # Clean up the created object on failure
            return HttpResponse(status=500)  # Internal Server Error

        # Create members and assignments subgroups
        def create_subgroup(name_suffix, description):
            subgroup_path = f"{group_data['path']}_{name_suffix}".strip('-.')

            subgroup_data = {
                "name": name_suffix,
                "path": subgroup_path,
                "description": description,
                "parent_id": group.id
            }
            return gl.groups.create(subgroup_data)

        members = create_subgroup("MEMBERS", "Classroom Members")
        assignments = create_subgroup("ASSIGNMENTS", "Assignments folder")

        self.object.gitlab_id = group.id
        self.object.save()
        messages.success(self.request, "Classroom was successfully created.")
        return response


class ClassroomUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Classroom
    fields = ["title", "description", "organization"]
    success_url = reverse_lazy("gitlab_classroom:classroom-list")
    template_name = "gitlab_classroom/classroom_form.html"
    #connect to gitlab functionality

    def form_valid(self, form):
        # This method is called when the form is valid, before saving the object.
        # Access the current user
        self.object = self.get_object()
        response = super().form_valid(form)
        try:
        # Optionally, access the GitLab ID stored in the Classroom instance
            gitlab_group_id = form.instance.gitlab_id
            # Example: update a GitLab group's name or other details
            # Configure access to your GitLab instance
            gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
            group = gl.groups.get(gitlab_group_id)
            # Assuming you want to update the name of the group based on a field in your form
            group.name = form.cleaned_data['title']
            group.description = form.cleaned_data['description']
            group.save()
            messages.success(self.request, "Classroom was successfully updated.")
            # Don't forget to save the form and the instance it represents
            response = super().form_valid(form)
        except GitlabGetError:
            messages.error(self.request, "GitLab group could not be found. Classroom was deleted.")
            self.object.delete()  # Delete the classroom instance
        except Exception as e:
            # Log the exception if necessary
            messages.error(self.request, f"An error occurred while trying to update the GitLab group: {str(e)}. It doesn't exist.")
            self.object.delete()  # Delete the classroom instance
        return response


class ClassroomDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Classroom
    template_name = "gitlab_classroom/classroom_confirm_delete.html"
    success_url = reverse_lazy("gitlab_classroom:classroom-list")

    def form_valid(self, form):
        # Get the object
        self.object = self.get_object()
        response = super().form_valid(form)
        if self.object.gitlab_id:
            gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                            private_token=self.request.session["access_token"])
            try:
                group = gl.groups.get(self.object.gitlab_id)
                group.delete()
                messages.success(self.request, "Classroom and associated GitLab group were deleted successfully.")
            except GitlabGetError:
                messages.error(self.request, "GitLab group could not be found. Classroom deleted without deleting the GitLab group.")
            except Exception as e:
                # Log the exception if necessary
                messages.error(self.request, f"An error occurred while trying to delete the GitLab group: {str(e)}. It doesn't exist.")
        return response


class StudentsListView(LoginRequiredMixin, generic.ListView):
    model = Student
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(StudentsListView, self).get_context_data(**kwargs)
        gitlab_username = self.request.GET.get("gitlab_username", "")
        context["search_form"] = StudentSearchForm(
            initial={"gitlab_username" : gitlab_username}
        )
        context["upload_form"] = UploadFileForm()
        return context

    def get_queryset(self):
        queryset = Student.objects.all()
        form = StudentSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(gitlab_username__icontains=form.cleaned_data["gitlab_username"])

    def post(self, request, *args, **kwargs):
        try:
            if 'file' in request.FILES:
                upload_form = UploadFileForm(request.POST, request.FILES)
                if upload_form.is_valid():
                    file = request.FILES['file']
                    file_extension = file.name.split('.')[-1].lower()
                    if file_extension == 'txt':
                        self.handle_txt_file(file)
                    elif file_extension == 'csv':
                        self.handle_csv_file(file)
                    elif file_extension == 'json':
                        self.handle_json_file(file)
                    else:
                        messages.error(request, 'Unsupported file format. Please upload a .txt, .csv, or .json file.')
                        return self.get(request, *args, **kwargs)

                    messages.success(request, 'Students were successfully created.')
                    return redirect('gitlab_classroom:student-list')
                else:
                    messages.error(request, 'Invalid form data.')
                    return self.get(request, *args, **kwargs)

        except Exception as e:
            messages.error(request, f"An error occurred during file processing: {e}.")
            return self.get(request, *args, **kwargs)

        if 'check_gitlab' in request.POST:
            try:
                self.check_gitlab_students()
                messages.success(request, "GitLab accounts were checked and updated.")
            except Exception as e:
                messages.error(request, f"An error occurred while checking GitLab accounts: {e}.")

            return redirect('gitlab_classroom:student-list')

        return self.get(request, *args, **kwargs)


    def check_gitlab_students(self):
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                           private_token=self.request.session["access_token"])

        students = Student.objects.all()
        for student in students:
            gitlab_username = student.gitlab_username.strip()
            gitlab_users = gl.users.list(username=gitlab_username)

            if gitlab_users:
                gitlab_user = gitlab_users[0]
                student.gitlab_id = gitlab_user.id
                student.gl_flag = True
            else:
                student.gitlab_id = 0  # or None, if that's more appropriate
                student.gl_flag = False

            student.save()

    def handle_txt_file(self, file):
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                        private_token=self.request.session["access_token"])
        for line in file:
            line = line.decode('utf-8').strip()
            data = line.split(',')
            if len(data) == 5:

                if Student.objects.filter(gitlab_username=data[0].strip()).exists():
                    continue

                students = gl.users.list(username=data[0].strip())
                gitlab_id = 0
                gl_flag = False
                if students:
                    student = students[0]
                    if not Student.objects.filter(gitlab_id=student.id).exists():
                        gitlab_id = student.id
                        gl_flag = True
                Student.objects.create(
                    gitlab_id=gitlab_id,
                    gitlab_username=data[0].strip(),
                    first_name=data[1].strip(),
                    second_name=data[2].strip(),
                    email=data[3].strip(),
                    student_id=data[4].strip(),
                    gl_flag=gl_flag
                )
            else:
                print(f"No GitLab user found for username {data[1].strip()}")

    def handle_csv_file(self, file):
        reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                           private_token=self.request.session["access_token"])
        for row in reader:
            if Student.objects.filter(gitlab_username=row['gitlab_username'].strip()).exists():
                continue

            students = gl.users.list(username=row['gitlab_username'].strip())
            gitlab_id = 0
            gl_flag = False
            if students:
                student = students[0]
                if not Student.objects.filter(gitlab_id=student.id).exists():
                    gitlab_id = student.id
                    gl_flag = True

            Student.objects.create(
                gitlab_username=row['gitlab_username'].strip(),
                first_name=row['first_name'].strip(),
                second_name=row['second_name'].strip(),
                email=row['email'].strip(),
                student_id=row['student_id'].strip(),
                gitlab_id=gitlab_id,
                gl_flag=gl_flag
            )

    def handle_json_file(self, file):
        data = json.load(file)
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                           private_token=self.request.session["access_token"])
        for entry in data:
            if Student.objects.filter(gitlab_username=entry['gitlab_username'].strip()).exists():
                continue

            students = gl.users.list(username=entry['gitlab_username'].strip())
            gitlab_id = 0
            gl_flag = False
            if students:
                student = students[0]
                if not Student.objects.filter(gitlab_id=student.id).exists():
                    gitlab_id = student.id
                    gl_flag = True

            Student.objects.create(
                gitlab_username=entry['gitlab_username'].strip(),
                first_name=entry['first_name'].strip(),
                second_name=entry['second_name'].strip(),
                email=entry['email'].strip(),
                student_id=entry['student_id'].strip(),
                gitlab_id=gitlab_id,
                gl_flag=gl_flag
            )

class StudentsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Student


class StudentCreateView(LoginRequiredMixin, generic.CreateView):
    model = Student
    fields = ["gitlab_username",
              "first_name",
              "second_name",
              "student_id",
              "email"]
    success_url = reverse_lazy("gitlab_classroom:student-list")
    template_name = "gitlab_classroom/student_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                        private_token=self.request.session["access_token"])
        try:
            students = gl.users.list(username=self.object.gitlab_username)
            if students:
                student = students[0]
                # Check if the gitlab_id already exists
                if not Student.objects.filter(gitlab_id=student.id).exists():
                    self.object.gitlab_id = student.id
                    self.object.gl_flag = True
                else:
                    # Handle duplicate gitlab_id scenario, maybe set gitlab_id to None or handle differently
                    print(f"Duplicate gitlab_id detected: {student.id}")
            else:
                print("No user found with that username.")
                messages.error(self.request, f"Student {self.object.gitlab_username} has no GitLab account.")
        except Exception as e:
            print("An error occurred:", e)
        self.object.save()
        messages.success(self.request, f"Student {self.object.gitlab_username} was successfully created")
        return response


class StudentUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Student
    fields = {"gitlab_id",
              "gitlab_username",
              "first_name",
              "second_name",
              "email",
              "student_id"}
    success_url=reverse_lazy("gitlab_classroom:student-list")
    template_name="gitlab_classroom/student_form.html"

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Student details were updated successfully.")
        return response


class StudentDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Student
    template_name = "gitlab_classroom/student_confirm_delete.html"
    success_url = reverse_lazy("gitlab_classroom:student-list")

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Student was deleted")
        return response

#this is a classbased representation of assignments
class AssignmentsListView(LoginRequiredMixin, generic.ListView):
    model = Assignment
    queryset = Assignment.objects.select_related("classroom", "classroom__teacher").prefetch_related("classroom__students")
    #above i am fixing n+1 problem i should fix it later
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(AssignmentsListView, self).get_context_data(**kwargs)
        title = self.request.GET.get("title", "")
        context["search_form"] = AssignmentSearchForm(
            initial={"title": title}
        )
        return context

    def get_queryset(self):
        queryset = Assignment.objects.select_related("classroom", "classroom__teacher").prefetch_related("classroom__students").filter(teacher=self.request.user)
        form = AssignmentSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(title__icontains=form.cleaned_data["title"])
        """Override to filter assignments to those owned by the current user."""
        return queryset


class AssignmentsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Assignment


class AssignmentCreateView(LoginRequiredMixin, generic.CreateView):
    model = Assignment
    form_class = AssignmentForm
    success_url = reverse_lazy("gitlab_classroom:assignment-list")
    template_name="gitlab_classroom/assignment_form.html"

    def form_valid(self, form):
        user = self.request.user
        form.instance.teacher = user
        classroom = get_object_or_404(Classroom, pk=self.kwargs.get('pk'))
        form.instance.classroom = classroom
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl',
                           private_token=self.request.session["access_token"])
        template_id = form.cleaned_data.get('template_id')
        try:
            template = gl.projects.get(template_id)
        except gitlab.exceptions.GitlabGetError:
            form.add_error('template_id', f"Template ID {template_id} does not exist on GitLab.")
            return self.form_invalid(form)
        response = super().form_valid(form)

        if classroom.gitlab_id:
            try:
                group = gl.groups.get(classroom.gitlab_id)
                subgroups = group.subgroups.list(all=True)
                assignments_group = gl.groups.get(subgroups[0].id)
                sanitized_title = re.sub(r'[^a-zA-Z0-9_\-.]', '_', form.instance.title.lower()).strip('-.')
                subgroup_data = {
                    "name": sanitized_title,
                    "path": f"{assignments_group.name}_{sanitized_title}",
                    "description": form.instance.description,
                    "parent_id": assignments_group.id  
                }
                group = gl.groups.create(subgroup_data)
                self.object.repo_url = group.web_url
                self.object.gitlab_id = group.id
                self.object.save()
                messages.success(self.request, "Assignment was successfully created")
            except Exception as e:
                messages.error(self.request, "Error occured ")

        return redirect(reverse('gitlab_classroom:classroom-detail', args=[classroom.id]))


class AssignmentUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Assignment
    form_class = AssignmentForm
    success_url=reverse_lazy("gitlab_classroom:assignment-list")
    template_name="gitlab_classroom/assignment_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
        try:
            gitlab_group_id = form.instance.gitlab_id
            group = gl.groups.get(gitlab_group_id)
            group.name = form.cleaned_data["title"]
            group.description = form.cleaned_data["description"]
            group.save()
            messages.success(self.request, "Assignment was updated successfully")
        except Exception as e:
            messages.error(self.request, "Error occured. Assignmend doesn't exist on gitlab")
        return response


class AssignmentDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Assignment
    template_name = "gitlab_classroom/assignment_confirm_delete.html"
    success_url = reverse_lazy("gitlab_classroom:assignment-list")

    def form_valid(self, form):
        try:
            self.object = self.get_object()
            gitlab_assignment_id = self.object.gitlab_id
            gl = gitlab.Gitlab('https://gitlab-stud.elka.pw.edu.pl', private_token=self.request.session["access_token"])
            response = super().form_valid(form)
            group = gl.groups.get(gitlab_assignment_id)
            group.delete()
            messages.success(self.request, "Assignment was deleted successfully")
        except Exception as e:
            messages.error(self.request, "Error occured. Assignment doesn't exists on GitLab")
            group = gl.groups.get(gitlab_assignment_id)
            group.delete()
        return response
