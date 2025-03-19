import gitlab
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "accounts/login.html")
    elif request.method == "POST":
        access_token = request.POST["access_token"]
        if not access_token:
            return render(request, "accounts/login.html", {'error': 'Access token is required'})
        request.session["access_token"] = access_token
        gl = gitlab.Gitlab(url='https://gitlab-stud.elka.pw.edu.pl', private_token=request.session["access_token"])
        try:
            gl.auth()
            gl_user_id = gl.user.id
            username = gl.user.username
            request.session["avatar"] = gl.user.avatar_url
            request.session["name"] = gl.user.username
            request.session["email"] = gl.user.email
            user = authenticate(request, gitlab_id=gl_user_id, username=username)
            if user:
                login(request, user)
                return HttpResponseRedirect(reverse("gitlab_classroom:index"))
            else:
                error_context = {
                    "error": "Invalid credentials" 
                }
        except gitlab.exceptions.GitlabAuthenticationError:
            error_context = {
                "error": "Invalid access token"
            }
        except Exception as e:
            error_context = {
                "error": f"Error occured: {e}. Try to login again."
            }
        return render(request, "accounts/login.html", context=error_context)

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return render(request, "accounts/logout.html")