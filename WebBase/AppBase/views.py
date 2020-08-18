import traceback, datetime
from django.shortcuts import render, redirect
from WebBase.settings import db, auth, db_storage, DEBUG, EMAIL_HOST_USER
from django.core.mail import send_mail
from django.http import HttpResponse
from google.cloud import firestore



def loginPage(request):
    if request.method == 'POST':
        user_email = request.POST['usermail']
        user_pass = request.POST['userpass']

        try:
            auth.current_user = auth.sign_in_with_email_and_password(email=user_email, password=user_pass)
            request.session['id'] = auth.current_user['localId']

            user_data = db.collection(u'userData').document(u'{}'.format(request.session['id'])).get().to_dict()
            request.session['avatar'] = db_storage.child('Avatar/{}'.format(user_data['userAvatar'])).get_url("")
            request.session['userName'] = user_data['userName']
            request.session['userActive'] = user_data['userActive']

            return redirect('home')

        except:
            if DEBUG:
                traceback.print_exc()
            return render(request, 'AuthLogin.html', {'CVP': 'FALSE'})

    return render(request, 'AuthLogin.html')


def registerPage(request):
    if request.method == 'POST':
        userimage = request.FILES['userimg']
        username = request.POST['username']
        useremail = request.POST['email']
        userpass = request.POST['realpass']

        if 'register' in request.POST:
            try:
                x = str(userimage).split(".")
                if x[-1] != "jpg": raise Exception

                # a = os.path.getsize(str(userimage))
                # if a > 1500000: raise Exception

                auth.current_user = auth.create_user_with_email_and_password(email=useremail, password=userpass)

                data = {
                    u"userEmail": u'{}'.format(useremail),
                    u"userName": u'{}'.format(username),
                    u"userAvatar": u'{}'.format(auth.current_user['localId'] + ".jpg"),
                    u"userUID": u'{}'.format(auth.current_user['localId']),
                    u'regisDate': u'{}'.format(datetime.datetime.now()),
                    u'userActive': False
                }
                to_database = db.collection(u"userData").document(auth.current_user['localId'])
                to_database.set(data)

                avatar = auth.current_user['localId'] + ".jpg"
                ref = db_storage.child(f'Avatar/{avatar}')
                ref.put(userimage)

                user_data = db.collection(u"userData").document(auth.current_user['localId']).get()
                send_mail(
                    'Account Confirmation',
                    f'Hello dear, {user_data.to_dict()["userName"]}. Please click the link to activate your account.{" "}Your userUID: {user_data.to_dict()["userUID"]}'
                    f'\nHere is the link:  http://127.0.0.1:8000/activateUser/{user_data.to_dict()["userUID"]}',
                    f'{EMAIL_HOST_USER}',
                    [f'{user_data.to_dict()["userEmail"]}'],
                    fail_silently=False,
                )

                return HttpResponse(
                    "<h4>Thanks for registration. Please confirm our email which is sended to your account, for activate your account.</h4>")

            except Exception as error:
                if DEBUG:
                    traceback.print_exc()
                return render(request, 'AuthRegister.html', {'CVP': 'FALSE'})

    return render(request, 'AuthRegister.html')


def activateUser(request, userID):
    activate_user = db.collection(u'userData').document(u'{}'.format(userID))

    activate_user.set({
        u'userActive': True
    }, merge=True)

    return HttpResponse("<p>Thanks for activate your account.</p>")


def forgetPass(request):
    if request.method == 'POST':
        user_email = request.POST['useremail']

        if 'resetpass' in request.POST:
            try:
                auth.send_password_reset_email(user_email)
            except Exception as error:
                if DEBUG:
                    traceback.print_exc()
                return render(request, 'AuthForgetPass.html', {'CVP': 'FALSE'})

    return render(request, 'AuthForgetPass.html', {})


