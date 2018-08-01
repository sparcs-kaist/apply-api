from rest_framework import serializers
from api.users.serializers import PaperuserListSerializer
from api.papers.serializers import PaperListSerializer, ChoiceSerializer
from apps.papers.models import Question, Choice
from apps.answers.models import Participate, Answer, Select
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
import json


class SelectSerializer(serializers.ModelSerializer):
    choice = ChoiceSerializer(read_only=True)

    class Meta:
        model = Select
        fields = (
            'choice',
        )


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.SlugRelatedField(read_only=True, slug_field='content')
    selects = SelectSerializer(read_only=True, many=True)

    class Meta:
        model = Answer
        fields = (
            'id',
            'question',
            'selects',
            'content'
        )


class ParticipateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participate
        fields = (
            'paper',
        )

    def to_internal_value(self, data):
        instance = super(ParticipateCreateSerializer, self).to_internal_value(data)
        if "answers" in data:
            answers_str_data = data["answers"]
            answers_json = json.loads(answers_str_data)
            instance["answers"] = answers_json
        return instance

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', None)
        try:
            participate = Participate.objects.create(**validated_data)
            if answers_data:
                questions = Question.objects.filter(paper=participate.paper)
                for answer_data, question in zip(answers_data, questions):
                    if question.type == 'C' or question.type == 'R':
                        choice_id_list = Choice.objects.filter(question=question).values_list('id', flat=True)
                        if answer_data["selects"] is None:
                            raise AssertionError()
                        selects_data = answer_data.pop('selects')
                        if question.is_multiple is False and len(selects_data) > 1:
                            raise AssertionError()
                        answer = Answer.objects.create(participate=participate, question=question, **answer_data)
                        for select_data in selects_data:
                            select_choice_id = select_data["choice"]
                            if select_choice_id not in choice_id_list:
                                raise AssertionError()
                            choice = Choice.objects.get(id=select_data["choice"])
                            Select.objects.create(answer=answer, choice=choice)
                    elif question.type == 'O':
                        if answer_data["content"] is None:
                            raise AssertionError()
                        Answer.objects.create(participate=participate, question=question, **answer_data)
        except ObjectDoesNotExist or AssertionError:
            participate.delete()
            return HttpResponse(status=400)
        return participate


class ParticipateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    author = PaperuserListSerializer(read_only=True)
    paper = PaperListSerializer(read_only=True)

    class Meta:
        model = Participate
        fields = (
            'id',
            'paper',
            'author',
            'answers'
        )
        read_only_fields = (
            'created_time',
            'updated_time',
        )


class ParticipateListSerializer(serializers.ModelSerializer):
    paper = PaperListSerializer(read_only=True)

    class Meta:
        model = Participate
        fields = (
            'id',
            'paper'
        )
        read_only_fields = (
            'created_time',
            'updated_time',
        )

class CheckingParticipateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    author = PaperuserListSerializer(read_only=True)

    class Meta:
        model = Participate
        fields = (
            'id',
            'author',
            'answers'
        )
        read_only_fields = (
            'created_time',
            'updated_time',
        )