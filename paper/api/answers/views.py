from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import viewsets
from apps.answers.models import Participate, Answer
from api.answers.serializers import AnswerSerializer, ParticipateCreateSerializer, ParticipateListSerializer, \
    ParticipateSerializer
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from paper.common.permissions import IsOwnerOrIsAuthenticatdThenCreateOnlyOrReadOnly
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from api.common.viewset import ActionAPIViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from paper.common.permissions import ParticipatePermission
from apps.papers.models import Paper

class ParticipateViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    """
        This viewset automatically provides `list`, `create`, `retrieve`,
        `update` and `destroy` actions.
    """
    serializer_class = ParticipateSerializer
    queryset = Participate.objects.all()
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    # 나중에 검색 결과 순서에 대해 이야기 해보아야 함
    ordering_fields = ('created_time',)

    action_serializer_class = {
        'create': ParticipateCreateSerializer,
        'list': ParticipateListSerializer,
        'retrieve': ParticipateSerializer,
        "update": ParticipateCreateSerializer
    }
    permission_classes = (ParticipatePermission, )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            author=self.request.user
        )

    @action(methods=['get'], detail=False)
    def created(self, request):
        if request.user.is_anonymous:
            return Response({'Message': 'You are unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        queryset = Participate.objects.filter(author=user).order_by('updated_time')
        page = self.paginate_queryset(queryset)
        serializer = ParticipateListSerializer(page, many=True, context={
            'request': request,
        })
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class AnswerViewSet(viewsets.ModelViewSet):
    """
        This viewset automatically provides `list`, `create`, `retrieve`,
        `update` and `destroy` actions.
    """
    serializer_class = AnswerSerializer
    queryset = Answer.objects.all()
    permission_classes = (IsOwnerOrIsAuthenticatdThenCreateOnlyOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )
