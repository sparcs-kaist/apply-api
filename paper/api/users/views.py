from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import RetrieveAPIView
from api.users.serializers import PaperuserSerializer
from apps.papers.models import PaperUser
from paper.common.permissions import IsOwnerOrIsAuthenticatdThenCreateOnlyOrReadOnly
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from apps.users.models import PaperUser
from apps.users.sparcssso import Client
from paper.settings.components.secret import SSO_CLIENT_ID, SSO_SECRET_KEY, SSO_IS_BETA
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from rest_framework_jwt.settings import api_settings
from paper.settings.components.common import base_url

sso_client = Client(SSO_CLIENT_ID, SSO_SECRET_KEY, SSO_IS_BETA)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = PaperuserSerializer
    queryset = PaperUser.objects.all()
    filter_fields = ("nickName",)

    @action(methods=['get'], detail=False)
    def myInfo(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


# url after login
url_after_login = base_url + "/login/"
# url when get error
url_when_error = base_url + "/error/"
# url after logout
url_after_logout = base_url


def login(request):
    user = request.user
    if user.is_authenticated:
        return redirect(url_after_login)

    login_url, state = sso_client.get_login_params()
    request.session['sso_state'] = state
    print("login_url: {login_url}".format(login_url=login_url))
    return redirect(login_url)


def sync_user_with_sso(user, sso_profile):
    user.nickName = email.split('@')[0]
    user.first_name = sso_profile['first_name']
    user.last_name = sso_profile['last_name']
    user.sid = sso_profile['sid']
    kaist_info = sso_profile.get('kaist_info')
    if kaist_info:
        employeeType = kaist_info.get('employeeType', '')
        # Active 학생, 교수, 직원을 구성원으로 취급
        user.is_kaistian = 'S' in employeeType or 'P' in employeeType or 'E' in employeeType
        # 단, 교수 및 직원은 은퇴한 상태가 아니어야 함
        user.is_kaistian = user.is_kaistian and 'R' not in employeetype
    user.save()

@require_http_methods(['GET'])
def login_callback(request):
    print("login_callback")
    state_before = request.session.get('sso_state', 'default before state')
    state = request.GET.get('state', 'default state')
    if state_before != state:
        return redirect(url_when_error)

    code = request.GET.get('code')
    sso_profile = sso_client.get_user_info(code)
    # print(sso_profile)
    email = sso_profile['email']
    user_list = PaperUser.objects.filter(email=email)

    user = None
    if len(user_list) == 0:
        user = PaperUser.objects.create_user(email=email, password=email)
    else:
        user = user_list[0]

    sync_user_with_sso(user, sso_profile)

    next_path = '{0}{1}'.format(url_after_login, api_settings.JWT_ENCODE_HANDLER(
        api_settings.JWT_PAYLOAD_HANDLER(
            user,
        )
    ))

    return redirect(next_path)

    return JsonResponse(status=200,
                        data={'error_title': "Login Error",
                              'error_message': "No such that user"})

@require_http_methods(['GET'])
def logout(request):
    print("logout")
    email = request.GET.get('email')
    sid = PaperUser.objects.get(email=email).sid
    logout_url = sso_client.get_logout_url(sid, url_after_logout)
    return redirect(logout_url)

    if request.user.is_authenticated:
        sid = Paper.objects.get(email=request.GET.get('email')).sid
        logout_url = sso_client.get_logout_url(sid, url_after_logout)
        request.session['visited'] = True
        return redirect(logout_url)
    return redirect(url_after_logout)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated, ])
def unregister(request):
    if request.method != 'POST':
        return JsonResponse(status=200,
                            data={'error_title': "Unregister Error",
                                  'error_message': "please try again1"})
    zabo_user = PaperUser.objects.get(email=request.user)

    sid = zabo_user.sid
    result = sso_client.do_unregister(sid)
    if not result:
        return JsonResponse(status=200,
                            data={'error_title': "Unregister Error",
                                  'error_message': "please try again2"})

    zabo_user.delete()
    request.user.delete()

    return JsonResponse(status=200,
                        data={'message': "Unregister successfully"})
