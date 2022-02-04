from email import message
from platform import java_ver
from xxlimited import Null

from numpy import empty
from library.forms import IssueBookForm
from django.shortcuts import redirect, render,HttpResponse
from .models import *
from .forms import IssueBookForm
from django.contrib.auth import authenticate, login, logout
from . import forms, models
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from PIL import Image

def index(request):
    return render(request, "index.html")

@login_required(login_url = '/admin_login')
def add_book(request):
    if request.method == "POST":
        name = request.POST['name']
        author = request.POST['author']
        isbn = request.POST['isbn']
        no_of_books = request.POST['no_of_books']

        books = Book.objects.create(name=name, author=author, isbn=isbn, no_of_books=no_of_books)
        books.save()
        alert = True
        return render(request, "add_book.html", {'alert':alert})
    return render(request, "add_book.html")

@login_required(login_url = '/admin_login')
def view_books(request):
    books = Book.objects.all()
    return render(request, "view_books.html", {'books':books})

@login_required(login_url = '/admin_login')
def view_students(request):
    students = Student.objects.all()
    return render(request, "view_students.html", {'students':students})

@login_required(login_url = '/admin_login')
def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.student_id = request.POST['name2']
            obj.isbn = request.POST['isbn2']

            obj3 = list(models.IssuedBook.objects.filter(student_id = obj.student_id).filter(isbn=obj.isbn))
            if obj3:
                messages.info(request,'Warning, Book already issued.')
                return render(request, "issue_book.html")
                
            else:
                obj1 = Book.objects.filter(isbn = obj.isbn).values_list('no_of_books',flat=True).order_by('id')
                obj2 = Book.objects.filter(isbn = obj.isbn).values_list('issued_count',flat=True).order_by('id')
                a = obj1[0]
                b = obj2[0]
                if a <= 0:
                    return HttpResponse('book not available')
                else:
                    update_data = {
                        'no_of_books': a-1,
                        'issued_count': b+1,
                    }
                    Book.objects.filter(isbn = obj.isbn).update(**update_data)
                    obj.save()
                    alert = True
                    
                return render(request, "issue_book.html", {'obj':obj, 'alert':alert})
    return render(request, "issue_book.html", {'form':form})

@login_required(login_url = '/admin_login')
def view_issued_book(request):
    issuedBooks = IssuedBook.objects.all()
    details = []
    for i in issuedBooks:
        days = (date.today()-i.issued_date)
        d=days.days
        fine=0
        if d>14:
            day=d-14
            fine=day*5
        books = list(models.Book.objects.filter(isbn=i.isbn))
        students = list(models.Student.objects.filter(user=i.student_id))
        j=0
        for l in books:
            t=(i.id,students[j].user,students[j].user_id,books[j].name,books[j].isbn,i.issued_date,i.expiry_date,fine)
            j=j+1
            details.append(t)
    return render(request, "view_issued_book.html", {'issuedBooks':issuedBooks, 'details':details})

@login_required(login_url = '/student_login')
def student_issued_books(request):
    student = Student.objects.filter(user_id=request.user.id)
    issuedBooks = IssuedBook.objects.filter(student_id=student[0].user_id)
    li1 = []
    li2 = []

    for i in issuedBooks:
        books = Book.objects.filter(isbn=i.isbn)
        for book in books:
            t=(request.user.id, request.user.get_full_name, book.name,book.author)
            li1.append(t)

        days=(date.today()-i.issued_date)
        d=days.days
        fine=0
        if d>15:
            day=d-14
            fine=day*5
        t=(issuedBooks[0].issued_date, issuedBooks[0].expiry_date, fine)
        li2.append(t)
    li = []
    j = 0
    for i in li1:
        li.append(i+li2[j])
        j= j+1
    return render(request,'student_issued_books.html',{'li':li})

@login_required(login_url = '/student_login')
def profile(request):
    return render(request, "profile.html")

@login_required(login_url = '/student_login')
def edit_profile(request):
    student = Student.objects.get(user=request.user)
    if request.method == "POST":
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']

        student.user.email = email
        student.phone = phone
        student.branch = branch
        student.classroom = classroom
        student.roll_no = roll_no
        student.user.save()
        student.save()
        alert = True
        return render(request, "edit_profile.html", {'alert':alert})
    return render(request, "edit_profile.html")

def delete_book(request, myid):
    books = Book.objects.filter(id=myid)
    books.delete()
    return redirect("/view_books")

def delete_student(request, myid):
    students = Student.objects.filter(id=myid)
    students.delete()
    return redirect("/view_students")

def delete_issue(request, myid):
    del_issue = IssuedBook.objects.filter(id = myid)
    obj3 = IssuedBook.objects.filter(id = myid).values_list('isbn',flat=True).order_by('id')
    obj1 = Book.objects.filter(isbn = obj3[0]).values_list('no_of_books',flat=True).order_by('id')
    obj2 = Book.objects.filter(isbn = obj3[0]).values_list('issued_count',flat=True).order_by('id')
    a = obj1[0]
    b = obj2[0]
    update_data = {
                    'no_of_books': a+1,
                    'issued_count': b-1,
                }
    Book.objects.filter(isbn = obj3[0]).update(**update_data)
    
    del_issue.delete()
    return redirect("/view_issued_book")

def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert':alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong':currpasswrong})
        except:
            pass
    return render(request, "change_password.html")

def student_registration(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']
        image = request.FILES['image']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        img = Image.open(image)
        wid, hgt = img.size

        if wid!=500 and hgt!=500:
            messages.info(request,'Image resolution must be (500pxX500px)')
            return render(request, "student_registration.html")

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username taken')
                return render(request, "student_registration.html")
            elif User.objects.filter(email=email).exists():
                messages.info(request,'Username taken')
                return render(request, "student_registration.html")
            else:
                user = User.objects.create_user(username=username, email=email, password=password,first_name=first_name, last_name=last_name)
                student = Student.objects.create(user=user, phone=phone, branch=branch, classroom=classroom,roll_no=roll_no, image=image)
                user.save()
                student.save()
                alert = True
                return render(request, "student_registration.html", {'alert':alert})
    return render(request, "student_registration.html")

def student_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                messages.info(request,'Invalid Credentials')
                return render(request, "student_login.html")
            else:
                return redirect("/profile")
        else:
            messages.info(request,'Invalid Credentials')
            return render(request, "student_login.html")
    return render(request, "student_login.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return redirect("/view_issued_book")
            else:
                messages.info(request,'Invalid Credentials')
        else:
            messages.info(request,'Invalid Credentials')
            return render(request, "admin_login.html")
    return render(request, "admin_login.html")

def Logout(request):
    logout(request)
    return redirect ("/")