def Home(request):
    if request.session['id'] is None:
        return render(request, 'NotAuth.html', {})

    if request.session['userActive']:
        if request.method == 'POST':
            if 'addtask' in request.POST:
                notbaslik = request.POST.get('notbaslik')
                noticerik = request.POST.get('noticerik')

                frontend = request.POST.get('frontend')
                backend = request.POST.get('backend')
                doc = request.POST.get('doc')
                bug = request.POST.get('bugs')

                try:

                    send_note = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(
                        u'Notlarım').document()
                    data = {
                        u"notBaslik": u"{}".format(notbaslik),
                        u"notIcerik": u"{}".format(noticerik),
                        u"trashed": False,
                        u"finished": False,
                        u"labels": [frontend, backend, doc, bug],
                        u"notTarihi": u"{}".format(datetime.datetime.now()),
                        u"userUID": u"{}".format(request.session['id']),

                    }
                    send_note.set(data)

                    not_id = {u"notID": u"{}".format(send_note.id)}
                    send_note.set(not_id, merge=True)

                except:
                    if DEBUG:
                        traceback.print_exc()
                    return render(request, 'HomePage.html', {})

            if 'updatenot' in request.POST:
                notbaslik_update = request.POST['notbaslikupdate']
                noticerik_update = request.POST['noticerikupdate']
                try:

                    send_note = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(u'Notlarım').document()
                    data = {
                        u"notBaslik": u"{}".format(notbaslik_update),
                        u"notIcerik": u"{}".format(noticerik_update),
                        u"notTarihi": u"{}".format(datetime.datetime.now()),
                        }
                    send_note.set(data, merge=True)


                except:
                    if DEBUG:
                        traceback.print_exc()
                    return render(request, 'HomePage.html', {})

            if 'nottamam' in request.POST:
                take_all_notes = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(
                    u'Notlarım').get()

                notes = []
                for item in take_all_notes:
                    notes.append(item.id)

                for i in range(0, len(notes)):
                    if str(i) == request.POST.get('nottamam'):
                        update_node_data = db.collection(u'userData').document(
                            u'{}'.format(request.session['id'])).collection(
                            u'Notlarım').document(notes[i])

                        try:
                            update_node_data.set({
                                u"finished": True
                            }, merge=True)

                        except:
                            return render(request, 'HomePage.html', {})
            if 'notsil' in request.POST:
                take_all_notes = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(
                    u'Notlarım').get()

                notes = []
                for item in take_all_notes:
                    notes.append(item.id)

                for i in range(0, len(notes)):
                    if str(i) == request.POST.get('notsil'):
                        update_node_data = db.collection(u'userData').document(
                            u'{}'.format(request.session['id'])).collection(u'Notlarım').document(notes[i])

                        try:
                            update_node_data.set({
                                u"trashed": True
                            }, merge=True)

                        except:
                            return render(request, 'HomePage.html', {})



    else:
        return render(request, 'NotAuth.html', {})

    take_notes = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(u'Notlarım').order_by(u'notTarihi', direction=firestore.Query.DESCENDING).get()

    return render(request, 'HomePage.html', {'CVP': 'TRUE','notes': take_notes})


def completedTasks(request):
    if request.session['userActive']:

        finished_notes = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(u'Notlarım').order_by(u'notTarihi', direction=firestore.Query.DESCENDING).get()

        return render(request, 'CompletedTasks.html', {'notes': finished_notes})


def trashedTasks(request):
    if request.session['userActive']:
        finished_notes = db.collection(u'userData').document(u'{}'.format(request.session['id'])).collection(u'Notlarım').order_by(u'notTarihi', direction=firestore.Query.DESCENDING).get()
        return render(request, 'TrashedTasks.html', {'notes': finished_notes})
    else:
        return redirect('loginPage')


def Logout(request):
    if request.session['userActive']:
        request.session['id'] = None
        request.session['avatar'] = None
        request.session['userName'] = None
        request.session['userActive'] = None
        return render(request, 'AuthLogin.html', {})

    else:
        return redirect('loginPage')
